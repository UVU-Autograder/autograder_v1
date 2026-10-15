from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

backend_dir = str(Path(__file__).resolve().parents[1])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if "PYTHONPATH" not in os.environ or backend_dir not in os.environ["PYTHONPATH"]:
    os.environ["PYTHONPATH"] = (
        f"{backend_dir}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(os.pathsep)
    )

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")


def _seed_test_fixtures() -> None:
    from sqlalchemy import select
    from app.db.session import SessionLocal
    from app.domains.courses.models import Course, Module
    from app.domains.assignments.models import Assignment
    from app.domains.assignments.service import seed_assignment_artifacts
    from app.domains.assignments.inventory import execution_fingerprint
    from app.domains.grading.report_contract import ValidatedManifest
    from app.domains.auth.models import Role, User

    with SessionLocal() as db:
        role = db.scalar(select(Role).where(Role.name == "admin"))
        if role is None:
            role = Role(name="admin")
            db.add(role)
            db.flush()
        staff_user = db.scalar(select(User).where(User.email == "dev.staff@uvu.edu"))
        if staff_user is None:
            staff_user = User(email="dev.staff@uvu.edu", display_name="Development Staff")
            db.add(staff_user)
            db.flush()
        course = db.scalar(select(Course).where(Course.code == "cs1400"))
        if course is None:
            course = Course(
                code="cs1400",
                title="Fundamentals of Programming",
                term="Fall 2026",
                default_concepts=["variables", "conditionals"],
                instructor=staff_user,
            )
            db.add(course)
            db.flush()
        m1 = db.scalar(select(Module).where(Module.course_id == course.id, Module.name.like("Module 1:%")))
        if m1 is None:
            m1 = Module(course=course, name="Module 1: Introduction to Programming", concepts=["variables"])
            db.add(m1)
            db.flush()
        fixture_assignment = db.scalar(
            select(Assignment).where(Assignment.course_id == course.id, Assignment.slug == "simple-python-functions")
        )
        if fixture_assignment is None:
            fixture_assignment = Assignment(
                course=course,
                slug="simple-python-functions",
                title="Simple Python Functions",
                language="python",
                canvas_ref="canvas:synthetic:simple-python-functions",
                sandbox_enabled=True,
                module=m1,
                is_active=True,
            )
            db.add(fixture_assignment)
            db.flush()
            seed_assignment_artifacts(db, fixture_assignment, fixture_assignment.slug)
            db.flush()
            cases = [
                {"nodeid": "assignment_tests.py::test_add_numbers_positive_values", "markers": ["ag_add_numbers"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_add_numbers_negative_values", "markers": ["ag_add_numbers"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_reverse_words_basic_sentence", "markers": ["ag_reverse_words"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_reverse_words_preserves_spacing_between_words", "markers": ["ag_reverse_words"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_count_vowels_lowercase", "markers": ["ag_count_vowels"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_count_vowels_case_insensitive", "markers": ["ag_count_vowels"], "xfail": False},
            ]
            fixture_assignment.config.validated_test_manifest = ValidatedManifest(
                fingerprint=execution_fingerprint(db, fixture_assignment),
                cases=cases,
            ).model_dump(mode="json")
            db.commit()


@pytest.fixture
def mock_httpx_client():
    """Generic fixture to mock httpx.Client calls in integrations.
    Usage in test:
        def test_api_calls(mock_httpx_client):
            mock_httpx_client.get.return_value = httpx.Response(200, json={"status": "ok"})
    """
    with patch("httpx.Client") as mock_class:
        mock_instance = MagicMock(spec=httpx.Client)
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def reset_database():
    """Recreate seeded tables before a test and leave a clean database after it."""
    from app.db.base import Base, import_domain_models
    from app.db.seed import initialize_database
    from app.db.session import engine

    from app.domains.runs.orchestrator import clear_local_orchestrator_cache

    # drop_all() empties whatever DATABASE_URL points at. Inside a deployed
    # container that is the live Postgres, which is how a stack ends up with
    # only alembic_version left. The suite only ever needs SQLite.
    if engine.url.get_backend_name() != "sqlite":
        pytest.exit(
            f"refusing to run database tests against {engine.url.render_as_string(hide_password=True)}: "
            "set DATABASE_URL=sqlite+pysqlite:///:memory:",
            returncode=2,
        )

    import_domain_models()
    clear_local_orchestrator_cache()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _seed_test_fixtures()
    initialize_database(seed=True)
    yield
    clear_local_orchestrator_cache()
    Base.metadata.drop_all(bind=engine)


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, Any] = {}

    def get(self, key: str) -> str | None:
        return self.data.get(key)

    def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> bool:
        self.data[key] = str(value)
        return True

    def setex(self, key: str, time: int, value: Any) -> bool:
        self.data[key] = str(value)
        return True

    def decrby(self, key: str, count: int) -> int:
        val = int(self.data.get(key) or 0) - count
        self.data[key] = str(val)
        return val

    def incr(self, key: str, amount: int = 1) -> int:
        val = int(self.data.get(key) or 0) + amount
        self.data[key] = str(val)
        return val

    def decr(self, key: str, amount: int = 1) -> int:
        return self.incr(key, -amount)

    def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self.data:
                self.data.pop(k)
                count += 1
        return count

    def rpush(self, key: str, *values: Any) -> int:
        if key not in self.data:
            self.data[key] = []
        if len(values) == 1 and isinstance(values[0], (list, tuple)):
            self.data[key].extend([str(v) for v in values[0]])
        else:
            self.data[key].extend([str(v) for v in values])
        return len(self.data[key])

    def expire(self, key: str, time: int) -> bool:
        return True

    def mget(self, keys: list[str]) -> list[str | None]:
        return [self.data.get(k) if not isinstance(self.data.get(k), list) else None for k in keys]

    def lpush(self, key: str, *values: Any) -> int:
        lst = self.data.setdefault(key, [])
        for value in values:
            lst.insert(0, str(value))
        return len(lst)

    def ltrim(self, key: str, start: int, end: int) -> bool:
        lst = self.data.get(key)
        if isinstance(lst, list):
            self.data[key] = lst[start:] if end == -1 else lst[start:end + 1]
        return True

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        lst = self.data.get(key)
        if lst is None:
            return []
        if end == -1:
            return lst[start:]
        return lst[start:end+1]

    def pipeline(self, transaction: bool = True) -> FakePipeline:
        return FakePipeline(self)


class FakePipeline:
    """Queues any client command and replays them in order on execute()."""

    def __init__(self, client: FakeRedis) -> None:
        self.client = client
        self.commands: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def watch(self, *args: Any, **kwargs: Any) -> FakePipeline:
        return self

    def unwatch(self, *args: Any, **kwargs: Any) -> FakePipeline:
        return self

    def multi(self, *args: Any, **kwargs: Any) -> FakePipeline:
        return self

    def __getattr__(self, name: str):
        def queue(*args: Any, **kwargs: Any) -> FakePipeline:
            self.commands.append((name, args, kwargs))
            return self

        return queue

    def execute(self) -> list[Any]:
        results = [getattr(self.client, name)(*args, **kwargs) for name, args, kwargs in self.commands]
        self.commands = []
        return results


@pytest.fixture(autouse=True)
def mock_redis_global() -> Generator[FakeRedis, None, None]:
    fake = FakeRedis()
    with patch("redis.Redis.from_url", return_value=fake):
        yield fake


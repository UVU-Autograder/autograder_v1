from __future__ import annotations

import os
import sqlite3
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, close_all_sessions

backend_dir = str(Path(__file__).resolve().parents[1])
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if "PYTHONPATH" not in os.environ or backend_dir not in os.environ["PYTHONPATH"]:
    os.environ["PYTHONPATH"] = (
        f"{backend_dir}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(os.pathsep)
    )

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AUTOGRADER_DISABLE_FSYNC", "1")


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


_db_template_conn: sqlite3.Connection | None = None


def _get_seeded_db_template() -> sqlite3.Connection:
    """Initialize and seed a template database once per pytest session."""
    global _db_template_conn
    if _db_template_conn is None:
        from app.db.base import Base, import_domain_models
        from app.db.seed import initialize_database
        from app.db.session import engine

        import_domain_models()
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        _seed_test_fixtures()
        initialize_database(seed=True)

        raw_conn = engine.raw_connection().dbapi_connection
        _db_template_conn = sqlite3.connect(":memory:")
        raw_conn.backup(_db_template_conn)

    return _db_template_conn


@pytest.fixture
def reset_database() -> Generator[None, None, None]:
    """Fast in-memory database reset using SQLite page backup/restore."""
    from app.db.session import engine
    from app.domains.runs.orchestrator import clear_local_orchestrator_cache

    if engine.url.get_backend_name() != "sqlite":
        pytest.exit(
            f"refusing to run database tests against {engine.url.render_as_string(hide_password=True)}: "
            "set DATABASE_URL=sqlite+pysqlite:///:memory:",
            returncode=2,
        )

    template = _get_seeded_db_template()
    close_all_sessions()
    clear_local_orchestrator_cache()
    raw_conn = engine.raw_connection().dbapi_connection
    raw_conn.rollback()
    template.backup(raw_conn)

    yield

    close_all_sessions()
    clear_local_orchestrator_cache()
    raw_conn = engine.raw_connection().dbapi_connection
    raw_conn.rollback()
    template.backup(raw_conn)


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


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Close the in-memory SQLite template at session completion."""
    global _db_template_conn
    if _db_template_conn is not None:
        _db_template_conn.close()
        _db_template_conn = None


# --- Centralized Shared Test Fixtures ---


@pytest.fixture
def anyio_backend() -> str:
    """Default backend for anyio async tests."""
    return "asyncio"


@pytest.fixture
def client(reset_database: Any) -> Generator[TestClient, None, None]:
    """Pre-configured FastAPI TestClient bound to the initialized test database."""
    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def db_session(reset_database: Any) -> Generator[Session, None, None]:
    """Active SQLAlchemy session bound to the test database with admission queue isolation."""
    from app.db.session import SessionLocal
    from app.domains.runs.queue_admission import reset_admission_state_for_tests

    reset_admission_state_for_tests()
    with SessionLocal() as session:
        yield session
    reset_admission_state_for_tests()


@pytest.fixture
def admin_token() -> str:
    """JWT bearer access token for default seeded development admin staff."""
    from app.core.auth_utils import create_access_token

    return create_access_token(email="dev.staff@uvu.edu", display_name="Dev Admin Staff")


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    """Authorization headers for default admin staff."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def student_token() -> str:
    """JWT bearer access token for standard student user without staff roles."""
    from app.core.auth_utils import create_access_token

    return create_access_token(email="student.test@uvu.edu", display_name="Test Student")


def _ensure_staff_token(
    db_session: Session,
    *,
    email: str,
    display_name: str,
    role_name: str,
) -> str:
    from sqlalchemy import select

    from app.core.auth_utils import create_access_token
    from app.domains.auth.models import Role, StaffAccess, User
    from app.domains.courses.models import Course, Section

    user = db_session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, display_name=display_name, is_active=True)
        db_session.add(user)
        db_session.flush()

        role = db_session.scalar(select(Role).where(Role.name == role_name))
        course = db_session.scalar(select(Course).where(Course.code == "cs1400"))
        assert course is not None
        section = db_session.scalar(select(Section).where(Section.course_id == course.id))

        db_session.add(
            StaffAccess(
                user=user,
                role=role,
                course=course,
                section=section,
                is_active=True,
            )
        )
        db_session.commit()
    return create_access_token(email=email, display_name=display_name)


@pytest.fixture
def instructor_token(db_session: Session) -> str:
    """JWT bearer access token for an active course instructor."""
    return _ensure_staff_token(
        db_session,
        email="instructor.test@uvu.edu",
        display_name="Test Instructor",
        role_name="instructor",
    )


@pytest.fixture
def ia_token(db_session: Session) -> str:
    """JWT bearer access token for an active teaching assistant (IA)."""
    return _ensure_staff_token(
        db_session,
        email="ia.test@uvu.edu",
        display_name="Test IA",
        role_name="IA",
    )


@pytest.fixture
def section_id(db_session: Session) -> int:
    """CRN 12345 section ID seeded for cs1400."""
    from sqlalchemy import select

    from app.domains.courses.models import Section

    section = db_session.scalar(select(Section).where(Section.crn == "12345"))
    assert section is not None
    return section.id


@pytest.fixture
def temp_workspaces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated temporary workspace root with settings.artifact_storage_dir redirected."""
    from app.core.settings import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    return tmp_path


@pytest.fixture
def temp_artifact_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolated artifact storage root without 'artifacts' subdirectory."""
    from app.core.settings import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path))
    return tmp_path


@pytest.fixture
def reset_sandbox_state() -> Generator[None, None, None]:
    """Ensure sandbox service memory store is clear before and after test execution."""
    from app.domains.sandbox.service import sandbox_service

    sandbox_service._runs.clear()
    sandbox_service._session_uploads.clear()
    yield
    sandbox_service._runs.clear()
    sandbox_service._session_uploads.clear()


@pytest.fixture
def base_config() -> Any:
    """Standard AssignmentConfigV1 for Python pytest testing."""
    from app.domains.assignments.schemas import AssignmentConfigV1

    config_dict = {
        "bundle": {
            "entrypoint": "main.py",
            "file_requirements": [{"paths": ["main.py"]}],
        },
        "artifacts": {
            "assignment_tests": {
                "type": "pytest_file",
                "display_filename": "tests.py",
            }
        },
        "scoring_items": [
            {
                "key": "test_pass",
                "label": "Test Pass",
                "points": 10,
                "extra_credit": False,
                "item_type": "pytest",
            }
        ],
    }
    return AssignmentConfigV1.model_validate(config_dict)


@pytest.fixture
def mock_official_run_dispatch() -> Generator[MagicMock, None, None]:
    """Patch background task runner for official runs."""
    with patch("app.domains.runs.tasks.run_mock_official_run") as mock_runner:
        yield mock_runner


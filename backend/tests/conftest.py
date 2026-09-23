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

    import_domain_models()
    clear_local_orchestrator_cache()
    Base.metadata.drop_all(bind=engine)
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

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        lst = self.data.get(key)
        if lst is None:
            return []
        if end == -1:
            return lst[start:]
        return lst[start:end+1]

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)


class FakePipeline:
    def __init__(self, client: FakeRedis) -> None:
        self.client = client
        self.commands: list[tuple[str, str, Any]] = []

    def watch(self, *args: Any, **kwargs: Any) -> FakePipeline:
        return self

    def unwatch(self, *args: Any, **kwargs: Any) -> FakePipeline:
        return self

    def multi(self, *args: Any, **kwargs: Any) -> FakePipeline:
        return self

    def set(self, key: str, value: Any, *args: Any, **kwargs: Any) -> FakePipeline:
        self.commands.append(("set", key, value))
        return self

    def execute(self) -> list[Any]:
        for cmd, key, val in self.commands:
            if cmd == "set":
                self.client.set(key, val)
        self.commands = []
        return []


@pytest.fixture(autouse=True)
def mock_redis_global() -> Generator[FakeRedis, None, None]:
    fake = FakeRedis()
    with patch("redis.Redis.from_url", return_value=fake):
        yield fake


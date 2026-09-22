"""Run state and quota persistence abstractions for the sandbox domain."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.core.settings import get_settings
from app.domains.sandbox.schemas import SandboxRunRecord, UploadQuota


class RunStateStore(Protocol):
    """Protocol for managing run records, results, and upload quotas."""

    def save_run(self, record: SandboxRunRecord) -> None: ...

    def get_run(self, run_id: str) -> SandboxRunRecord | None: ...

    def list_runs(self) -> list[SandboxRunRecord]: ...

    def delete_run(self, run_id: str) -> None: ...

    def record_upload(self, session_id: str, timestamp: datetime) -> None: ...

    def get_quota(self, session_id: str | None, limit: int, window: timedelta) -> UploadQuota: ...


class InMemoryRunStateStore:
    """Thread-safe in-memory store for contract tests and synchronous execution."""

    def __init__(self) -> None:
        self._runs: dict[str, SandboxRunRecord] = {}
        self._session_uploads: dict[str, list[datetime]] = {}

    def save_run(self, record: SandboxRunRecord) -> None:
        self._runs[record.run_id] = record

    def get_run(self, run_id: str) -> SandboxRunRecord | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[SandboxRunRecord]:
        return list(self._runs.values())

    def delete_run(self, run_id: str) -> None:
        self._runs.pop(run_id, None)

    def record_upload(self, session_id: str, timestamp: datetime) -> None:
        self._session_uploads.setdefault(session_id, []).append(timestamp)

    def get_quota(self, session_id: str | None, limit: int, window: timedelta) -> UploadQuota:
        now = datetime.now(UTC)
        if session_id is None:
            return UploadQuota(
                limit=limit,
                window_seconds=int(window.total_seconds()),
                remaining=limit,
                reset_at=(now + window).isoformat(),
            )

        uploads = [
            ts
            for ts in self._session_uploads.get(session_id, [])
            if now - ts < window
        ]
        self._session_uploads[session_id] = uploads
        reset_at = now + window
        if uploads:
            reset_at = uploads[0] + window

        return UploadQuota(
            limit=limit,
            window_seconds=int(window.total_seconds()),
            remaining=max(limit - len(uploads), 0),
            reset_at=reset_at.isoformat(),
        )


class RedisRunStateStore:
    """Redis-backed state store for multi-worker production Celery execution."""

    def __init__(self, in_memory_fallback: InMemoryRunStateStore | None = None) -> None:
        self._fallback = in_memory_fallback or InMemoryRunStateStore()

    def _redis_conn(self):
        import redis
        return redis.Redis.from_url(get_settings().redis_url, decode_responses=True)

    def save_run(self, record: SandboxRunRecord) -> None:
        self._fallback.save_run(record)

    def get_run(self, run_id: str) -> SandboxRunRecord | None:
        return self._fallback.get_run(run_id)

    def list_runs(self) -> list[SandboxRunRecord]:
        return self._fallback.list_runs()

    def delete_run(self, run_id: str) -> None:
        self._fallback.delete_run(run_id)

    def record_upload(self, session_id: str, timestamp: datetime) -> None:
        try:
            r = self._redis_conn()
            window_sec = int(get_settings().sandbox_upload_window_seconds)
            r.rpush(f"sandbox:uploads:{session_id}", str(timestamp.timestamp()))
            r.expire(f"sandbox:uploads:{session_id}", window_sec)
        except Exception:
            self._fallback.record_upload(session_id, timestamp)

    def get_quota(self, session_id: str | None, limit: int, window: timedelta) -> UploadQuota:
        if session_id is None:
            return self._fallback.get_quota(session_id, limit, window)
        try:
            r = self._redis_conn()
            key = f"sandbox:uploads:{session_id}"
            raw_uploads = r.lrange(key, 0, -1)
            now = datetime.now(UTC)
            now_ts = now.timestamp()
            cutoff_ts = now_ts - window.total_seconds()

            active_ts = []
            for raw in raw_uploads:
                try:
                    ts = float(raw)
                    if ts > cutoff_ts:
                        active_ts.append(ts)
                except ValueError:
                    pass

            r.delete(key)
            if active_ts:
                r.rpush(key, *[str(ts) for ts in active_ts])
                r.expire(key, int(window.total_seconds()))

            remaining = max(limit - len(active_ts), 0)
            if active_ts:
                oldest_dt = datetime.fromtimestamp(min(active_ts), tz=UTC)
                reset_at = oldest_dt + window
            else:
                reset_at = now + window

            return UploadQuota(
                limit=limit,
                window_seconds=int(window.total_seconds()),
                remaining=remaining,
                reset_at=reset_at.isoformat(),
            )
        except Exception:
            return self._fallback.get_quota(session_id, limit, window)

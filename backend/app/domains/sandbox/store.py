"""Run state and quota persistence abstractions for the sandbox domain."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Protocol

from pydantic import TypeAdapter
from redis import Redis
from redis.exceptions import RedisError

from app.core.settings import get_settings
from app.domains.sandbox.schemas import SandboxRunRecord, UploadQuota

RUN_RECORD_PREFIX = "sandbox:record:"
_SUBMISSION_PREFIX = "sandbox:submission:"
_record_codec = TypeAdapter(SandboxRunRecord)


def _submission_client():
    return Redis.from_url(get_settings().redis_url, socket_timeout=2, socket_connect_timeout=2)


def save_pending_submission(run_id: str, contents: bytes, expires_at: datetime) -> None:
    _submission_client().set(f"{_SUBMISSION_PREFIX}{run_id}", contents, exat=expires_at)


def take_pending_submission(run_id: str) -> bytes | None:
    return _submission_client().getdel(f"{_SUBMISSION_PREFIX}{run_id}")


def delete_pending_submission(run_id: str) -> None:
    try:
        _submission_client().delete(f"{_SUBMISSION_PREFIX}{run_id}")
    except RedisError:
        pass


class RunStateStore(Protocol):
    """Protocol for managing run records, results, and upload quotas."""

    def save_run(self, record: SandboxRunRecord) -> None: ...

    def get_run(self, run_id: str) -> SandboxRunRecord | None: ...

    def list_runs(self) -> list[SandboxRunRecord]: ...

    def delete_run(self, run_id: str) -> None: ...

    def record_upload(self, session_id: str, timestamp: datetime) -> None: ...

    def unrecord_upload(self, session_id: str) -> None: ...

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

    def unrecord_upload(self, session_id: str) -> None:
        uploads = self._session_uploads.get(session_id)
        if uploads:
            uploads.pop()

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
        self._client = Redis.from_url(
            get_settings().redis_url, decode_responses=True, socket_timeout=2, socket_connect_timeout=2,
        )

    def _redis_conn(self):
        return self._client

    def save_run(self, record: SandboxRunRecord) -> None:
        expiry = int(record.expires_at.timestamp())
        if expiry <= datetime.now(UTC).timestamp():
            return
        shared = replace(record, zip_data_b64=None, stdin=None, expected_manifest=None, result=None)
        self._redis_conn().set(f"{RUN_RECORD_PREFIX}{record.run_id}", _record_codec.dump_json(shared), exat=expiry)

    def get_run(self, run_id: str) -> SandboxRunRecord | None:
        try:
            raw = self._redis_conn().get(f"{RUN_RECORD_PREFIX}{run_id}")
            record = _record_codec.validate_json(raw) if raw is not None else None
        except RedisError:
            return None
        if record is not None and record.expires_at <= datetime.now(UTC):
            return None
        return record

    def list_run_ids(self) -> list[str]:
        try:
            return [key.removeprefix(RUN_RECORD_PREFIX) for key in self._redis_conn().scan_iter(match=f"{RUN_RECORD_PREFIX}*")]
        except RedisError:
            return []

    def list_runs(self) -> list[SandboxRunRecord]:
        return [record for run_id in self.list_run_ids() if (record := self.get_run(run_id)) is not None]

    def delete_run(self, run_id: str) -> None:
        try:
            self._redis_conn().delete(f"{RUN_RECORD_PREFIX}{run_id}")
        except RedisError:
            pass

    def record_upload(self, session_id: str, timestamp: datetime) -> None:
        # One transaction: append, keep only the newest `limit` uploads (older ones can
        # never count again within the window), refresh the expiry.
        settings = get_settings()
        key = f"sandbox:uploads:{session_id}"
        try:
            pipe = self._redis_conn().pipeline(transaction=True)
            pipe.rpush(key, str(timestamp.timestamp()))
            pipe.ltrim(key, -max(1, settings.sandbox_upload_limit), -1)
            pipe.expire(key, int(settings.sandbox_upload_window_seconds))
            pipe.execute()
        except Exception:
            self._fallback.record_upload(session_id, timestamp)

    def unrecord_upload(self, session_id: str) -> None:
        key = f"sandbox:uploads:{session_id}"
        try:
            removed = self._redis_conn().rpop(key)
            if removed is None:
                self._fallback.unrecord_upload(session_id)
        except Exception:
            self._fallback.unrecord_upload(session_id)

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

            # Read-only: rewriting the list here could drop an upload recorded concurrently.
            active_ts = []
            for raw in raw_uploads:
                try:
                    ts = float(raw)
                    if ts > cutoff_ts:
                        active_ts.append(ts)
                except ValueError:
                    pass

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

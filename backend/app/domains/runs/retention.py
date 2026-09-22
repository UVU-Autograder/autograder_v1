"""Official workspace retention. The shared local volume is the lock authority.

Locks protect short filesystem operations only, never execution or network waits.
Lock files deliberately survive cleanup: unlinking one would split lock ownership.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.audit_log import audit_event
from app.core.settings import get_settings
from app.domains.runs.models import RunSummary

REVIEW_WINDOW = timedelta(hours=23)
DELETION_WINDOW = timedelta(hours=24)
_LOCKS: dict[int, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()
_HELD = threading.local()
_OFFICIAL_NAME = re.compile(r"official_([1-9][0-9]*)(?:\.zip)?\Z")


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def workspace_root() -> Path:
    return get_settings().artifact_storage_path.parent / "workspaces"


def control_root() -> Path:
    return get_settings().artifact_storage_path.parent / "retention"


def review_expiry(run: RunSummary) -> datetime:
    return as_utc(run.review_expires_at or (as_utc(run.created_at) + REVIEW_WINDOW))


def deletion_deadline(run: RunSummary) -> datetime:
    return as_utc(run.deletion_deadline_at or (as_utc(run.created_at) + DELETION_WINDOW))


def available(run: RunSummary) -> bool:
    return run.retention_state == "available" and utc_now() < review_expiry(run)


def _unsafe_link(path: Path) -> bool:
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def validate_root() -> Path:
    root = workspace_root().absolute()
    for part in (root, *root.parents):
        if _unsafe_link(part):
            raise OSError("unsafe_workspace_root")
    return root


def validate_tree(path: Path) -> None:
    """Reject links/reparse points before reads, writes, or recursive deletion."""
    root = validate_root()
    path.absolute().relative_to(root)
    current = path.absolute()
    while current != root:
        if _unsafe_link(current):
            raise OSError("unsafe_workspace_path")
        current = current.parent
    if path.is_dir():
        for directory, directories, files in os.walk(path, followlinks=False):
            for name in directories + files:
                if _unsafe_link(Path(directory) / name):
                    raise OSError("unsafe_workspace_path")


@contextmanager
def run_lock(run_id: int, *, blocking: bool = True) -> Iterator[None]:
    if run_id < 1:
        raise ValueError("Invalid run ID")
    held = getattr(_HELD, "runs", None)
    if held is None:
        held = _HELD.runs = set()
    if run_id in held:
        yield
        return
    with _LOCKS_GUARD:
        local_lock = _LOCKS.setdefault(run_id, threading.RLock())
    acquired = local_lock.acquire(timeout=2 if blocking else 0)
    if not acquired:
        raise BlockingIOError("workspace_busy")
    try:
        directory = control_root() / "locks"
        directory.mkdir(parents=True, exist_ok=True)
        if any(_unsafe_link(p) for p in (directory, *directory.parents)):
            raise OSError("unsafe_lock_path")
        lock_path = directory / f"{run_id}.lock"
        if _unsafe_link(lock_path):
            raise OSError("unsafe_lock_path")
        with lock_path.open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            deadline = time.monotonic() + (2 if blocking else 0)
            while True:
                try:
                    if os.name == "nt":
                        import msvcrt

                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise BlockingIOError("workspace_busy") from None
                    time.sleep(0.02)
            held.add(run_id)
            try:
                yield
            finally:
                held.remove(run_id)
                if os.name == "nt":
                    import msvcrt

                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        local_lock.release()


def load_run(db: Session, run_id: int) -> RunSummary:
    run = db.scalar(select(RunSummary).where(
        RunSummary.id == run_id, RunSummary.workflow_type == "official",
    ).execution_options(populate_existing=True))
    if run is None:
        raise HTTPException(410, "Official review data is no longer available.")
    return run


@contextmanager
def access(run_id: int, db: Session | None = None) -> Iterator[RunSummary]:
    """Call only after route authorization. Fail closed on missing DB or expiry."""
    from app.db.session import SessionLocal

    own_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        with run_lock(run_id):
            run = load_run(session, run_id)
            if not available(run):
                raise HTTPException(410, "Official review data has expired or been cleaned up.")
            validate_tree(workspace_root() / f"official_{run_id}")
            validate_tree(workspace_root() / f"official_{run_id}.zip")
            yield run
    except SQLAlchemyError:
        session.rollback()
        raise HTTPException(503, "Retention status is unavailable. Retry later.") from None
    except OSError:
        raise HTTPException(503, "Workspace is unavailable. Retry later.") from None
    finally:
        if own_session:
            session.close()


def _delete_files(run_id: int) -> None:
    root = validate_root()
    paths = [root / f"official_{run_id}", root / f"official_{run_id}.zip"]
    for path in paths:
        validate_tree(path)
    failed = False
    for path in paths:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink(missing_ok=True)
        except OSError:
            failed = True
    if failed or any(os.path.lexists(path) for path in paths):
        raise OSError("deletion_failed")


def cleanup(run_id: int, db: Session, *, manual: bool = False) -> bool:
    """Caller authorizes manual requests. False means a retry is required."""
    try:
        with run_lock(run_id, blocking=manual):
            run = load_run(db, run_id)
            if manual and run.status in ("queue", "run"):
                raise HTTPException(409, "Wait for grading to finish before cleaning up this run.")
            if not manual and available(run):
                return False
            if run.retention_state != "deleted":
                run.retention_state = "cleanup_pending"
                run.cleanup_reason = run.cleanup_reason or ("manual" if manual else "expired")
                run.cleanup_last_attempt_at = utc_now()
                db.commit()  # Tombstone is durable before any deletion.
            try:
                _delete_files(run_id)
            except OSError:
                run.retention_state = "cleanup_failed"
                run.cleanup_failure_category = "workspace_deletion_failed"
                db.commit()
                audit_event("official.cleanup_failed", run_id=run_id,
                            failure_category="workspace_deletion_failed")
                return False
            run.retention_state = "deleted"
            run.deleted_at = run.deleted_at or utc_now()
            run.cleanup_failure_category = None
            db.commit()
            audit_event("official.workspace_deleted", run_id=run_id, workflow_type="official")
            return True
    except BlockingIOError:
        return False


def reconcile(db: Session) -> dict[str, int]:
    counts = {"cleaned_runs_count": 0, "error_count": 0, "busy_count": 0,
              "orphaned_cleaned_count": 0}
    run_ids = list(db.scalars(select(RunSummary.id).where(RunSummary.workflow_type == "official")))
    for run_id in run_ids:
        run = load_run(db, run_id)
        if available(run):
            continue
        if run.retention_state == "deleted" and not any(os.path.lexists(workspace_root() / name) for name in (f"official_{run_id}", f"official_{run_id}.zip")):
            continue
        if cleanup(run_id, db):
            counts["cleaned_runs_count"] += 1
        elif load_run(db, run_id).retention_state == "cleanup_failed":
            counts["error_count"] += 1
        else:
            counts["busy_count"] += 1
    root = validate_root()
    if root.exists():
        orphan_ids = {int(match[1]) for path in root.iterdir()
                      if (match := _OFFICIAL_NAME.fullmatch(path.name))}
        for run_id in orphan_ids.difference(run_ids):
            try:
                with run_lock(run_id, blocking=False):
                    # Recheck under lock; intake commits its row before creating files.
                    if db.get(RunSummary, run_id, populate_existing=True) is not None:
                        continue
                    _delete_files(run_id)
                    counts["orphaned_cleaned_count"] += 1
            except BlockingIOError:
                counts["busy_count"] += 1
            except OSError:
                counts["error_count"] += 1
    return counts


def write_heartbeat(*, healthy: bool, counts: dict[str, int]) -> None:
    root = control_root()
    root.mkdir(parents=True, exist_ok=True)
    payload = {"checked_at": utc_now().isoformat(), "healthy": healthy, **counts}
    temporary = root / f"heartbeat.{os.getpid()}.tmp"
    temporary.write_text(json.dumps(payload), encoding="utf-8")
    temporary.replace(root / "heartbeat.json")


def health(db: Session) -> dict:
    heartbeat: dict = {}
    try:
        heartbeat = json.loads((control_root() / "heartbeat.json").read_text(encoding="utf-8"))
        recent = (utc_now() - as_utc(datetime.fromisoformat(heartbeat["checked_at"]))).total_seconds() <= 180
    except (OSError, ValueError, KeyError, TypeError):
        recent = False
    runs = list(db.scalars(select(RunSummary).where(RunSummary.workflow_type == "official")))
    failed = sum(run.retention_state == "cleanup_failed" for run in runs)
    overdue = sum(run.retention_state != "deleted" and utc_now() >= deletion_deadline(run) for run in runs)
    return {"cleanup_service_healthy": bool(recent and heartbeat.get("healthy")),
            "cleanup_last_checked_at": heartbeat.get("checked_at"),
            "cleanup_failed_runs": failed, "cleanup_overdue_runs": overdue,
            "cleanup_orphan_errors": heartbeat.get("error_count", 0)}

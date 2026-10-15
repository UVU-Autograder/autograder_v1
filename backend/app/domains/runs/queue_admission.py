"""Durable, owned execution capacity; Redis is transport, not an authority."""
from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.domains.runs import retention
from app.domains.runs.models import ExecutionTicket, OfficialDispatch
from app.domains.runs.schemas import EtaBand, QueueBackpressure

HIGH_LOAD_THRESHOLD = 40
FULL_QUEUE_THRESHOLD = 50
# Longer than the 180s hard task limit plus Judge0's maximum 45s wall time.
ACTIVE_LEASE_SECONDS = 240
# Scheduling transactions are a few milliseconds, but a burst of uploads queues up
# behind each other (and behind workers' claims). With a 2 s wait, 12 of 16
# simultaneous uploads were turned away as "busy" in a local stress run.
SCHEDULER_LOCK_TIMEOUT_SECONDS = 10.0


class QueueFullError(Exception):
    pass


@contextmanager
def transaction():
    lock = retention.control_lock("scheduler", timeout=SCHEDULER_LOCK_TIMEOUT_SECONDS)
    try:
        lock.__enter__()
    except OSError:
        raise HTTPException(503, "Scheduling is unavailable. Retry later.") from None
    try:
        try:
            with SessionLocal() as db:
                yield db
                db.commit()
        except SQLAlchemyError:
            raise HTTPException(503, "Scheduling is unavailable. Retry later.") from None
    finally:
        lock.__exit__(None, None, None)


def _count(db, state: str) -> int:
    return db.scalar(select(func.count()).select_from(ExecutionTicket).where(
        ExecutionTicket.state == state,
        ExecutionTicket.expires_at > retention.utc_now(),
    )) or 0


def waiting_count() -> int:
    with transaction() as db:
        return _count(db, "waiting")


def reserve_execution_slots(count: int, *, owner: str | None = None, ttl: int = 3600) -> int:
    """Reserve waiting work. Anonymous reservations support isolated mock callers."""
    with transaction() as db:
        current = _count(db, "waiting")
        if owner and db.get(ExecutionTicket, owner):
            return current
        if current + count > FULL_QUEUE_THRESHOLD:
            raise QueueFullError("Grading queue is full (50 waiting jobs). Retry later.")
        for _ in range(count):
            db.add(ExecutionTicket(
                owner=owner or f"anonymous:{uuid4()}", token=str(uuid4()), state="waiting",
                created_at=retention.utc_now(),
                expires_at=retention.utc_now() + timedelta(seconds=ttl),
            ))
        return current + count


def claim(owner: str, token: str | None = None) -> str | None:
    """Claim once, without a filesystem/DB lock held during execution."""
    with transaction() as db:
        ticket = db.get(ExecutionTicket, owner)
        if not ticket or ticket.state != "waiting" or retention.as_utc(ticket.expires_at) <= retention.utc_now():
            return None
        if token is not None and ticket.token != token:
            return None
        if _count(db, "active") >= get_settings().judge0_max_concurrent:
            raise QueueFullError("Execution capacity is busy.")
        ticket.state = "active"
        ticket.expires_at = retention.utc_now() + timedelta(seconds=ACTIVE_LEASE_SECONDS)
        if owner.startswith("official:"):
            dispatch = db.get(OfficialDispatch, int(owner.split(":")[1]))
            if dispatch:
                dispatch.attempts += 1
        return ticket.token


def assert_owner(owner: str, token: str) -> None:
    with transaction() as db:
        ticket = db.get(ExecutionTicket, owner)
        if not ticket or ticket.token != token or ticket.state != "active" or retention.as_utc(ticket.expires_at) <= retention.utc_now():
            raise HTTPException(409, "Execution attempt is no longer current.")


def cancel_waiting(owner: str) -> bool:
    with transaction() as db:
        ticket = db.get(ExecutionTicket, owner)
        if ticket and ticket.state == "active":
            return False
        if ticket:
            ticket.state = "done"
        return True


def ticket_state(owner: str) -> str | None:
    with transaction() as db:
        ticket = db.get(ExecutionTicket, owner)
        if not ticket:
            return None
        if ticket.state in ("waiting", "active") and retention.as_utc(ticket.expires_at) <= retention.utc_now():
            return "expired"
        return ticket.state


def release_execution_slots(count: int = 1, *, owner: str | None = None, token: str | None = None) -> int:
    """Idempotent owned release. Never decrement another run's reservation."""
    with transaction() as db:
        if owner:
            ticket = db.get(ExecutionTicket, owner)
            if ticket and (token is None or ticket.token == token):
                ticket.state = "done"
        else:
            tickets = db.scalars(select(ExecutionTicket).where(
                ExecutionTicket.owner.like("anonymous:%"), ExecutionTicket.state == "waiting",
            ).limit(max(0, count)))
            for ticket in tickets:
                ticket.state = "done"
        db.flush()
        return _count(db, "waiting")


def reset_admission_state_for_tests() -> None:
    with transaction() as db:
        db.execute(delete(ExecutionTicket))


def backpressure_for(waiting: int) -> QueueBackpressure:
    return QueueBackpressure(
        high_load_threshold=HIGH_LOAD_THRESHOLD, full_queue_threshold=FULL_QUEUE_THRESHOLD,
        current_waiting=waiting, high_load=waiting >= HIGH_LOAD_THRESHOLD,
        accepting_runs=waiting < FULL_QUEUE_THRESHOLD,
    )


def backpressure_snapshot() -> QueueBackpressure:
    snapshot = queue_snapshot()
    waiting = snapshot.waiting if snapshot is not None else waiting_count()
    return backpressure_for(waiting)


@dataclass(frozen=True)
class QueueSnapshot:
    """Aggregate scheduling counts. ``ahead`` is how many waiting submissions were queued
    before ``owner``'s (None when the owner is not waiting). Counts only -- never identities."""

    waiting: int
    active: int
    ahead: int | None
    owner_state: str | None


def queue_snapshot(owner: str | None = None) -> QueueSnapshot | None:
    """Read-only counts for status polling, without the scheduler lock.

    Status polls are the highest-volume scheduling call. Taking the write lock for
    them made a busy queue answer polls with 503s; plain reads are consistent
    enough for a progress display. Returns None when the database is unreachable.
    """
    try:
        with SessionLocal() as db:
            now = retention.utc_now()
            waiting = _count(db, "waiting")
            active = _count(db, "active")
            ahead: int | None = None
            owner_state: str | None = None
            if owner:
                ticket = db.get(ExecutionTicket, owner)
                if ticket is not None:
                    expired = (
                        ticket.state in ("waiting", "active")
                        and retention.as_utc(ticket.expires_at) <= now
                    )
                    owner_state = "expired" if expired else ticket.state
                    if owner_state == "waiting":
                        ahead = db.scalar(select(func.count()).select_from(ExecutionTicket).where(
                            ExecutionTicket.state == "waiting",
                            ExecutionTicket.expires_at > now,
                            ExecutionTicket.created_at < ticket.created_at,
                        )) or 0
            return QueueSnapshot(waiting=waiting, active=active, ahead=ahead, owner_state=owner_state)
    except SQLAlchemyError:
        return None


def eta_seconds_for(ahead: int, mean_grade_seconds: float, throughput_per_second: float | None = None) -> int:
    """Rough wait until a waiting run starts.

    The ideal estimate assumes every execution slot is always busy:
    ceil((ahead + 1) / slots) rounds of the mean grading time. When recent
    completions show the grader is actually slower (claim retries, a single Judge0
    worker), the observed rate wins; the estimate never drops below the ideal one.
    """
    slots = max(1, get_settings().judge0_max_concurrent)
    ideal = math.ceil((ahead + 1) / slots) * mean_grade_seconds
    observed = (ahead + 1) / throughput_per_second if throughput_per_second else 0.0
    return max(1, round(max(ideal, observed)))


def eta_band_for_position(position: int | None) -> EtaBand | None:
    if position is None or position < 1:
        return None
    if position <= 2:
        return "under_1_min"
    if position <= 6:
        return "1_to_3_min"
    if position <= 10:
        return "3_to_5_min"
    return "over_5_min"

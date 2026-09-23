"""Durable, owned execution capacity; Redis is transport, not an authority."""
from __future__ import annotations

from contextlib import contextmanager
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


class QueueFullError(Exception):
    pass


@contextmanager
def transaction():
    lock = retention.control_lock("scheduler")
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


def backpressure_snapshot() -> QueueBackpressure:
    waiting = waiting_count()
    return QueueBackpressure(
        high_load_threshold=HIGH_LOAD_THRESHOLD, full_queue_threshold=FULL_QUEUE_THRESHOLD,
        current_waiting=waiting, high_load=waiting >= HIGH_LOAD_THRESHOLD,
        accepting_runs=waiting < FULL_QUEUE_THRESHOLD,
    )


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

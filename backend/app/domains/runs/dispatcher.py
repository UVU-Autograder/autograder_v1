"""Restart-safe official outbox. Only run IDs and attempt tokens reach the broker."""
from collections.abc import Callable
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.settings import get_settings
from app.domains.runs import retention
from app.domains.runs.models import ExecutionTicket, OfficialDispatch, RunSummary
from app.domains.runs.queue_admission import FULL_QUEUE_THRESHOLD, _count, transaction


def sweep(publish: Callable[[int, str], object] | None = None) -> dict:
    publisher: Callable[[int, str], object]
    if publish is None:
        from app.domains.runs.tasks import grade_official_run
        def default_publish(run_id: int, token: str) -> object:
            return grade_official_run.apply_async(args=[run_id, token], task_id=token, expires=60)
        publisher = default_publish
    else:
        publisher = publish
    outgoing = []
    now = retention.utc_now()
    with transaction() as db:
        db.execute(delete(ExecutionTicket).where(
            ExecutionTicket.state.in_(("done", "expired")),
            ExecutionTicket.expires_at < now - timedelta(days=1),
        ))
        # Expired sandbox deliveries become terminal, rather than leaking capacity.
        for ticket in db.scalars(select(ExecutionTicket).where(
            ExecutionTicket.expires_at <= now, ExecutionTicket.state.in_(("waiting", "active")),
        )):
            ticket.state = "expired"
        db.flush()
        official_inflight = sum(1 for t in db.scalars(select(ExecutionTicket).where(
            ExecutionTicket.owner.like("official:%"),
            ExecutionTicket.state.in_(("waiting", "active")), ExecutionTicket.expires_at > now,
        )))
        budget = min(FULL_QUEUE_THRESHOLD - _count(db, "waiting"),
                     get_settings().judge0_max_concurrent - official_inflight)
        rows = db.execute(select(OfficialDispatch, RunSummary).join(
            RunSummary, OfficialDispatch.run_id == RunSummary.id,
        ).where(RunSummary.status.in_(("queue", "run"))).order_by(
            OfficialDispatch.next_attempt_at, OfficialDispatch.run_id,
        )).all()
        for dispatch, run in rows:
            if not retention.available(run):
                run.status = "failure"
                run.failure_summary = {"error": "review_expired"}
                # Active capacity remains reserved until the worker exits or its
                # lease expires, even if retention already removed its workspace.
                continue
            if not dispatch.ready:
                if now - retention.as_utc(dispatch.next_attempt_at) > timedelta(minutes=5):
                    run.status = "failure"
                    run.failure_summary = {"error": "intake_interrupted"}
                continue
            owner = f"official:{run.id}"
            ticket = db.get(ExecutionTicket, owner)
            if ticket and ticket.state in ("waiting", "active"):
                continue
            if dispatch.attempts >= 3:
                run.status = "failure"
                run.failure_summary = {"error": "execution_interrupted"}
                continue
            if budget <= 0 or retention.as_utc(dispatch.next_attempt_at) > now:
                continue
            token = str(uuid4())
            if ticket is None:
                ticket = ExecutionTicket(owner=owner)
                db.add(ticket)
            ticket.token = token
            ticket.state = "waiting"
            ticket.created_at = now
            ticket.expires_at = now + timedelta(seconds=60)
            dispatch.next_attempt_at = now + timedelta(seconds=5)
            outgoing.append((run.id, token))
            budget -= 1
    failures = 0
    for run_id, token in outgoing:
        try:
            publisher(run_id, token)
        except Exception:
            # Publication might have succeeded. Keep the token's lease until it
            # expires; a delayed delivery cannot claim a replacement generation.
            failures += 1
    return {"published": len(outgoing) - failures, "publish_failures": failures}


def finish_step(run_id: int, token: str) -> None:
    with transaction() as db:
        ticket = db.get(ExecutionTicket, f"official:{run_id}")
        if ticket and ticket.token == token:
            ticket.state = "done"
            dispatch = db.get(OfficialDispatch, run_id)
            if dispatch:
                dispatch.attempts = 0
                dispatch.next_attempt_at = retention.utc_now()

"""Run lifecycle management module encapsulating state transitions, Redis counters, and DB updates."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from app.db.session import SessionLocal
from app.domains.runs.models import RunSummary
from app.domains.runs.orchestrator import (
    is_run_cancelled,
    set_run_state,
)
from app.domains.runs.queue_admission import (
    release_execution_slots,
)

logger = logging.getLogger(__name__)


class RunLifecycleTracker:
    """Manages the state lifecycle, Redis status notifications, and DB persistence for grading runs."""

    def __init__(self, run_id: int | str, total_submissions: int = 0):
        self.run_id = str(run_id)
        self.raw_run_id = run_id
        self.total_submissions = total_submissions
        self._unreleased_slots = total_submissions

    def is_cancelled(self) -> bool:
        return is_run_cancelled(self.run_id)

    def set_running(self, message: str = "Grading run executing.") -> None:
        set_run_state(
            self.run_id,
            "run",
            {
                "total": self.total_submissions,
                "queued": 0,
                "running": self.total_submissions,
                "completed": 0,
                "failed": 0,
                "warnings": 0,
                "message": message,
            },
        )

    def _update_db_run(self, **attrs: Any) -> None:
        if isinstance(self.raw_run_id, int):
            with SessionLocal() as db:
                run_db = db.scalar(select(RunSummary).where(RunSummary.id == self.raw_run_id))
                if run_db:
                    for key, val in attrs.items():
                        if val is not None:
                            setattr(run_db, key, val)
                    db.commit()

    def update_progress(
        self,
        success_count: int,
        warning_count: int,
        failure_count: int,
        timeout_count: int,
        failure_summary: dict,
    ) -> None:
        done = success_count + warning_count + failure_count + timeout_count
        set_run_state(
            self.run_id,
            "run",
            {
                "total": self.total_submissions,
                "queued": 0,
                "running": max(0, self.total_submissions - done),
                "completed": success_count + warning_count,
                "failed": failure_count + timeout_count,
                "warnings": warning_count,
                "message": "Official run executing.",
            },
        )
        self._update_db_run(
            success_count=success_count,
            warning_count=warning_count,
            failure_count=failure_count,
            timeout_count=timeout_count,
            failure_summary=failure_summary,
        )

    def mark_complete(
        self,
        success_count: int,
        warning_count: int,
        failure_count: int,
        failure_summary: dict | None = None,
    ) -> None:
        self._update_db_run(
            status="complete",
            success_count=success_count,
            warning_count=warning_count,
            failure_count=failure_count,
            failure_summary=failure_summary,
        )
        set_run_state(
            self.run_id,
            "complete",
            {
                "total": self.total_submissions,
                "queued": 0,
                "running": 0,
                "completed": success_count + warning_count,
                "failed": failure_count,
                "warnings": warning_count,
                "message": "Run complete.",
            },
        )

    def mark_failure(self, message: str, category: str = "internal_error") -> None:
        self._update_db_run(
            status="failure",
            failure_summary={"error": category},
        )
        set_run_state(self.run_id, "failure", {"message": message})

    def release_slots(self, count: int) -> None:
        if count > 0:
            release_execution_slots(count)
            self._unreleased_slots = max(0, self._unreleased_slots - count)

    def release_remaining_slots(self) -> None:
        if self._unreleased_slots > 0:
            release_execution_slots(self._unreleased_slots)
            self._unreleased_slots = 0

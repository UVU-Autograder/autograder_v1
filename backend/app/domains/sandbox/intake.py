"""Deep domain engine for student sandbox run intake, validation, and dispatch."""
from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from secrets import token_urlsafe
from typing import Any

from sqlalchemy.orm import Session

from app.domains.assignments.inventory import inventory_status
from app.domains.assignments.service import (
    effective_allowed_concepts,
    get_assignment_for_course,
)
from app.domains.assignments.validation import run_preflight_validation
from app.domains.runs.queue_admission import (
    QueueFullError,
    eta_band_for_position,
    queue_snapshot,
    release_execution_slots,
    reserve_execution_slots,
)
from app.domains.sandbox import ip_limit
from app.domains.sandbox.catalog import get_sandbox_assignment
from app.domains.sandbox.schemas import (
    SandboxRunCreateResponse,
    SandboxRunRecord,
    UploadQuota,
)
from app.domains.sandbox.service import (
    SandboxService,
    sandbox_service,
)

logger = logging.getLogger(__name__)


class SandboxIntakeError(Exception):
    """Base class for domain errors during sandbox intake."""

    def __init__(self, message: str, session_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.session_id = session_id


class AssignmentNotFoundError(SandboxIntakeError):
    """The requested course or assignment does not exist."""

    def __init__(self, course_id: str, assignment_id: str, session_id: str | None = None) -> None:
        super().__init__(f"Assignment '{assignment_id}' in course '{course_id}' was not found.", session_id)
        self.course_id = course_id
        self.assignment_id = assignment_id


class AssignmentNotGradableError(SandboxIntakeError):
    """The assignment failed preflight checks or requires reference validation."""


class SessionQuotaExceededError(SandboxIntakeError):
    """The student sandbox session has exhausted its allowed uploads for the window."""

    session_id: str

    def __init__(self, quota: UploadQuota, session_id: str) -> None:
        super().__init__(f"Sandbox upload quota exhausted for session {session_id}.", session_id)
        self.quota = quota
        self.session_id = session_id


class NetworkRateLimitExceededError(SandboxIntakeError):
    """Too many runs have been initiated from the client network IP."""

    session_id: str

    def __init__(self, reset_at: str, limit: int, session_id: str) -> None:
        super().__init__("Network rate limit exceeded.", session_id)
        self.reset_at = reset_at
        self.limit = limit
        self.session_id = session_id


class GradingQueueFullError(SandboxIntakeError):
    """The execution queue is at capacity and rejecting new sandbox runs."""

    def __init__(self, retry_after_seconds: int = 15, session_id: str = "") -> None:
        super().__init__("The grading queue is full.", session_id)
        self.retry_after_seconds = retry_after_seconds
        self.session_id = session_id


class GraderServiceUnavailableError(SandboxIntakeError):
    """The grader or scheduling service is temporarily unreachable."""

    def __init__(
        self,
        code: str = "busy",
        message: str = "The grader is busy. Retrying automatically.",
        retry_after_seconds: int = 5,
        session_id: str = "",
    ) -> None:
        super().__init__(message, session_id)
        self.code = code
        self.retry_after_seconds = retry_after_seconds
        self.session_id = session_id


@dataclass(frozen=True)
class SandboxIntakeResult:
    """Outcome of a successful submission intake."""

    response: SandboxRunCreateResponse
    session_id: str


class SandboxIntakeEngine:
    """Deep domain engine encapsulating sandbox intake, validation, quotas, and dispatch."""

    def __init__(self, service: SandboxService | None = None) -> None:
        self._service = service or sandbox_service

    def intake_submission(
        self,
        db: Session,
        *,
        course_id: str,
        assignment_id: str,
        session_id: str | None,
        zip_data: bytes,
        stdin: str | None = None,
        client_ip: str | None = None,
    ) -> SandboxIntakeResult:
        """Validate an assignment, enforce quota/IP limits, register the run, and dispatch."""
        session = session_id or self._service._new_session()

        db_assignment = get_assignment_for_course(db, course_id, assignment_id)
        if db_assignment is None or db_assignment.config is None:
            raise AssignmentNotFoundError(course_id, assignment_id, session_id=session)

        sandbox_assignment = get_sandbox_assignment(
            db,
            course_id,
            assignment_id,
            self._service.quota_for_session(session),
        )
        if sandbox_assignment is None:
            raise AssignmentNotFoundError(course_id, assignment_id, session_id=session)

        preflight_errors = run_preflight_validation(db, course_id, assignment_id)
        if preflight_errors:
            raise AssignmentNotGradableError(
                "Assignment is not ready for grading. Contact your instructor.",
                session_id=session,
            )

        if inventory_status(db, db_assignment) != "ready":
            raise AssignmentNotGradableError(
                "Assignment requires instructor reference validation before grading.",
                session_id=session,
            )

        artifact_refs: dict[str, str] = {
            art.artifact_key: art.storage_ref
            for art in db_assignment.artifacts
            if art.storage_ref
        }
        allowed_concepts = effective_allowed_concepts(db_assignment)

        run_config: dict[str, Any] = (
            dict(db_assignment.config.config)
            if db_assignment.config and db_assignment.config.config
            else {}
        )
        if db_assignment.description and not run_config.get("description"):
            run_config["description"] = db_assignment.description
        run_config["_relational_assignment_id"] = db_assignment.id
        run_config["_session_id"] = session
        run_config["_assignment_code"] = db_assignment.slug
        run_config["_course_code"] = course_id

        expected_manifest = (
            db_assignment.config.validated_test_manifest
            if db_assignment.config
            else None
        )
        max_score = sandbox_assignment.max_score

        # Release database connection before entering the concurrency scheduler lock
        # to prevent pool starvation under bursts.
        db.close()

        quota = self._service.quota_for_session(session)
        if quota.remaining <= 0:
            raise SessionQuotaExceededError(quota=quota, session_id=session)

        limited = ip_limit.charge(client_ip)
        if limited is not None:
            raise NetworkRateLimitExceededError(
                reset_at=limited.reset_at,
                limit=limited.limit,
                session_id=session,
            )

        now = datetime.now(UTC)
        self._service._store.record_upload(session, now)

        run_id = f"run_{token_urlsafe(16)}"
        try:
            waiting = reserve_execution_slots(1, owner=run_id)
        except QueueFullError:
            ip_limit.refund(client_ip)
            self._service._store.unrecord_upload(session)
            raise GradingQueueFullError(retry_after_seconds=15, session_id=session) from None
        except Exception as exc:
            ip_limit.refund(client_ip)
            self._service._store.unrecord_upload(session)
            if hasattr(exc, "status_code") and exc.status_code == 503:
                raise GraderServiceUnavailableError(
                    code="busy",
                    message="The grader is busy. Retrying automatically.",
                    retry_after_seconds=5,
                    session_id=session,
                ) from None
            raise GraderServiceUnavailableError(
                code="grader_unavailable",
                message="The grader could not start your run. Please try again in a minute.",
                retry_after_seconds=60,
                session_id=session,
            ) from exc

        record = SandboxRunRecord(
            run_id=run_id,
            session_id=session,
            course_id=course_id,
            assignment_id=assignment_id,
            queue_position=max(1, waiting),
            max_score=max_score,
        )

        try:
            self._service._store.save_run(record)
        except Exception as exc:
            ip_limit.refund(client_ip)
            release_execution_slots(owner=run_id)
            self._service._store.unrecord_upload(session)
            raise GraderServiceUnavailableError(
                code="grader_unavailable",
                message="The grader could not start your run. Please try again in a minute.",
                retry_after_seconds=60,
                session_id=session,
            ) from exc

        zip_b64 = base64.b64encode(zip_data).decode("ascii")
        record.zip_data_b64 = zip_b64
        record.config = run_config
        record.expected_manifest = expected_manifest
        record.artifact_refs = artifact_refs
        record.allowed_concepts = allowed_concepts
        record.stdin = stdin

        if self._service._use_celery:
            from app.domains.runs.tasks import grade_sandbox_run, set_run_state

            try:
                set_run_state(
                    run_id,
                    "queue",
                    {
                        "queue_position": record.queue_position,
                        "eta_band": eta_band_for_position(record.queue_position),
                    },
                )
            except Exception:
                pass

            try:
                self._service._store.save_run(record)
                grade_result = grade_sandbox_run.delay(
                    run_id=run_id,
                    zip_data_b64=zip_b64,
                    config=run_config,
                    artifact_refs=artifact_refs,
                    allowed_concepts=allowed_concepts,
                    stdin=stdin,
                    expected_manifest=expected_manifest,
                )
                record.celery_task_id = grade_result.id
                self._service._store.save_run(record)
            except Exception as exc:
                from app.domains.runs.queue_admission import cancel_waiting

                cancel_waiting(run_id)
                ip_limit.refund(client_ip)
                self._service._store.unrecord_upload(session)
                raise GraderServiceUnavailableError(
                    code="grader_unavailable",
                    message="The grader could not start your run. Please try again in a minute.",
                    retry_after_seconds=60,
                    session_id=session,
                ) from exc

        if self._service._use_celery:
            status = self._service._build_status(
                run_id, "queue", None, None, queue_snapshot(run_id)
            )
        else:
            status = self._service._status_for(record)

        create_response = SandboxRunCreateResponse(
            run_id=run_id,
            sandbox_session=session,
            status_url=f"/runs/{run_id}/status",
            result_url=f"/sandbox/runs/{run_id}/result",
            upload_quota=self._service.quota_for_session(session),
            initial_status=status,
            file_preview=self._service._file_preview(),
        )
        return SandboxIntakeResult(response=create_response, session_id=session)


sandbox_intake_engine = SandboxIntakeEngine(sandbox_service)

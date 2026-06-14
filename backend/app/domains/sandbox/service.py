from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

from app.domains.runs.schemas import (
    QueueBackpressure,
    RunCounters,
    RunStatusResponse,
    RunState,
)
from app.domains.sandbox.schemas import (
    FilePreviewMetadata,
    SandboxAssignmentDetail,
    SandboxAssignmentListResponse,
    SandboxAssignmentSummary,
    SandboxCancelResponse,
    SandboxConstraint,
    SandboxCourse,
    SandboxCourseListResponse,
    SandboxRubricItem,
    SandboxRunCreateResponse,
    SandboxRunResultResponse,
    SandboxWarning,
    TestSummary,
    UploadQuota,
)

UPLOAD_LIMIT = 5
UPLOAD_WINDOW = timedelta(hours=1)
SESSION_TTL = timedelta(hours=1)
HIGH_LOAD_THRESHOLD = 40
FULL_QUEUE_THRESHOLD = 50


@dataclass
class SandboxRunRecord:
    run_id: str
    session_id: str
    course_id: str
    assignment_id: str
    state: RunState = "queue"
    status_reads: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(
        default_factory=lambda: datetime.now(UTC) + SESSION_TTL
    )
    queue_position: int = 1
    warnings: int = 1
    max_score: int = 100


class SandboxService:
    """In-memory contract store with optional Celery dispatch.

    When use_celery=True, create_run dispatches a real Celery task and
    run state is tracked in Redis. When use_celery=False (default for
    contract tests), the service uses the original in-memory mock behavior.
    """

    def __init__(self, use_celery: bool = False) -> None:
        self._use_celery = use_celery
        self._runs: dict[str, SandboxRunRecord] = {}
        self._session_uploads: dict[str, list[datetime]] = {}

    def quota_for_session(self, session_id: str | None) -> UploadQuota:
        return self._quota_for(session_id)

    def create_run(
        self,
        course_id: str,
        assignment_id: str,
        session_id: str | None,
        assignment_exists: bool | None = None,
        max_score: int = 100,
        zip_data: bytes | None = None,
        config_json: dict | None = None,
        artifact_refs: dict[str, str] | None = None,
        allowed_concepts: list[str] | None = None,
    ) -> tuple[SandboxRunCreateResponse | None, str, int | None]:
        if not assignment_exists:
            return None, session_id or self._new_session(), None

        session = session_id or self._new_session()
        quota = self._quota_for(session)
        if quota.remaining <= 0:
            return None, session, 429

        if self._queued_count() >= FULL_QUEUE_THRESHOLD:
            return None, session, 503

        now = datetime.now(UTC)
        self._session_uploads.setdefault(session, []).append(now)
        run_id = f"run_{token_urlsafe(16)}"
        record = SandboxRunRecord(
            run_id=run_id,
            session_id=session,
            course_id=course_id,
            assignment_id=assignment_id,
            queue_position=self._queued_count() + 1,
            max_score=max_score,
        )
        self._runs[run_id] = record

        # Dispatch Celery task if enabled and ZIP data is provided
        if self._use_celery and zip_data is not None and config_json is not None:
            import base64
            from app.domains.runs.tasks import grade_sandbox_run, set_run_state

            zip_b64 = base64.b64encode(zip_data).decode("ascii")
            set_run_state(run_id, "queue", {"queue_position": record.queue_position})
            grade_sandbox_run.delay(
                run_id=run_id,
                zip_data_b64=zip_b64,
                config_json=config_json,
                artifact_refs=artifact_refs or {},
                allowed_concepts=allowed_concepts or [],
            )

        status = self._status_for(record)
        return (
            SandboxRunCreateResponse(
                run_id=run_id,
                sandbox_session=session,
                status_url=f"/runs/{run_id}/status",
                result_url=f"/sandbox/runs/{run_id}/result",
                upload_quota=self._quota_for(session),
                initial_status=status,
                file_preview=self._file_preview(),
            ),
            session,
            None,
        )

    def get_status(self, run_id: str) -> RunStatusResponse | None:
        self._expire_old_runs()

        # Try Redis first if Celery mode is active
        if self._use_celery:
            from app.domains.runs.tasks import get_run_state
            redis_state = get_run_state(run_id)
            if redis_state is not None:
                state = redis_state.get("state", "queue")
                record = self._runs.get(run_id)
                queue_pos = redis_state.get("queue_position")
                return RunStatusResponse(
                    run_id=run_id,
                    state=state,
                    queue_position=queue_pos if state == "queue" else None,
                    eta_band="1_to_3_min" if state == "queue" else None,
                    counters=self._counters(),
                    backpressure=self._backpressure(),
                    message=self._message_for(state),
                )

        # Fall back to in-memory mock
        record = self._runs.get(run_id)
        if record is None:
            return None
        status = self._status_for(record)
        self._advance(record)
        return status

    def cancel_run(
        self, run_id: str, session_id: str | None
    ) -> SandboxCancelResponse | None | str:
        self._expire_old_runs()
        record = self._runs.get(run_id)
        if record is None or record.session_id != session_id:
            return None
        if record.state != "queue":
            return "not_cancelable"
        record.state = "failure"

        # Also update Redis if in Celery mode
        if self._use_celery:
            from app.domains.runs.tasks import set_run_state
            set_run_state(run_id, "failure", {"failure_category": "cancelled"})

        return SandboxCancelResponse(
            run_id=run_id,
            state="failure",
            counters=self._counters(),
            backpressure=self._backpressure(),
            message="Queued sandbox run cancelled before execution started.",
        )

    def get_result(
        self, run_id: str, session_id: str | None
    ) -> SandboxRunResultResponse | None | str:
        self._expire_old_runs()
        record = self._runs.get(run_id)
        if record is None or record.session_id != session_id:
            return None

        # Try Redis for real results if in Celery mode
        if self._use_celery:
            from app.domains.runs.tasks import get_run_result, get_run_state
            redis_state = get_run_state(run_id)
            if redis_state is None:
                return "not_ready"
            state = redis_state.get("state", "queue")
            if state not in {"complete", "failure"}:
                return "not_ready"

            redis_result = get_run_result(run_id)
            if redis_result is None:
                return "not_ready"

            if state == "failure":
                return SandboxRunResultResponse(
                    run_id=run_id,
                    state="failure",
                    projected_score=0,
                    max_score=record.max_score,
                    warnings=[
                        SandboxWarning(
                            code=redis_result.get("failure_category", "internal_error"),
                            message=redis_result.get("failure_message", "Run failed."),
                        )
                    ],
                    test_summaries=[],
                    sanitized_feedback="The sandbox run ended with an error.",
                    file_preview=self._file_preview(),
                    retention_notice="Sandbox results are session-only and are not retained as student submissions.",
                )

            # Build test summaries from real results
            test_summaries = []
            for tr in redis_result.get("test_results", []):
                test_summaries.append(
                    TestSummary(
                        label=tr.get("label", tr.get("key", "Unknown")),
                        status="passed" if tr.get("passed") else "failed",
                        points_awarded=tr.get("points_awarded", 0),
                        points_possible=tr.get("points", 0),
                        message=tr.get("label", ""),
                    )
                )

            warnings = [
                SandboxWarning(code=w.get("code", "warning"), message=w.get("message", ""))
                for w in redis_result.get("warnings", [])
            ]

            return SandboxRunResultResponse(
                run_id=run_id,
                state="complete",
                projected_score=redis_result.get("score", 0),
                max_score=redis_result.get("max_score", record.max_score),
                warnings=warnings,
                test_summaries=test_summaries,
                sanitized_feedback="Review your results above.",
                file_preview=self._file_preview(),
                retention_notice="Sandbox results are session-only and are not retained as student submissions.",
            )

        # In-memory mock behavior for contract tests
        if record.state not in {"complete", "failure"}:
            return "not_ready"
        if record.state == "failure":
            return SandboxRunResultResponse(
                run_id=run_id,
                state="failure",
                projected_score=0,
                max_score=self._assignment_max_score(record),
                warnings=[
                    SandboxWarning(code="cancelled", message="Run did not execute.")
                ],
                test_summaries=[],
                sanitized_feedback="The sandbox run ended before projected grading completed.",
                file_preview=self._file_preview(),
                retention_notice="Sandbox results are session-only and are not retained as student submissions.",
            )
        return SandboxRunResultResponse(
            run_id=run_id,
            state="complete",
            projected_score=86,
            max_score=self._assignment_max_score(record),
            warnings=[
                SandboxWarning(
                    code="style_signal",
                    message="One style check reported a non-blocking improvement.",
                )
            ],
            test_summaries=[
                TestSummary(
                    label="Public behavior checks",
                    status="passed",
                    points_awarded=60,
                    points_possible=60,
                    message="Visible examples matched expected behavior.",
                ),
                TestSummary(
                    label="Edge-case checks",
                    status="warning",
                    points_awarded=26,
                    points_possible=40,
                    message="Some boundary behavior may need review.",
                ),
            ],
            sanitized_feedback=(
                "Your projected result is strong. Review boundary-case handling and keep "
                "the implementation organized before an official submission."
            ),
            file_preview=self._file_preview(),
            retention_notice="Sandbox results are session-only and are not retained as student submissions.",
        )

    def _quota_for(self, session_id: str | None) -> UploadQuota:
        now = datetime.now(UTC)
        if session_id is not None:
            uploads = [
                ts
                for ts in self._session_uploads.get(session_id, [])
                if now - ts < UPLOAD_WINDOW
            ]
            self._session_uploads[session_id] = uploads
        else:
            uploads = []
        reset_at = now + UPLOAD_WINDOW
        if uploads:
            reset_at = uploads[0] + UPLOAD_WINDOW
        return UploadQuota(
            remaining=max(UPLOAD_LIMIT - len(uploads), 0),
            reset_at=reset_at.isoformat(),
        )

    def _status_for(self, record: SandboxRunRecord) -> RunStatusResponse:
        return RunStatusResponse(
            run_id=record.run_id,
            state=record.state,
            queue_position=record.queue_position if record.state == "queue" else None,
            eta_band="1_to_3_min" if record.state == "queue" else None,
            counters=self._counters(),
            backpressure=self._backpressure(),
            message=self._message_for(record.state),
        )

    def _advance(self, record: SandboxRunRecord) -> None:
        record.status_reads += 1
        if record.state == "queue" and record.status_reads >= 1:
            record.state = "run"
        elif record.state == "run" and record.status_reads >= 2:
            record.state = "complete"

    def _message_for(self, state: RunState) -> str:
        return {
            "queue": "Sandbox run accepted and waiting for execution capacity.",
            "run": "Sandbox run is executing in the mock contract prototype.",
            "complete": "Sandbox run completed. Fetch session-only projected feedback from the sandbox result endpoint.",
            "failure": "Sandbox run ended with a coarse failure state.",
        }[state]

    def _counters(self) -> RunCounters:
        values = list(self._runs.values())
        return RunCounters(
            total=len(values),
            queued=sum(1 for item in values if item.state == "queue"),
            running=sum(1 for item in values if item.state == "run"),
            completed=sum(1 for item in values if item.state == "complete"),
            failed=sum(1 for item in values if item.state == "failure"),
            warnings=sum(item.warnings for item in values if item.state == "complete"),
        )

    def _backpressure(self) -> QueueBackpressure:
        waiting = self._queued_count()
        return QueueBackpressure(
            current_waiting=waiting,
            high_load=waiting >= HIGH_LOAD_THRESHOLD,
            accepting_runs=waiting < FULL_QUEUE_THRESHOLD,
        )

    def _queued_count(self) -> int:
        return sum(1 for item in self._runs.values() if item.state == "queue")

    def _assignment_max_score(self, record: SandboxRunRecord) -> int:
        return record.max_score

    def _file_preview(self) -> FilePreviewMetadata:
        return FilePreviewMetadata(
            preview_available=False,
            preview_kind="metadata_only",
            sanitized_entries=["submission_bundle", "source_file_1", "support_file_1"],
        )

    def _new_session(self) -> str:
        return f"sandbox_{token_urlsafe(18)}"

    def _expire_old_runs(self) -> None:
        now = datetime.now(UTC)
        expired = [run_id for run_id, run in self._runs.items() if run.expires_at < now]
        for run_id in expired:
            del self._runs[run_id]


# Default instance - use_celery=False preserves existing contract test behavior
sandbox_service = SandboxService(use_celery=False)

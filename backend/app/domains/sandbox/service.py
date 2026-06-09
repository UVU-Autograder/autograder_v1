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


class SandboxService:
    """Temporary in-memory contract store.

    Redis, Celery, Judge0, ZIP extraction, and real cleanup are intentionally out
    of scope here; this service exists to stabilize frontend/backend JSON.
    """

    def __init__(self) -> None:
        self._runs: dict[str, SandboxRunRecord] = {}
        self._session_uploads: dict[str, list[datetime]] = {}
        self._courses = [
            SandboxCourse(
                id="cs1400",
                title="CS 101: Programming Foundations",
                term="Spring 2026",
                sandbox_enabled_assignments=2,
            ),
            SandboxCourse(
                id="cs201",
                title="CS 201: Data Structures",
                term="Spring 2026",
                sandbox_enabled_assignments=1,
            ),
        ]
        self._assignments = {
            "cs1400": [
                SandboxAssignmentDetail(
                    id="loops-lab",
                    course_id="cs1400",
                    title="Loops Lab",
                    sandbox_enabled=True,
                    language="python",
                    due_label="Practice",
                    max_score=100,
                    upload_quota=self._quota_for("preview"),
                    description="Practice iteration, input validation, and simple aggregation.",
                    accepted_bundle_types=["application/zip", ".zip"],
                    max_upload_bytes=50 * 1024 * 1024,
                    constraints=[
                        SandboxConstraint(label="Runtime", value="2 seconds"),
                        SandboxConstraint(label="Memory", value="512 MB"),
                    ],
                    rubric=[
                        SandboxRubricItem(label="Correctness", points=70),
                        SandboxRubricItem(label="Style", points=20),
                        SandboxRubricItem(label="Edge cases", points=10),
                    ],
                ),
                SandboxAssignmentDetail(
                    id="functions-checkpoint",
                    course_id="cs1400",
                    title="Functions Checkpoint",
                    sandbox_enabled=True,
                    language="python",
                    due_label="Practice",
                    max_score=50,
                    upload_quota=self._quota_for("preview"),
                    description="Practice decomposition with small reusable functions.",
                    accepted_bundle_types=["application/zip", ".zip"],
                    max_upload_bytes=50 * 1024 * 1024,
                    constraints=[SandboxConstraint(label="Runtime", value="2 seconds")],
                    rubric=[
                        SandboxRubricItem(label="Function behavior", points=35),
                        SandboxRubricItem(label="Readable structure", points=15),
                    ],
                ),
            ],
            "cs201": [
                SandboxAssignmentDetail(
                    id="linked-list-practice",
                    course_id="cs201",
                    title="Linked List Practice",
                    sandbox_enabled=True,
                    language="python",
                    due_label="Practice",
                    max_score=100,
                    upload_quota=self._quota_for("preview"),
                    description="Practice linked-list insert, remove, and traversal behavior.",
                    accepted_bundle_types=["application/zip", ".zip"],
                    max_upload_bytes=50 * 1024 * 1024,
                    constraints=[
                        SandboxConstraint(label="Runtime", value="3 seconds"),
                        SandboxConstraint(label="Memory", value="768 MB"),
                    ],
                    rubric=[
                        SandboxRubricItem(label="Core operations", points=75),
                        SandboxRubricItem(label="Boundary cases", points=25),
                    ],
                )
            ],
        }

    def list_courses(self) -> SandboxCourseListResponse:
        return SandboxCourseListResponse(courses=self._courses)

    def list_assignments(
        self, course_id: str, session_id: str | None
    ) -> SandboxAssignmentListResponse | None:
        assignments = self._assignments.get(course_id)
        if assignments is None:
            return None
        return SandboxAssignmentListResponse(
            course_id=course_id,
            assignments=[self._summary(item, session_id) for item in assignments],
        )

    def get_assignment(
        self, course_id: str, assignment_id: str, session_id: str | None
    ) -> SandboxAssignmentDetail | None:
        assignment = self._find_assignment(course_id, assignment_id)
        if assignment is None:
            return None
        return assignment.model_copy(
            update={"upload_quota": self._quota_for(session_id)}
        )

    def create_run(
        self,
        course_id: str,
        assignment_id: str,
        session_id: str | None,
    ) -> tuple[SandboxRunCreateResponse | None, str, int | None]:
        assignment = self._find_assignment(course_id, assignment_id)
        if assignment is None:
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
        )
        self._runs[run_id] = record

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

    def _find_assignment(
        self, course_id: str, assignment_id: str
    ) -> SandboxAssignmentDetail | None:
        for assignment in self._assignments.get(course_id, []):
            if assignment.id == assignment_id and assignment.sandbox_enabled:
                return assignment
        return None

    def _summary(
        self, assignment: SandboxAssignmentDetail, session_id: str | None
    ) -> SandboxAssignmentSummary:
        return SandboxAssignmentSummary(
            id=assignment.id,
            course_id=assignment.course_id,
            title=assignment.title,
            sandbox_enabled=assignment.sandbox_enabled,
            language=assignment.language,
            due_label=assignment.due_label,
            max_score=assignment.max_score,
            upload_quota=self._quota_for(session_id),
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
        assignment = self._find_assignment(record.course_id, record.assignment_id)
        return assignment.max_score if assignment is not None else 100

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


sandbox_service = SandboxService()

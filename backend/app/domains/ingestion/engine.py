"""Submission ingestion engine module encapsulating Canvas archive intake, section authority checks, and run creation."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.domains.assignments.service import get_assignment_for_course
from app.domains.assignments.validation import run_preflight_validation
from app.domains.courses.models import Course, Section
from app.domains.ingestion.extractor import (
    ExtractionError,
    count_canvas_submissions,
)
from app.domains.runs.models import RunSummary
from app.domains.runs.orchestrator import set_run_state
from app.domains.runs.queue_admission import (
    QueueFullError,
    backpressure_snapshot,
    eta_band_for_position,
    release_execution_slots,
    reserve_execution_slots,
)
from app.domains.runs.service import get_workspaces_dir, official_run_zip_path

logger = logging.getLogger(__name__)


class IngestError(Exception):
    """Domain failure during official Canvas ZIP ingest."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class SubmissionIngestionEngine:
    """Deep domain module managing Canvas archive intake, section authority checks, and official run creation."""

    def ingest_canvas_upload(
        self,
        db: Session,
        *,
        course_id: str,
        assignment_id: str,
        section_id: int,
        actor_user_id: int,
        filename: str,
        content: bytes,
    ) -> RunSummary:
        """Validate a Canvas ZIP, create a queued official run, persist, and dispatch."""
        settings = get_settings()

        if not filename.lower().endswith(".zip"):
            raise IngestError("Invalid file type. Only ZIP files are accepted.")

        if len(content) > settings.max_upload_bytes:
            raise IngestError(
                f"Upload size limit exceeded. Max size allowed is "
                f"{settings.max_upload_bytes / (1024 * 1024):.1f}MB."
            )

        assignment = get_assignment_for_course(db, course_id, assignment_id)
        if assignment is None:
            raise IngestError("Assignment not found.", status_code=404)

        course = db.scalar(select(Course).where(Course.code == course_id))
        if course is None:
            raise IngestError("Course not found.", status_code=404)

        section = db.scalar(
            select(Section).where(
                Section.id == section_id,
                Section.course_id == course.id,
                Section.is_active.is_(True),
            )
        )
        if section is None:
            raise IngestError("Section not found for this course.", status_code=404)

        preflight_errors = run_preflight_validation(db, course_id, assignment_id)
        if preflight_errors:
            raise IngestError(
                "Assignment is not ready for grading: " + "; ".join(preflight_errors)
            )

        try:
            submission_count = count_canvas_submissions(content)
        except ExtractionError as exc:
            raise IngestError(f"Invalid or unsafe ZIP file: {exc}") from exc

        if submission_count == 0:
            raise IngestError(
                "The ZIP file does not contain recognized Canvas submissions. "
                "Ensure filenames match Canvas export format."
            )

        try:
            waiting = reserve_execution_slots(submission_count)
        except QueueFullError as exc:
            raise IngestError(str(exc), status_code=429) from exc

        try:
            run = RunSummary(
                workflow_type="official",
                actor_user_id=actor_user_id,
                assignment_id=assignment.id,
                section_id=section.id,
                status="queue",
                total_submission_count=submission_count,
                success_count=0,
                warning_count=0,
                failure_count=0,
                timeout_count=0,
                failure_summary={},
                token_usage_metadata={},
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            get_workspaces_dir().mkdir(parents=True, exist_ok=True)
            official_run_zip_path(run.id).write_bytes(content)

            queue_position = max(1, waiting - submission_count + 1)
            set_run_state(
                str(run.id),
                "queue",
                {
                    "total": submission_count,
                    "queued": submission_count,
                    "running": 0,
                    "completed": 0,
                    "failed": 0,
                    "warnings": 0,
                    "queue_position": queue_position,
                    "eta_band": eta_band_for_position(queue_position),
                    "message": "Official run queued for execution.",
                    "high_load": backpressure_snapshot().high_load,
                },
            )

            if settings.sandbox_use_celery:
                from app.domains.runs.tasks import grade_official_run

                grade_official_run.delay(run.id)
            else:
                from app.domains.runs.tasks import run_mock_official_run

                run_mock_official_run(run.id)
                db.refresh(run)

            return run
        except Exception as exc:
            release_execution_slots(submission_count)
            if "run" in locals() and isinstance(run, RunSummary):
                try:
                    official_run_zip_path(run.id).unlink(missing_ok=True)
                    run.status = "failure"
                    run.failure_summary = {"error": f"Ingestion error: {exc}"}
                    db.commit()
                except Exception:
                    pass
            if isinstance(exc, OSError):
                raise IngestError("Failed to persist submission archive.", status_code=500) from exc
            raise


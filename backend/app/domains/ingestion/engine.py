"""Submission ingestion engine module encapsulating Canvas archive intake, section authority checks, and run creation."""

from __future__ import annotations

import logging
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.core.audit_log import audit_event
from app.db.session import SessionLocal
from app.domains.assignments.service import get_assignment_for_course
from app.domains.courses.models import Course, Section
from app.domains.ingestion.extractor import (
    ExtractionError,
    count_canvas_submissions,
)
from app.domains.runs.models import OfficialDispatch, RunSummary
from app.domains.runs import retention
from app.domains.runs.grading_package import (
    PackageCaptureError, atomic_write, capture_package, load_package, write_package,
)
from app.domains.runs.orchestrator import set_run_state
from app.domains.runs.queue_admission import (
    backpressure_snapshot,
    eta_band_for_position,
)
from app.domains.runs.service import get_workspaces_dir, official_run_dir, official_run_zip_path

logger = logging.getLogger(__name__)


class IngestError(Exception):
    """Domain failure during official Canvas ZIP ingest."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def resolve_failed_admission(run_id: int) -> Literal["admitted", "failed", "unknown"]:
    """Recheck durable readiness before removing any possibly admitted inputs."""
    try:
        with retention.run_lock(run_id), SessionLocal() as recovery:
            run = recovery.get(RunSummary, run_id)
            dispatch = recovery.get(OfficialDispatch, run_id)
            if dispatch and dispatch.ready:
                return "admitted"
            if run:
                run.status = "failure"
                run.failure_summary = {"error": "ingestion_error"}
                if dispatch:
                    dispatch.ready = False
                recovery.commit()
            # Only remove after confirming this batch is not dispatchable and
            # recording failure. The retention helper validates all target paths.
            retention._delete_files(run_id)
            return "failed"
    except Exception:
        # Files stay under normal retention/orphan reconciliation on DB or disk loss.
        logger.warning("Official admission recovery could not be confirmed")
        return "unknown"


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

        try:
            submission_count = count_canvas_submissions(content)
        except ExtractionError as exc:
            raise IngestError(f"Invalid or unsafe ZIP file: {exc}") from exc

        if submission_count == 0:
            raise IngestError(
                "The ZIP file does not contain recognized Canvas submissions. "
                "Ensure filenames match Canvas export format."
            )

        if submission_count > settings.official_batch_limit:
            raise IngestError(
                f"Official uploads are limited to {settings.official_batch_limit} submissions.",
                status_code=413,
            )

        try:
            package = capture_package(course_id, assignment_id)
        except PackageCaptureError as exc:
            raise IngestError("Assignment is not ready for grading: " + str(exc)) from None

        assignment_pk, course_pk, section_pk = assignment.id, course.id, section.id
        if package.assignment_id != assignment_pk:
            raise IngestError("Assignment changed during intake. Retry the upload.", status_code=409)

        run_id: int | None = None
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
            # Serialize intake capacity across API processes on the shared volume.
            # Only aggregate counts enter durable scheduling metadata.
            with retention.control_lock("scheduler"):
                unfinished = db.scalars(select(RunSummary).where(
                    RunSummary.workflow_type == "official",
                    RunSummary.status.in_(("queue", "run")),
                )).all()
                retained = sum(max(0, value.total_submission_count - value.success_count
                    - value.warning_count - value.failure_count - value.timeout_count)
                    for value in unfinished if retention.available(value))
                if retained + submission_count > settings.official_unfinished_limit:
                    raise IngestError("Official intake capacity is full. Retry later.", status_code=429)
                db.add(run)
                db.flush()
                run_id = run.id
                db.add(OfficialDispatch(run_id=run.id, ready=False,
                    next_attempt_at=retention.utc_now(), attempts=0))
                db.commit()
                db.refresh(run)

            with retention.access(run.id, db):
                get_workspaces_dir().mkdir(parents=True, exist_ok=True)
                directory = official_run_dir(run.id)
                directory.mkdir(parents=True, exist_ok=True)
                atomic_write(official_run_zip_path(run.id), content, temporary_directory=directory)
                write_package(run.id, package)
                load_package(run.id, assignment_id=assignment_pk)
                dispatch = db.get(OfficialDispatch, run.id)
                if dispatch is None:
                    raise IngestError("Official intake record is unavailable.", status_code=503)
                db.refresh(run)
                if run.status != "queue":
                    raise IngestError("Official intake was interrupted. Retry the upload.", status_code=503)
                dispatch.ready = True
                db.commit()
        except Exception as exc:
            try:
                db.rollback()
            except Exception:
                logger.warning("Official intake transaction reset unavailable")
            recovered = resolve_failed_admission(run_id) if run_id is not None else "failed"
            if recovered == "admitted":
                # Commit may have reached the server before the connection failed.
                # Never delete its inputs or pretend the accepted batch failed.
                try:
                    db.refresh(run)
                except Exception:
                    raise IngestError("Official intake is queued but its status is temporarily unavailable.", status_code=503) from None
            elif isinstance(exc, IngestError):
                raise
            else:
                raise IngestError("Official intake could not be confirmed. Check run status before retrying.",
                                  status_code=503 if recovered == "unknown" else 500) from None

        # Durable admission is complete. Cache/log/mock failures must never roll
        # back readiness, overwrite run status or delete committed package files.
        try:
            queue_position = None
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
                    "message": "Official batch retained; awaiting bounded dispatch.",
                    "high_load": backpressure_snapshot().high_load,
                },
            )

        except Exception:
            logger.warning("Official intake status cache update unavailable")
        try:
            audit_event(
                "official.ingest_queued",
                run_id=run.id,
                assignment_id=assignment_pk,
                course_id=course_pk,
                section_id=section_pk,
                actor_user_id=actor_user_id,
                submission_count=submission_count,
                workflow_type="official",
            )
        except Exception:
            logger.warning("Official intake audit emission unavailable")
        if not settings.sandbox_use_celery:
            from app.domains.runs.tasks import run_mock_official_run

            try:
                run_mock_official_run(run.id)
                db.refresh(run)
            except Exception:
                logger.warning("Official development mock execution unavailable")
        return run


"""Official Canvas ZIP ingestion orchestration.

Keeps ZIP/Canvas filesystem utilities in :mod:`extractor`; this module owns
the upload transaction: validate, create run metadata, persist archive, dispatch.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.domains.assignments.service import get_assignment_for_course
from app.domains.ingestion.extractor import ExtractionError, count_canvas_submissions
from app.domains.runs.models import RunSummary
from app.domains.runs.service import get_workspaces_dir, official_run_zip_path


class IngestError(Exception):
    """Domain failure during official Canvas ZIP ingest."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def ingest_official_canvas_zip(
    db: Session,
    *,
    course_id: str,
    assignment_id: str,
    actor_user_id: int,
    filename: str,
    content: bytes,
) -> RunSummary:
    """Validate a Canvas ZIP, create a queued official run, persist, and dispatch.

    Preserves commit-before-ZIP-write ordering and dispatches only after the
    archive is on disk. The worker re-extracts the persisted ZIP separately.
    """
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

    try:
        submission_count = count_canvas_submissions(content)
    except ExtractionError as exc:
        raise IngestError(f"Invalid or unsafe ZIP file: {exc}") from exc

    if submission_count == 0:
        raise IngestError(
            "The ZIP file does not contain recognized Canvas submissions. "
            "Ensure filenames match Canvas export format."
        )

    run = RunSummary(
        workflow_type="official",
        actor_user_id=actor_user_id,
        assignment_id=assignment.id,
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

    from app.domains.runs.tasks import grade_official_run, run_mock_official_run

    if settings.sandbox_use_celery:
        grade_official_run.delay(run.id)
    else:
        run_mock_official_run(run.id)
        db.refresh(run)

    return run

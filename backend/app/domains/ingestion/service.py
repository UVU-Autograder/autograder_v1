"""Official Canvas ZIP ingestion orchestration.

Keeps ZIP/Canvas filesystem utilities in :mod:`extractor`; this module owns
the upload transaction: validate, create run metadata, persist archive, dispatch.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.domains.ingestion.engine import IngestError as IngestError, SubmissionIngestionEngine
from app.domains.runs.models import RunSummary

_engine = SubmissionIngestionEngine()


def ingest_official_canvas_zip(
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
    return _engine.ingest_canvas_upload(
        db,
        course_id=course_id,
        assignment_id=assignment_id,
        section_id=section_id,
        actor_user_id=actor_user_id,
        filename=filename,
        content=content,
    )

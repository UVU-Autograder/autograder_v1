"""Service-level tests for official Canvas ZIP ingest."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.auth.models import User
from app.domains.ingestion import (
    IngestError,
    ingestion_engine,
)
from app.domains.runs.service import official_run_zip_path
from test_ingestion_extractor import create_zip_bytes


@pytest.fixture()
def staff_user(db_session):
    user = db_session.query(User).filter(User.email == "dev.staff@uvu.edu").one()
    return user


def test_ingest_official_canvas_zip_success(
    db_session, staff_user, section_id, mock_official_run_dispatch, temp_workspaces
):
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )

    run = ingestion_engine.ingest_canvas_upload(
        db_session,
        course_id="cs1400",
        assignment_id="simple-python-functions",
        section_id=section_id,
        actor_user_id=staff_user.id,
        filename="submissions.zip",
        content=zip_bytes,
    )

    assert run.status == "queue"
    assert run.workflow_type == "official"
    assert run.section_id == section_id
    assert run.total_submission_count == 1
    assert official_run_zip_path(run.id).read_bytes() == zip_bytes
    mock_official_run_dispatch.assert_called_once_with(run.id)


def test_ingest_rejects_non_zip(db_session, staff_user, section_id):
    with pytest.raises(IngestError, match="Only ZIP files"):
        ingestion_engine.ingest_canvas_upload(
            db_session,
            course_id="cs1400",
            assignment_id="simple-python-functions",
            section_id=section_id,
            actor_user_id=staff_user.id,
            filename="submissions.txt",
            content=b"not a zip",
        )


def test_ingest_rejects_oversized(db_session, staff_user, section_id, monkeypatch):
    from app.core.settings import get_settings

    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    with pytest.raises(IngestError, match="Upload size limit"):
        ingestion_engine.ingest_canvas_upload(
            db_session,
            course_id="cs1400",
            assignment_id="simple-python-functions",
            section_id=section_id,
            actor_user_id=staff_user.id,
            filename="submissions.zip",
            content=b"x" * 20,
        )


def test_ingest_rejects_missing_assignment(db_session, staff_user, section_id):
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )
    with pytest.raises(IngestError, match="Assignment not found") as exc_info:
        ingestion_engine.ingest_canvas_upload(
            db_session,
            course_id="cs1400",
            assignment_id="does-not-exist",
            section_id=section_id,
            actor_user_id=staff_user.id,
            filename="submissions.zip",
            content=zip_bytes,
        )
    assert exc_info.value.status_code == 404


def test_ingest_rejects_non_canvas_zip(db_session, staff_user, section_id):
    zip_bytes = create_zip_bytes({"main.py": b"print('hello')"})
    with pytest.raises(IngestError, match="recognized Canvas"):
        ingestion_engine.ingest_canvas_upload(
            db_session,
            course_id="cs1400",
            assignment_id="simple-python-functions",
            section_id=section_id,
            actor_user_id=staff_user.id,
            filename="submissions.zip",
            content=zip_bytes,
        )


def test_ingest_rejects_bad_section(db_session, staff_user):
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )
    with pytest.raises(IngestError, match="Section not found") as exc_info:
        ingestion_engine.ingest_canvas_upload(
            db_session,
            course_id="cs1400",
            assignment_id="simple-python-functions",
            section_id=99999,
            actor_user_id=staff_user.id,
            filename="submissions.zip",
            content=zip_bytes,
        )

    assert exc_info.value.status_code == 404

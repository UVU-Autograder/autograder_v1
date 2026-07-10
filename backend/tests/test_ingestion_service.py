"""Service-level tests for official Canvas ZIP ingest."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_domain_models  # noqa: E402
from app.db.seed import initialize_database  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.domains.auth.models import User  # noqa: E402
from app.domains.courses.models import Section  # noqa: E402
from app.domains.ingestion.service import IngestError, ingest_official_canvas_zip  # noqa: E402
from app.domains.runs.queue_admission import reset_admission_state_for_tests  # noqa: E402
from app.domains.runs.service import official_run_zip_path  # noqa: E402
from test_ingestion_extractor import create_zip_bytes  # noqa: E402


@pytest.fixture(autouse=True)
def db_session():
    import_domain_models()
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)
    reset_admission_state_for_tests()
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)


@pytest.fixture(autouse=True)
def temp_workspace_storage(tmp_path, monkeypatch):
    from app.core.settings import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    yield tmp_path


@pytest.fixture()
def staff_user(db_session):
    user = db_session.query(User).filter(User.email == "dev.staff@uvu.edu").one()
    return user


@pytest.fixture()
def section_id(db_session):
    section = db_session.scalar(select(Section).where(Section.crn == "12345"))
    assert section is not None
    return section.id


@pytest.fixture(autouse=True)
def mock_dispatch():
    with patch("app.domains.runs.tasks.run_mock_official_run") as mock:
        yield mock


def test_ingest_official_canvas_zip_success(db_session, staff_user, section_id, mock_dispatch):
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )

    run = ingest_official_canvas_zip(
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
    mock_dispatch.assert_called_once_with(run.id)


def test_ingest_rejects_non_zip(db_session, staff_user, section_id):
    with pytest.raises(IngestError, match="Only ZIP files"):
        ingest_official_canvas_zip(
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
        ingest_official_canvas_zip(
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
        ingest_official_canvas_zip(
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
        ingest_official_canvas_zip(
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
        ingest_official_canvas_zip(
            db_session,
            course_id="cs1400",
            assignment_id="simple-python-functions",
            section_id=99999,
            actor_user_id=staff_user.id,
            filename="submissions.zip",
            content=zip_bytes,
        )
    assert exc_info.value.status_code == 404

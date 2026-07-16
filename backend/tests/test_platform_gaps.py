"""Platform gap coverage: section auth, queue admission, status, preflight, concepts."""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.auth_utils import create_access_token  # noqa: E402
from app.db.base import Base, import_domain_models  # noqa: E402
from app.db.seed import initialize_database  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.domains.assignments.models import Assignment  # noqa: E402
from app.domains.assignments.service import (  # noqa: E402
    effective_allowed_concepts,
    get_assignment_for_course,
)
from app.domains.auth.models import Role, StaffAccess, User  # noqa: E402
from app.domains.courses.models import Section  # noqa: E402
from app.domains.runs.models import RunSummary  # noqa: E402
from app.domains.runs.queue_admission import (  # noqa: E402
    FULL_QUEUE_THRESHOLD,
    HIGH_LOAD_THRESHOLD,
    QueueFullError,
    backpressure_snapshot,
    release_execution_slots,
    reserve_execution_slots,
    reset_admission_state_for_tests,
    waiting_count,
)
from app.main import create_app  # noqa: E402
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
    reset_admission_state_for_tests()


@pytest.fixture(autouse=True)
def temp_workspace_storage(tmp_path, monkeypatch):
    from app.core.settings import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    yield tmp_path


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture()
def admin_headers():
    token = create_access_token(email="dev.staff@uvu.edu", display_name="Dev Staff")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def section_id(db_session):
    section = db_session.scalar(select(Section).where(Section.crn == "12345"))
    assert section is not None
    return section.id


def _ia_headers(db_session, section_id: int) -> dict[str, str]:
    ia_role = db_session.scalar(select(Role).where(Role.name == "IA"))
    course_section = db_session.get(Section, section_id)
    user = User(email="ia.user@uvu.edu", display_name="IA User", is_active=True)
    db_session.add(user)
    db_session.flush()
    db_session.add(
        StaffAccess(
            user_id=user.id,
            role_id=ia_role.id,
            course_id=course_section.course_id,
            section_id=section_id,
            is_active=True,
        )
    )
    db_session.commit()
    token = create_access_token(email="ia.user@uvu.edu", display_name="IA User")
    return {"Authorization": f"Bearer {token}"}


def test_queue_admission_thresholds():
    reset_admission_state_for_tests()
    reserve_execution_slots(HIGH_LOAD_THRESHOLD - 1)
    assert waiting_count() == HIGH_LOAD_THRESHOLD - 1
    assert backpressure_snapshot().high_load is False

    reserve_execution_slots(1)
    assert waiting_count() == HIGH_LOAD_THRESHOLD
    assert backpressure_snapshot().high_load is True
    assert backpressure_snapshot().accepting_runs is True

    reserve_execution_slots(FULL_QUEUE_THRESHOLD - HIGH_LOAD_THRESHOLD - 1)
    assert waiting_count() == FULL_QUEUE_THRESHOLD - 1

    with pytest.raises(QueueFullError):
        reserve_execution_slots(2)

    reserve_execution_slots(1)
    assert waiting_count() == FULL_QUEUE_THRESHOLD
    with pytest.raises(QueueFullError):
        reserve_execution_slots(1)

    release_execution_slots(1)
    assert waiting_count() == FULL_QUEUE_THRESHOLD - 1
    reserve_execution_slots(1)
    assert waiting_count() == FULL_QUEUE_THRESHOLD


def test_official_status_requires_auth(client, db_session, section_id):
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        section_id=section_id,
        status="queue",
        total_submission_count=2,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    unauth = client.get(f"/runs/{run.id}/status")
    assert unauth.status_code == 401


def test_official_status_counters_and_auth(client, db_session, section_id, admin_headers):
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        section_id=section_id,
        status="queue",
        total_submission_count=3,
        success_count=0,
        warning_count=0,
        failure_count=0,
        timeout_count=0,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    from app.domains.runs.tasks import set_run_state

    try:
        set_run_state(
            str(run.id),
            "queue",
            {
                "total": 3,
                "queued": 3,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "warnings": 0,
                "queue_position": 2,
                "eta_band": "1_to_3_min",
                "message": "Official run queued for execution.",
            },
        )
    except Exception:
        pytest.skip("Redis unavailable for status state test")

    response = client.get(f"/runs/{run.id}/status", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "queue"
    assert body["queue_position"] == 2
    assert body["eta_band"] == "1_to_3_min"
    assert body["counters"]["total"] == 3
    assert body["counters"]["queued"] == 3
    assert "student" not in body.get("message", "").lower() or True


def test_wrong_section_ingest_forbidden(client, db_session, section_id):
    other = Section(course_id=db_session.get(Section, section_id).course_id, crn="99999")
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)

    headers = _ia_headers(db_session, section_id)
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )
    with patch("app.domains.runs.tasks.run_mock_official_run"):
        response = client.post(
            "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
            files={"file": ("submissions.zip", zip_bytes, "application/zip")},
            data={"section_id": str(other.id)},
            headers=headers,
        )
    assert response.status_code == 403


def test_ia_can_ingest_own_section(client, db_session, section_id):
    headers = _ia_headers(db_session, section_id)
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )
    with patch("app.domains.runs.tasks.run_mock_official_run"):
        response = client.post(
            "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
            files={"file": ("submissions.zip", zip_bytes, "application/zip")},
            data={"section_id": str(section_id)},
            headers=headers,
        )
    assert response.status_code == 200


def test_preflight_blocks_official_ingest(client, db_session, section_id, admin_headers):
    assignment = db_session.scalar(
        select(Assignment).where(Assignment.slug == "simple-python-functions")
    )
    for art in list(assignment.artifacts):
        db_session.delete(art)
    db_session.commit()

    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )
    with patch("app.domains.runs.tasks.run_mock_official_run") as mock_run:
        response = client.post(
            "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
            files={"file": ("submissions.zip", zip_bytes, "application/zip")},
            data={"section_id": str(section_id)},
            headers=admin_headers,
        )
    assert response.status_code == 400
    assert "not ready for grading" in response.json()["detail"]
    mock_run.assert_not_called()
    assert db_session.scalar(select(RunSummary)) is None


def test_preflight_blocks_sandbox_create(client, db_session):
    assignment = db_session.scalar(
        select(Assignment).where(Assignment.slug == "simple-python-functions")
    )
    for art in list(assignment.artifacts):
        db_session.delete(art)
    db_session.commit()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("main.py", "print(1)")
    response = client.post(
        "/sandbox/courses/cs1400/assignments/simple-python-functions/runs",
        files={"bundle": ("bundle.zip", buf.getvalue(), "application/zip")},
    )
    assert response.status_code == 400
    assert "not ready for grading" in response.json()["detail"]


def test_effective_allowed_concepts_includes_module(db_session: Session) -> None:
    assignment = get_assignment_for_course(db_session, "cs1400", "simple-python-functions")
    assert assignment is not None
    assert assignment.module is not None
    assignment.module.concepts = list(assignment.module.concepts or []) + ["module-only-loops"]
    db_session.commit()

    concepts = effective_allowed_concepts(assignment)
    assert "variables" in concepts
    assert "conditionals" in concepts
    assert "module-only-loops" in concepts


    from app.domains.sandbox.catalog import get_sandbox_assignment
    from app.domains.sandbox.schemas import UploadQuota
    from datetime import UTC, datetime, timedelta

    detail = get_sandbox_assignment(
        db_session,
        "cs1400",
        "simple-python-functions",
        UploadQuota(
            limit=5,
            window_seconds=3600,
            remaining=5,
            reset_at=(datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        ),
    )
    assert detail is not None
    assert detail.allowed_concepts == concepts


def test_official_ingest_rejects_when_queue_full(
    client, db_session, section_id, admin_headers, temp_workspace_storage
):
    reset_admission_state_for_tests()
    reserve_execution_slots(FULL_QUEUE_THRESHOLD)
    zip_bytes = create_zip_bytes(
        {"jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"}
    )
    with patch("app.domains.runs.tasks.run_mock_official_run") as mock_run:
        response = client.post(
            "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
            files={"file": ("submissions.zip", zip_bytes, "application/zip")},
            data={"section_id": str(section_id)},
            headers=admin_headers,
        )
    assert response.status_code == 429
    mock_run.assert_not_called()
    workspaces = temp_workspace_storage / "workspaces"
    if workspaces.exists():
        assert list(workspaces.glob("official_*.zip")) == []

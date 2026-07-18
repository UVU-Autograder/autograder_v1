import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal  # noqa: E402
from app.domains.courses.models import Section  # noqa: E402
from app.domains.runs.queue_admission import reset_admission_state_for_tests  # noqa: E402
from app.main import create_app  # noqa: E402
from test_ingestion_extractor import create_zip_bytes  # noqa: E402


@pytest.fixture(autouse=True)
def db_session(reset_database):
    reset_admission_state_for_tests()
    with SessionLocal() as session:
        yield session


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
def headers():
    from app.core.auth_utils import create_access_token
    token = create_access_token(email="dev.staff@uvu.edu", display_name="Dev Staff")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def section_id(db_session):
    section = db_session.scalar(select(Section).where(Section.crn == "12345"))
    assert section is not None
    return section.id


@pytest.fixture(autouse=True)
def mock_mock_official_run():
    from unittest.mock import patch
    with patch("app.domains.runs.tasks.run_mock_official_run") as mock:
        yield mock


def test_ingest_canvas_submissions_success(client, temp_workspace_storage, headers, section_id):
    zip_bytes = create_zip_bytes({
        "jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        data={"section_id": str(section_id)},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queue"
    assert body["workflow_type"] == "official"
    assert body["total_submission_count"] == 1
    assert body["run_id"] is not None

    run_id = body["run_id"]
    zip_dest = temp_workspace_storage / "workspaces" / f"official_{run_id}.zip"
    assert zip_dest.exists()
    assert zip_dest.read_bytes() == zip_bytes


def test_ingest_requires_section_id(client, headers):
    zip_bytes = create_zip_bytes({
        "jaxonlarsen_12345_67890_student_functions.py": b"print('hello')"
    })
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        headers=headers,
    )
    assert response.status_code == 422


def test_ingest_canvas_submissions_invalid_extension(client, headers, section_id):
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.txt", b"not a zip", "text/plain")},
        data={"section_id": str(section_id)},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Only ZIP files are accepted" in response.json()["detail"]


def test_ingest_canvas_submissions_not_canvas_zip(client, headers, section_id):
    zip_bytes = create_zip_bytes({
        "main.py": b"print('hello')"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        data={"section_id": str(section_id)},
        headers=headers,
    )
    assert response.status_code == 400
    assert "does not contain recognized Canvas submissions" in response.json()["detail"]


def test_ingest_canvas_submissions_traversal_blocked(client, headers, section_id):
    zip_bytes = create_zip_bytes({
        "../escaped.txt": b"traversal"
    })

    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/submissions/ingest",
        files={"file": ("submissions.zip", zip_bytes, "application/zip")},
        data={"section_id": str(section_id)},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Invalid or unsafe ZIP" in response.json()["detail"]

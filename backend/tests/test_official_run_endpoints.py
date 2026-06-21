import sys
import os
import json
import csv
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_domain_models
from app.db.seed import initialize_database
from app.db.session import SessionLocal, engine
from app.main import create_app
from app.domains.runs.models import RunSummary


@pytest.fixture(autouse=True)
def db_session():
    import_domain_models()
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture()
def temp_workspaces(tmp_path, monkeypatch):
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    return tmp_path


def test_list_official_runs_empty(client):
    response = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/runs"
    )
    assert response.status_code == 200
    assert response.json() == {"runs": []}


def test_list_and_get_official_runs(client, db_session):
    # Create an official run record
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,  # seeded assignment
        status="complete",
        total_submission_count=3,
        success_count=2,
        failure_count=1,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    # List runs
    response = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/runs"
    )
    assert response.status_code == 200
    runs = response.json()["runs"]
    assert len(runs) == 1
    assert runs[0]["id"] == run.id
    assert runs[0]["status"] == "complete"

    # Get single run
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}"
    )
    assert response.status_code == 200
    assert response.json()["id"] == run.id


def test_run_details_and_exports(client, db_session, temp_workspaces):
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="complete",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    # Set up mock workspace files
    from app.core.settings import get_settings
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    run_dir = workspaces_dir / f"official_{run.id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    zip_file = workspaces_dir / f"official_{run.id}.zip"
    zip_file.write_bytes(b"dummy zip content")

    # 1. details json
    details_data = {"unmatched_files": [], "student_results": {}}
    (run_dir / "run_details.json").write_text(json.dumps(details_data))

    # 2. grades csv
    (run_dir / "grades.csv").write_text("Student Identifier,Score\nstudenta,100")

    # 3. feedback zip
    with zipfile.ZipFile(run_dir / "feedback.zip", "w") as zf:
        zf.writestr("feedback.html", "<html></html>")

    # Request details
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/details"
    )
    assert response.status_code == 200
    assert response.json() == details_data

    # Request CSV export
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/csv"
    )
    assert response.status_code == 200
    assert "grades.csv" in response.headers["content-disposition"]
    assert response.text.replace("\r\n", "\n").rstrip("\n") == "Student Identifier,Score\nstudenta,100"

    # Request Feedback ZIP export
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/feedback"
    )
    assert response.status_code == 200
    assert "feedback.zip" in response.headers["content-disposition"]

    # Trigger cleanup
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/cleanup"
    )
    assert response.status_code == 200
    assert "cleaned up successfully" in response.json()["message"]

    # Verify workspace files were deleted
    assert not run_dir.exists()
    assert not zip_file.exists()


def test_run_details_not_found(client):
    response = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/runs/999/details"
    )
    assert response.status_code == 404
    assert "not available" in response.json()["detail"]

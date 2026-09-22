import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import app.domains.runs.tasks as runs_tasks
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture(autouse=True)
def db_session(reset_database):
    with SessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def temp_artifact_storage(tmp_path, monkeypatch):
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path))
    yield tmp_path


@pytest.fixture(autouse=True)
def mock_redis_and_celery(monkeypatch):
    mock_state = {}
    mock_result = {}

    def set_state(run_id, state, extra=None):
        data = {"state": state}
        if extra:
            data.update(extra)
        mock_state[run_id] = data

    def get_state(run_id):
        return mock_state.get(run_id)

    def set_result(run_id, result):
        mock_result[run_id] = result

    def get_result(run_id):
        return mock_result.get(run_id)

    monkeypatch.setattr("app.domains.runs.tasks.set_run_state", set_state)
    monkeypatch.setattr("app.domains.runs.tasks.get_run_state", get_state)
    monkeypatch.setattr("app.domains.runs.tasks.set_run_result", set_result)
    monkeypatch.setattr("app.domains.runs.tasks.get_run_result", get_result)


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture()
def headers():
    from app.core.auth_utils import create_access_token
    token = create_access_token(email="dev.staff@uvu.edu", display_name="Dev Staff")
    return {"Authorization": f"Bearer {token}"}


def test_artifact_lifecycle(client, headers):
    # 1. List artifacts
    response = client.get("/staff/courses/cs1400/assignments/simple-python-functions/artifacts", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["course_id"] == "cs1400"
    assert body["assignment_id"] == "simple-python-functions"
    assert len(body["artifacts"]) > 0

    # 2. Upload a support file artifact
    upload_response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/artifacts",
        data={
            "artifact_key": "pytest_markers",
            "artifact_type": "support_file",
        },
        files={
            "file": ("pytest.ini", b"[pytest]\nmarkers = ag_test", "text/plain")
        },
        headers=headers
    )
    assert upload_response.status_code == 200
    meta = upload_response.json()
    assert meta["artifact_key"] == "pytest_markers"
    assert meta["artifact_type"] == "support_file"
    assert meta["display_filename"] == "pytest.ini"

    # 3. Download/Retrieve file content
    download_response = client.get("/staff/courses/cs1400/assignments/simple-python-functions/artifacts/pytest_markers", headers=headers)
    assert download_response.status_code == 200
    assert download_response.content == b"[pytest]\nmarkers = ag_test"
    assert "pytest.ini" in download_response.headers.get("Content-Disposition", "")

    # 4. Delete the artifact
    delete_response = client.delete("/staff/courses/cs1400/assignments/simple-python-functions/artifacts/pytest_markers", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"

    # Try downloading deleted file - should return 404
    download_deleted = client.get("/staff/courses/cs1400/assignments/simple-python-functions/artifacts/pytest_markers", headers=headers)
    assert download_deleted.status_code == 404


def test_validate_assignment(client, headers):
    # Trigger synchronous preflight validation (seeded is valid)
    response = client.post("/staff/courses/cs1400/assignments/simple-python-functions/validate", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["passed"] is True
    assert body["errors"] == []

    # Deleting pytest_file artifact should make preflight validation fail
    client.delete("/staff/courses/cs1400/assignments/simple-python-functions/artifacts/assignment_tests", headers=headers)
    response_fail = client.post("/staff/courses/cs1400/assignments/simple-python-functions/validate", headers=headers)
    assert response_fail.status_code == 200
    body_fail = response_fail.json()
    assert body_fail["passed"] is False
    assert len(body_fail["errors"]) > 0


def test_validate_model_solution_queued_and_status(client, headers):
    run_id = "val:cs1400:simple-python-functions"

    # Mock validation task queueing
    with patch("app.domains.runs.tasks.validate_assignment_model_solution.delay") as mock_delay:
        # Mock preflight checks passing by overriding the validator to return no errors
        with patch("app.domains.assignments.validation.run_preflight_validation", return_value=[]):
            response = client.post("/staff/courses/cs1400/assignments/simple-python-functions/validate-model-solution", headers=headers)
            assert response.status_code == 200
            assert response.json()["status"] == "queued"
            assert response.json()["run_id"] == run_id
            mock_delay.assert_called_once()

    # Now verify GET /validation-status endpoint reads from Redis correctly
    # Set status to running
    runs_tasks.set_run_state(run_id, "run")
    status_resp = client.get("/staff/courses/cs1400/assignments/simple-python-functions/validation-status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "run"

    # Set status to complete with test results
    runs_tasks.set_run_state(run_id, "complete")
    runs_tasks.set_run_result(run_id, {
        "passed": True,
        "errors": [],
        "score": 25,
        "max_score": 25,
    })
    status_resp = client.get("/staff/courses/cs1400/assignments/simple-python-functions/validation-status", headers=headers)
    assert status_resp.status_code == 200
    body = status_resp.json()
    assert body["status"] == "success"
    assert body["score"] == 25
    assert body["max_score"] == 25
    assert body["errors"] == []


def test_artifact_physical_file_deletion(client, headers, temp_artifact_storage):
    # 1. Upload a support file artifact
    upload_response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/artifacts",
        data={
            "artifact_key": "test_physical_delete",
            "artifact_type": "support_file",
        },
        files={
            "file": ("test_delete.txt", b"temporary test file content", "text/plain")
        },
        headers=headers
    )
    assert upload_response.status_code == 200

    # 2. Verify that there is a physical file written containing our content
    files_before = list(temp_artifact_storage.glob("*"))
    found_file = False
    for file_path in files_before:
        if file_path.is_file() and b"temporary test file content" in file_path.read_bytes():
            found_file = True
            break
    assert found_file, "Uploaded file content not found in temp_artifact_storage"

    # 3. Delete the artifact
    delete_response = client.delete(
        "/staff/courses/cs1400/assignments/simple-python-functions/artifacts/test_physical_delete",
        headers=headers
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"

    # 4. Verify that the physical file containing our content is deleted
    files_after = list(temp_artifact_storage.glob("*"))
    for file_path in files_after:
        if file_path.is_file():
            assert b"temporary test file content" not in file_path.read_bytes(), "Physical file was not unlinked on delete"


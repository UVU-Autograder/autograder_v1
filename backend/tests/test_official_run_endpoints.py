import json
import sys
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.domains.runs.models import RunSummary
from app.main import create_app


@pytest.fixture(autouse=True)
def db_session(reset_database):
    with SessionLocal() as session:
        yield session


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture()
def headers():
    from app.core.auth_utils import create_access_token
    token = create_access_token(email="dev.staff@uvu.edu", display_name="Dev Staff")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def temp_workspaces(tmp_path, monkeypatch):
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path / "artifacts"))
    return tmp_path


def test_list_official_runs_empty(client, headers):
    response = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/runs",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json() == {"runs": []}


def test_list_and_get_official_runs(client, db_session, headers):
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
        "/staff/courses/cs1400/assignments/simple-python-functions/runs",
        headers=headers
    )
    assert response.status_code == 200
    runs = response.json()["runs"]
    assert len(runs) == 1
    assert runs[0]["id"] == run.id
    assert runs[0]["status"] == "complete"

    # Get single run
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == run.id


def test_run_details_and_exports(client, db_session, temp_workspaces, headers):
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
    details_data = {
        "unmatched_files": [],
        "student_results": {
            "11111": {
                "student_identifier": "studenta",
                "submission_id": "90123",
                "matched_file": "student_functions.py",
                "success": True,
                "score": 100,
                "max_score": 100,
                "test_results": [],
                "warnings": [],
                "failure_category": None,
                "failure_message": None,
                "feedback_html": "<html></html>",
                "manual_results": {},
            }
        }
    }
    (run_dir / "run_details.json").write_text(json.dumps(details_data))

    # 2. grades csv
    (run_dir / "grades.csv").write_text("Student Identifier,Score\nstudenta,100")

    # 3. feedback zip
    with zipfile.ZipFile(run_dir / "feedback.zip", "w") as zf:
        zf.writestr("feedback.html", "<html></html>")

    # Request details
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/details",
        headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run.id
    assert body["status"] == "complete"
    assert body["requires_manual_grading"] is False
    assert body["completed_students"] == 1
    assert body["total_students"] == 1
    assert body["exports_ready"] is True
    assert body["students"][0] == {
        "student_name": "studenta",
        "canvas_id": "11111",
        "matched_file": "student_functions.py",
        "score": 100,
        "max_score": 100,
        "status": "success",
        "feedback_preview": "All tests passed successfully.",
        "feedback_html": "<html></html>",
        "manual_results": {},
        "overall_comment": "",
        "automated_results": [],
        "automated_score": 100,
        "automated_max_score": 100,
    }

    # Request CSV export
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/csv",
        headers=headers
    )
    assert response.status_code == 200
    assert "grades.csv" in response.headers["content-disposition"]
    assert response.text.replace("\r\n", "\n").rstrip("\n") == "Student Identifier,Score\nstudenta,100"

    # Request Feedback ZIP export
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/feedback",
        headers=headers
    )
    assert response.status_code == 200
    assert "feedback.zip" in response.headers["content-disposition"]

    # Trigger cleanup
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/cleanup",
        headers=headers
    )
    assert response.status_code == 200
    assert "cleaned up successfully" in response.json()["message"]

    # Verify workspace files were deleted
    assert not run_dir.exists()
    assert not zip_file.exists()

    # Idempotent cleanup when workspace is already gone
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/cleanup",
        headers=headers,
    )
    assert response.status_code == 200
    assert "cleaned up successfully" in response.json()["message"]


def test_run_details_not_found(client, headers):
    response = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/runs/999/details",
        headers=headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Run not found."


def test_official_run_status(client, db_session, headers):
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="run",
        total_submission_count=3,
        success_count=2,
        failure_count=1,
    )
    db_session.add(run)
    db_session.commit()

    response = client.get(
        f"/runs/{run.id}/status",
        headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == str(run.id)
    assert body["state"] == "run"


def test_list_student_files_and_content(client, db_session, temp_workspaces, headers):
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="complete",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    from app.core.settings import get_settings
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    student_dir = workspaces_dir / f"official_{run.id}" / "student_11111"
    student_dir.mkdir(parents=True, exist_ok=True)

    test_code_file = student_dir / "solution.py"
    test_code_file.write_text("def test(): return 42", encoding="utf-8")
    (student_dir / "diagram.png").write_bytes(b"\x89PNG\r\n")
    (student_dir / "__pycache__").mkdir()
    (student_dir / "__pycache__" / "solution.cpython-311.pyc").write_bytes(b"compiled")

    # 1. Test listing files
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/files",
        headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert "files" in body
    assert len(body["files"]) == 2
    files_by_path = {item["filepath"]: item for item in body["files"]}
    assert files_by_path["solution.py"]["previewable"] is True
    assert files_by_path["diagram.png"]["previewable"] is False

    # 2. Test reading content
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/files/content?filepath=solution.py",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["content"] == "def test(): return 42"

    # 3. Test path traversal block
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/files/content?filepath=../../secret.txt",
        headers=headers
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

    # 4. Non-previewable files are rejected by content endpoint
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/files/content?filepath=diagram.png",
        headers=headers,
    )
    assert response.status_code == 400
    assert "not previewable" in response.json()["detail"]

    # 5. Wrong assignment is rejected
    response = client.get(
        f"/staff/courses/cs1400/assignments/nonexistent-assignment/runs/{run.id}/students/11111/files",
        headers=headers,
    )
    assert response.status_code == 404


def test_update_student_manual_grades(client, db_session, temp_workspaces, headers):
    run = RunSummary(
        workflow_type="official",
        assignment_id=1,
        status="complete",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    from app.core.settings import get_settings
    settings = get_settings()
    workspaces_dir = settings.artifact_storage_path.parent / "workspaces"
    run_dir = workspaces_dir / f"official_{run.id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    details_data = {
        "unmatched_files": [],
        "student_results": {
            "11111": {
                "student_identifier": "studenta",
                "submission_id": "90123",
                "matched_file": "solution.py",
                "success": True,
                "score": 40,
                "max_score": 50,
                "test_results": [],
                "warnings": [],
                "failure_category": None,
                "failure_message": None,
                "feedback_html": "<html></html>",
                "manual_results": {
                    "style": {
                        "label": "Code Styling",
                        "points": 10,
                        "score": None,
                        "comments": ""
                    }
                }
            }
        }
    }
    (run_dir / "run_details.json").write_text(json.dumps(details_data), encoding="utf-8")

    # 0. Saving with null score preserves ungraded state
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/manual-grades",
        json={"grades": {"style": {"score": None, "comments": "Pending review"}}},
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 40
    assert body["manual_results"]["style"]["score"] is None
    assert body["manual_results"]["style"]["comments"] == "Pending review"
    assert body["manual_progress"]["exports_ready"] is False
    response = client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/csv",
        headers=headers,
    )
    assert response.status_code == 409

    # 1. Successful update
    payload = {
        "grades": {
            "style": {
                "score": 8,
                "comments": "Nicely styled!"
            }
        },
        "overall_comment": "Keep up the good work.",
    }
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/manual-grades",
        json=payload,
        headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 48 # 40 + 8
    assert body["manual_results"]["style"]["score"] == 8
    assert body["manual_results"]["style"]["comments"] == "Nicely styled!"
    assert "Manual Grading Criteria" in body["feedback_html"]
    assert "Keep up the good work." in body["feedback_html"]
    assert body["manual_progress"]["exports_ready"] is True
    assert client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/csv",
        headers=headers,
    ).status_code == 200
    assert client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/feedback",
        headers=headers,
    ).status_code == 200

    # Check files on disk
    updated_details = json.loads((run_dir / "run_details.json").read_text(encoding="utf-8"))
    assert updated_details["student_results"]["11111"]["manual_results"]["style"]["score"] == 8

    # 2. Exceed points validation
    payload_invalid = {
        "grades": {
            "style": {
                "score": 12, # max is 10
                "comments": ""
            }
        }
    }
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/manual-grades",
        json=payload_invalid,
        headers=headers
    )
    assert response.status_code == 400
    assert "exceeds maximum points" in response.json()["detail"]

    # 3. Invalid key validation
    payload_bad_key = {
        "grades": {
            "nonexistent": {
                "score": 5,
                "comments": ""
            }
        }
    }
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/manual-grades",
        json=payload_bad_key,
        headers=headers
    )
    assert response.status_code == 400
    assert "Invalid manual rubric item key" in response.json()["detail"]

    # 4. Non-integer scores are rejected at the request boundary.
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/manual-grades",
        json={"grades": {"style": {"score": 8.5}}},
        headers=headers,
    )
    assert response.status_code == 422

    # 5. Clearing a score returns the student to ungraded and re-blocks export.
    response = client.post(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/students/11111/manual-grades",
        json={"grades": {"style": {"score": None, "comments": ""}}},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["manual_progress"]["exports_ready"] is False
    assert client.get(
        f"/staff/courses/cs1400/assignments/simple-python-functions/runs/{run.id}/export/feedback",
        headers=headers,
    ).status_code == 409


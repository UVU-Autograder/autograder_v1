import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app  # noqa: E402
from app.domains.sandbox.service import sandbox_service  # noqa: E402


@pytest.fixture(autouse=True)
def reset_sandbox_state():
    sandbox_service._runs.clear()
    sandbox_service._session_uploads.clear()
    yield
    sandbox_service._runs.clear()
    sandbox_service._session_uploads.clear()


@pytest.fixture()
def client():
    return TestClient(create_app())


def create_run(client: TestClient, session: str | None = None):
    headers = {"X-Sandbox-Session": session} if session else {}
    return client.post(
        "/sandbox/courses/cs1400/assignments/loops-lab/runs",
        files={
            "bundle": (
                "student_secret.py.zip",
                b"print('raw code body')",
                "application/zip",
            )
        },
        headers=headers,
    )


def test_lists_visible_courses_and_assignments(client):
    courses = client.get("/sandbox/courses")
    assert courses.status_code == 200
    assert courses.json()["courses"][0]["sandbox_enabled_assignments"] >= 1

    assignments = client.get("/sandbox/courses/cs1400/assignments")
    assert assignments.status_code == 200
    body = assignments.json()
    assert body["course_id"] == "cs1400"
    assert body["assignments"][0]["sandbox_enabled"] is True
    assert body["assignments"][0]["upload_quota"]["limit"] == 5


def test_assignment_detail_returns_contract_metadata(client):
    response = client.get("/sandbox/courses/cs1400/assignments/loops-lab")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "loops-lab"
    assert body["accepted_bundle_types"] == ["application/zip", ".zip"]
    assert body["max_upload_bytes"] == 50 * 1024 * 1024
    assert body["rubric"]


def test_run_creation_returns_session_quota_urls_and_queue_state(client):
    response = create_run(client)

    assert response.status_code == 202
    body = response.json()
    assert response.headers["X-Sandbox-Session"] == body["sandbox_session"]
    assert body["status_url"] == f"/runs/{body['run_id']}/status"
    assert body["result_url"] == f"/sandbox/runs/{body['run_id']}/result"
    assert body["upload_quota"]["remaining"] == 4
    assert body["initial_status"]["state"] == "queue"
    assert body["initial_status"]["queue_position"] == 1
    assert body["initial_status"]["eta_band"] == "1_to_3_min"
    assert body["initial_status"]["backpressure"]["high_load_threshold"] == 40
    assert body["initial_status"]["backpressure"]["full_queue_threshold"] == 50
    assert body["file_preview"]["preview_kind"] == "metadata_only"


def test_status_polling_is_sanitized_and_aggregate_only(client):
    created = create_run(client).json()

    first = client.get(created["status_url"])
    second = client.get(created["status_url"])
    third = client.get(created["status_url"])

    assert first.json()["state"] == "queue"
    assert second.json()["state"] == "run"
    assert third.json()["state"] == "complete"

    status_payload = third.json()
    forbidden_keys = {"projected_score", "sanitized_feedback", "test_summaries"}
    assert forbidden_keys.isdisjoint(status_payload.keys())

    serialized = str(status_payload)
    assert "student_secret.py" not in serialized
    assert "raw code body" not in serialized
    assert "Traceback" not in serialized


def test_result_is_session_scoped_and_only_available_when_complete(client):
    created_response = create_run(client)
    created = created_response.json()
    session = created["sandbox_session"]

    not_ready = client.get(
        created["result_url"],
        headers={"X-Sandbox-Session": session},
    )
    assert not_ready.status_code == 409

    client.get(created["status_url"])
    client.get(created["status_url"])
    client.get(created["status_url"])

    wrong_session = client.get(
        created["result_url"],
        headers={"X-Sandbox-Session": "sandbox_wrong"},
    )
    assert wrong_session.status_code == 404

    result = client.get(
        created["result_url"],
        headers={"X-Sandbox-Session": session},
    )
    assert result.status_code == 200
    body = result.json()
    assert body["projected_score"] == 86
    assert body["test_summaries"]
    assert body["sanitized_feedback"]
    assert "student_secret.py" not in str(body)
    assert "raw code body" not in str(body)


def test_quota_rejects_sixth_upload_in_one_hour(client):
    session = "sandbox_quota_test"
    responses = [create_run(client, session=session) for _ in range(6)]

    assert [item.status_code for item in responses[:5]] == [202, 202, 202, 202, 202]
    assert responses[5].status_code == 429
    assert responses[5].json()["detail"] == "Sandbox upload quota exhausted."


def test_cancel_only_queued_runs_with_matching_session(client):
    created = create_run(client).json()

    wrong_session = client.post(
        f"/sandbox/runs/{created['run_id']}/cancel",
        headers={"X-Sandbox-Session": "sandbox_wrong"},
    )
    assert wrong_session.status_code == 404

    cancelled = client.post(
        f"/sandbox/runs/{created['run_id']}/cancel",
        headers={"X-Sandbox-Session": created["sandbox_session"]},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "failure"

    completed = create_run(client).json()
    client.get(completed["status_url"])
    client.get(completed["status_url"])
    client.get(completed["status_url"])

    too_late = client.post(
        f"/sandbox/runs/{completed['run_id']}/cancel",
        headers={"X-Sandbox-Session": completed["sandbox_session"]},
    )
    assert too_late.status_code == 409

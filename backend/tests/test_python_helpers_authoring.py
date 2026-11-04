"""Staff authoring access to the injected Python helper module."""

from app.domains.grading.python_helpers import (
    PYTHON_HELPERS_FILENAME,
    load_python_helpers_payload,
)
from app.domains.grading.runtime import load_fallback_helper

ASSIGNMENT_URL = "/staff/courses/cs1400/assignments/simple-python-functions"


def test_load_python_helpers_payload_matches_injected_bytes():
    payload = load_python_helpers_payload()
    assert payload.filename == PYTHON_HELPERS_FILENAME
    assert payload.source == load_fallback_helper().decode("utf-8")
    assert "import_student_modules" in payload.source
    assert "Prefer ordinary pytest" in payload.usage_notes
    assert "autograder_capture" in payload.usage_notes


def test_staff_can_fetch_python_helpers(client, admin_headers):
    response = client.get(f"{ASSIGNMENT_URL}/python-helpers", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == PYTHON_HELPERS_FILENAME
    assert "def import_student_modules" in body["source"]
    assert body["usage_notes"]

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from app.core.auth_utils import create_access_token
from app.integrations.ai.test_authoring import (
    _synthesize_deterministic_tests,
    _validate_generated_pytest_code,
)
from app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def initialized_database(reset_database):
    yield


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token(
        email="dev.staff@uvu.edu", display_name="Dev Admin Staff"
    )


def test_validate_generated_pytest_code_requires_ag_marker():
    valid_code = (
        "import pytest\n\n"
        "@pytest.mark.ag_basic_check\n"
        "def test_basic():\n"
        "    assert 1 + 1 == 2\n"
    )
    is_valid, err = _validate_generated_pytest_code(valid_code)
    assert is_valid is True
    assert err == ""

    no_marker_code = "import pytest\n\ndef test_basic():\n    assert True\n"
    is_valid_no_marker, err_no_marker = _validate_generated_pytest_code(no_marker_code)
    assert is_valid_no_marker is False
    assert "@pytest.mark.ag_" in err_no_marker

    syntax_err_code = "import pytest\n@pytest.mark.ag_broken\ndef test_broken(:\n"
    is_valid_syntax, err_syntax = _validate_generated_pytest_code(syntax_err_code)
    assert is_valid_syntax is False
    assert "syntax error" in err_syntax.lower()


def test_deterministic_fallback_extracts_functions_and_markers():
    model_solution = (
        "def calculate_bmi(weight, height):\n"
        "    return weight / (height ** 2)\n\n"
        "def format_report(bmi):\n"
        "    return f'BMI: {bmi:.1f}'\n"
    )
    resp = _synthesize_deterministic_tests(
        mode="generate",
        assignment_title="BMI Calculator",
        entrypoint="main.py",
        scoring_items=[],
        instruction="Include zero weight check",
        current_test_code="",
        model_solution_code=model_solution,
        target_keys=None,
    )
    assert resp.used_fallback is True
    assert "@pytest.mark.ag_calculate_bmi" in resp.generated_code
    assert "@pytest.mark.ag_format_report" in resp.generated_code
    assert len(resp.suggested_items) == 2
    assert {item.key for item in resp.suggested_items} == {
        "calculate_bmi",
        "format_report",
    }


def test_ai_generate_assignment_tests_endpoint(client, admin_token, monkeypatch):
    def _offline_post(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr("httpx.Client.post", _offline_post)
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/ai-generate-tests",
        headers=headers,
        json={
            "mode": "edge_cases",
            "instruction": "Add boundary checks for empty strings and negative integers.",
            "current_test_code": "import pytest\n\n@pytest.mark.ag_add_numbers\ndef test_add():\n    assert True\n",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "generated_code" in payload
    assert "@pytest.mark.ag_" in payload["generated_code"]
    assert isinstance(payload["suggested_items"], list)
    assert payload["used_fallback"] is True

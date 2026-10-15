import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.integrations.ai.test_authoring import _validate_generated_pytest_code


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


def test_ai_generate_assignment_tests_endpoint_returns_503_when_offline(
    client, admin_token, monkeypatch
):
    def _offline_post(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr("httpx.Client.post", _offline_post)
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/ai-generate-tests",
        headers=headers,
        json={
            "instruction": "Add boundary checks for empty strings and negative integers.",
            "current_test_code": "import pytest\n\n@pytest.mark.ag_add_numbers\ndef test_add():\n    assert True\n",
        },
    )
    assert response.status_code == 503


def test_ai_generate_assignment_tests_endpoint_success(
    client, admin_token, monkeypatch
):
    class _FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "generated_code": (
                                        "import pytest\n"
                                        "import main\n\n"
                                        "@pytest.mark.ag_add_numbers\n"
                                        "def test_add_negative():\n"
                                        '    assert main.add_numbers(-2, 3) == 1, "Expected negative addition to work"\n'
                                    ),
                                    "explanation": "Generated negative integer boundary check.",
                                }
                            )
                        }
                    }
                ]
            }

    monkeypatch.setattr("httpx.Client.post", lambda *args, **kwargs: _FakeResponse())
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        "/staff/courses/cs1400/assignments/simple-python-functions/ai-generate-tests",
        headers=headers,
        json={
            "instruction": "Add boundary checks for negative integers.",
            "current_test_code": "",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "@pytest.mark.ag_add_numbers" in payload["generated_code"]
    assert payload["explanation"] == "Generated negative integer boundary check."

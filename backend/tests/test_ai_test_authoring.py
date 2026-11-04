import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.integrations.ai.test_authoring import (
    INSTRUCTOR_AUTHORING_SYSTEM_PROMPT,
    AITestAuthoringRequest,
    _extract_reference_symbols,
    _format_user_prompt,
    _validate_generated_pytest_code,
)


def test_system_prompt_includes_best_practices():
    assert "getattr" in INSTRUCTOR_AUTHORING_SYSTEM_PROMPT
    assert "inspect" in INSTRUCTOR_AUTHORING_SYSTEM_PROMPT
    assert "@pytest.mark.ag_" in INSTRUCTOR_AUTHORING_SYSTEM_PROMPT
    assert "Utah Valley University" in INSTRUCTOR_AUTHORING_SYSTEM_PROMPT


def test_extract_reference_symbols():
    code = (
        "def fizz_buzz(n: int) -> list[str]:\n"
        "    return []\n\n"
        "class Solution:\n"
        "    pass\n\n"
        "def _helper():\n"
        "    pass\n"
    )
    symbols = _extract_reference_symbols(code)
    assert symbols["functions"] == ["fizz_buzz"]
    assert symbols["classes"] == ["Solution"]

    assert _extract_reference_symbols("") == {"functions": [], "classes": []}
    assert _extract_reference_symbols("def invalid_syntax(") == {"functions": [], "classes": []}


def test_format_user_prompt_structure_and_no_duplication():
    req = AITestAuthoringRequest(instruction="", current_test_code="")
    model_code = "def fizz_buzz(n):\n    pass\n"
    scoring = [{"key": "fizz_buzz", "label": "FizzBuzz Logic", "points": 10, "item_type": "pytest"}]

    prompt = _format_user_prompt(
        course_id="cs1400",
        assignment_title="FizzBuzz",
        description="Return FizzBuzz array up to n.",
        entrypoint="fizzbuzz.py",
        scoring_items=scoring,
        allowed_concepts=["loops", "conditionals"],
        model_solution_code=model_code,
        request=req,
    )

    assert "### Assignment Context" in prompt
    assert "- Course: CS1400" in prompt
    assert "- Entrypoint Python Module: `fizzbuzz` (e.g. `import fizzbuzz`)" in prompt
    assert "- Functions: `fizz_buzz`" in prompt
    assert "- `ag_fizz_buzz`: FizzBuzz Logic (10 pts)" in prompt
    assert "### Assignment Description\nReturn FizzBuzz array up to n." in prompt
    # No duplicate instructor instructions section when instruction is empty
    assert "### Instructor Instructions" not in prompt


def test_format_user_prompt_with_instructions_and_tests():
    req = AITestAuthoringRequest(
        instruction="Focus on boundary n=15.",
        current_test_code="def test_sample(): pass",
    )
    prompt = _format_user_prompt(
        course_id=None,
        assignment_title="FizzBuzz",
        description="Desc",
        entrypoint="fizzbuzz.py",
        scoring_items=[],
        allowed_concepts=None,
        model_solution_code=None,
        request=req,
    )
    assert "- Course: UVU Computer Science" in prompt
    assert "### Instructor Instructions\nFocus on boundary n=15." in prompt
    assert "### Current tests.py\n```python\ndef test_sample(): pass\n```" in prompt
    assert "### Target Symbols Detected" not in prompt



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

"""Tests for Local LLM integration and AI feedback generation."""

import json
import unittest.mock as mock

from app.integrations.ai.prompts import (
    EXECUTION_ERROR_KEY,
    MAX_FAILURE_MESSAGE_CHARS,
    SYSTEM_PROMPT,
    _render_failure,
    _truncate_message,
    build_messages,
    failures_from_test_results,
    requirements_from_config,
)
from app.integrations.llm.client import FEEDBACK_UNAVAILABLE, LocalLLMClient, sanitize_code_and_text


def test_sanitize_code_and_text():
    raw_code = """
    # Author: John Doe
    # Email: john.doe@uvu.edu
    # Student ID: U10876543
    student_id = "10876543"
    def add(a, b):
        return a + b
    """
    sanitized = sanitize_code_and_text(raw_code)
    assert "john.doe@uvu.edu" not in sanitized
    assert "10876543" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "def add(a, b):" in sanitized

    code_with_vars = """
    filename = "test.txt"
    username = "student_user"
    order_by = "score"
    name = "Project"
    """
    sanitized_vars = sanitize_code_and_text(code_with_vars)
    assert 'filename = "test.txt"' in sanitized_vars
    assert 'username = "student_user"' in sanitized_vars
    assert 'order_by = "score"' in sanitized_vars
    assert 'name = "Project"' in sanitized_vars



def test_local_llm_client_fallback_on_connection_error():
    client = LocalLLMClient(endpoint="http://127.0.0.1:99999/v1", timeout_seconds=1.0)
    res = client.generate_chat_completion([{"role": "user", "content": "hello"}])
    assert "unreachable" in res or "error" in res.lower() or "timed out" in res.lower()


FAILING_RESULTS = [
    {
        "name": "test_filter",
        "outcome": "Failed",
        "test_results": [{"outcome": "failed", "message": "Expected 42 but got 0"}],
    }
]


def _feedback(raw: str, test_results=FAILING_RESULTS, code_files=None) -> tuple[str, list]:
    """Run generate_sandbox_feedback against a canned model response."""
    with mock.patch.object(LocalLLMClient, "_complete_structured", return_value=raw) as mock_chat:
        client = LocalLLMClient()
        feedback = client.generate_sandbox_feedback(
            assignment_title="Lab 1: Image Processing",
            code_files=code_files or {"bears2.py": "def process(): pass"},
            test_results=test_results,
            allowed_concepts=["loops", "functions"],
            warnings=[{"code": "concept_warning", "message": "Avoid while loops"}],
        )
        return feedback, mock_chat.call_args[0][0]


def _json(**overrides) -> str:
    body = {
        "summary": "Your filter runs but returns the wrong value.",
        "items": [{"test_key": "test_filter", "what_went_wrong": "It returns 0.", "hint": "Where is the total updated?"}],
        "next_step": "Trace the loop by hand.",
    }
    body.update(overrides)
    return json.dumps(body)


def test_sandbox_feedback_uses_shared_prompt_and_renders_validated_json():
    feedback, messages = _feedback(_json())
    system_msg, user_msg = messages[0]["content"], messages[1]["content"]
    # One prompt for serving, eval, and training.
    assert system_msg == SYSTEM_PROMPT
    assert "Lab 1: Image Processing" in user_msg
    assert "Expected 42 but got 0" in user_msg
    assert "concept_warning: Avoid while loops" in user_msg
    # Rendered for the UI, labelled with the test's label.
    assert "Your filter runs but returns the wrong value." in feedback
    assert "**test_filter**: It returns 0." in feedback
    assert "Where is the total updated?" in feedback
    assert "**Next step:** Trace the loop by hand." in feedback


def test_sandbox_feedback_blocks_invented_failures():
    raw = _json(items=[{"test_key": "made_up", "what_went_wrong": "x", "hint": "y"}])
    assert _feedback(raw)[0] == FEEDBACK_UNAVAILABLE


def test_sandbox_feedback_blocks_score_statements():
    assert _feedback(_json(summary="You earned 80% on this lab."))[0] == FEEDBACK_UNAVAILABLE


def test_sandbox_feedback_blocks_writing_the_students_code():
    raw = _json(next_step="Try:\ndef process(img):\n    return img")
    assert _feedback(raw)[0] == FEEDBACK_UNAVAILABLE


def test_sandbox_feedback_blocks_non_json_output():
    assert _feedback("Great job! Check line 12.")[0] == FEEDBACK_UNAVAILABLE


def test_sandbox_feedback_all_passing_rejects_any_failure_items():
    passing = [{"key": "k", "label": "K", "passed": True, "item_type": "pytest"}]
    ok = _json(summary="All checks passed -- nice work.", items=[])
    assert "nice work" in _feedback(ok, test_results=passing)[0]
    bad = _json(items=[{"test_key": "k", "what_went_wrong": "x", "hint": "y"}])
    assert _feedback(bad, test_results=passing)[0] == FEEDBACK_UNAVAILABLE


def test_sandbox_feedback_stream_yields_only_validated_text():
    with mock.patch.object(LocalLLMClient, "_complete_structured", return_value=_json()):
        chunks = list(
            LocalLLMClient().generate_sandbox_feedback_stream(
                assignment_title="Lab 1", code_files={"a.py": ""}, test_results=FAILING_RESULTS
            )
        )
    assert len(chunks) > 1
    assert "Where is the total updated?" in "".join(chunks)
    with mock.patch.object(LocalLLMClient, "_complete_structured", return_value="You got 90%"):
        chunks = list(
            LocalLLMClient().generate_sandbox_feedback_stream(
                assignment_title="Lab 1", code_files={"a.py": ""}, test_results=FAILING_RESULTS
            )
        )
    assert "".join(chunks) == FEEDBACK_UNAVAILABLE


def test_failures_from_test_results_skips_manual_and_passed_items():
    results = [
        {"key": "init", "label": "Init", "passed": True, "item_type": "pytest"},
        {"key": "reflection", "label": "Reflection", "passed": False, "item_type": "manual"},
        {
            "key": "str",
            "label": "__str__ output",
            "passed": False,
            "item_type": "pytest",
            "your_value": "$5.5",
            "expected_value": "$5.50",
            "test_results": [{"outcome": "failed", "message": "assert '$5.5' == '$5.50'"}],
        },
    ]
    failures, passing = failures_from_test_results(results)
    assert [f["key"] for f in failures] == ["str"]
    assert failures[0]["message"] == "assert '$5.5' == '$5.50'"
    assert passing == ["Init"]


def test_failures_from_test_results_execution_error_is_citable():
    failures, _ = failures_from_test_results([], failure_message="SyntaxError: invalid syntax")
    assert failures == [
        {"key": EXECUTION_ERROR_KEY, "label": "Submission could not run", "message": "SyntaxError: invalid syntax"}
    ]


def test_prompt_is_sanitized_for_every_caller():
    messages = build_messages(
        assignment_title="Lab 2",
        requirements="",
        allowed_concepts=[],
        failures=[{"key": "k", "label": "K", "message": "failed for jane.doe@uvu.edu"}],
        concept_violations=[],
        student_code="# Author: Jane Doe\nx = 10123456\n",
    )
    user = messages[1]["content"]
    assert "jane.doe@uvu.edu" not in user and "Jane Doe" not in user and "10123456" not in user


def test_requirements_from_config_lists_automated_items_only():
    config = {
        "scoring_items": [
            {"key": "a", "label": "Account init", "item_type": "pytest"},
            {"key": "r", "label": "Reflection", "item_type": "manual"},
        ]
    }
    text = requirements_from_config(config)
    assert "Account init" in text and "Reflection" not in text
    assert requirements_from_config(None) == ""


def test_requirements_from_config_includes_sanitized_and_truncated_description():
    config = {
        "description": "Implement student submission. Contact jane.doe@uvu.edu (10123456) for help.",
        "scoring_items": [
            {"key": "a", "label": "Account init", "item_type": "pytest"},
        ],
    }
    text = requirements_from_config(config)
    assert "jane.doe@uvu.edu" not in text
    assert "10123456" not in text
    assert "Implement student submission." in text
    assert "Automatically checked items:" in text
    assert "- Account init" in text

    # Long description truncated to 1000 chars
    long_desc = "A" * 1500
    text_long = requirements_from_config({"scoring_items": []}, description=long_desc)
    assert text_long.startswith("A" * 1000)
    assert text_long.endswith("...")
    assert len(text_long) == 1003


def test_local_llm_global_code_ceiling():
    client = LocalLLMClient()
    # Provide 3 files of 9000 chars each (total 27,000 chars > 16,000 ceiling)
    code_files = {
        "file1.py": "x = 1\n" * 1500,
        "file2.py": "y = 2\n" * 1500,
        "file3.py": "z = 3\n" * 1500,
    }
    messages = client.build_sandbox_messages(
        assignment_title="Test Lab",
        code_files=code_files,
        test_results=[],
    )
    user_prompt = messages[1]["content"]
    assert "[truncated]" in user_prompt or "additional files truncated" in user_prompt
    # Total code content in prompt should be bounded
    assert len(user_prompt) < 22000


def test_truncate_message_under_limit():
    short_msg = "AssertionError: expected 5 but got 4"
    assert _truncate_message(short_msg) == short_msg


def test_truncate_message_at_limit():
    exact_msg = "x" * MAX_FAILURE_MESSAGE_CHARS
    assert _truncate_message(exact_msg) == exact_msg


def test_truncate_message_exceeding_limit():
    head = "A" * 400
    middle = "M" * 500
    tail = "Z" * 400
    long_msg = head + middle + tail
    result = _truncate_message(long_msg)
    assert result.startswith(head)
    assert result.endswith(tail)
    assert "... [truncated 500 chars] ..." in result
    assert middle not in result


def test_render_failure_truncates_long_assertion():
    long_assertion = "assert False\n" + ("traceback line\n" * 100)
    item = {
        "key": "test_calc",
        "label": "Calculator test",
        "message": long_assertion,
    }
    rendered = _render_failure(item)
    assert "- test_key: test_calc" in rendered
    assert "label: Calculator test" in rendered
    assert "... [truncated" in rendered
    assert len(rendered) < len(long_assertion)


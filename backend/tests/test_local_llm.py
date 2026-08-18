"""Tests for Local LLM integration and AI feedback generation."""

import unittest.mock as mock
from app.integrations.llm.client import LocalLLMClient, sanitize_code_and_text


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
    assert "[REDACTED_ID]" in sanitized
    assert "def add(a, b):" in sanitized


def test_local_llm_client_fallback_on_connection_error():
    client = LocalLLMClient(endpoint="http://127.0.0.1:99999/v1", timeout_seconds=1.0)
    res = client.generate_chat_completion([{"role": "user", "content": "hello"}])
    assert "unreachable" in res or "error" in res.lower()


def test_local_llm_generate_sandbox_feedback_format():
    with mock.patch.object(LocalLLMClient, "generate_chat_completion", return_value="Great job! Check line 12.") as mock_chat:
        client = LocalLLMClient()
        feedback = client.generate_sandbox_feedback(
            assignment_title="Lab 1: Image Processing",
            code_files={"bears2.py": "def process(): pass"},
            test_results=[{"name": "test_filter", "outcome": "Failed", "test_results": [{"outcome": "failed", "message": "Expected 42 but got 0"}]}],
            allowed_concepts=["loops", "functions"],
            warnings=[{"code": "concept_warning", "message": "Avoid while loops"}],
        )
        assert feedback == "Great job! Check line 12."
        mock_chat.assert_called_once()
        call_args = mock_chat.call_args[0][0]
        system_msg = call_args[0]["content"]
        user_msg = call_args[1]["content"]
        assert "Teaching Assistant" in system_msg
        assert "Lab 1: Image Processing" in user_msg
        assert "Expected 42 but got 0" in user_msg

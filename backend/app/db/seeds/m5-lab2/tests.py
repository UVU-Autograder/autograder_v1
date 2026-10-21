"""Tests for CS 1400 Module 5 Lab 2: Input Validation for Name and Age."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        run_script,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        run_script,
    )

ENTRYPOINT = "validate_name_age.py"


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify code includes comments or docstrings explaining the validation logic."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_doc = any(
        isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for node in ast.walk(tree)
    )
    try:
        assert_has_comments(ENTRYPOINT, min_comments=1)
        has_comment = True
    except AssertionError:
        has_comment = False

    assert has_doc or has_comment, "Script must include an explanatory comment or docstring."


@pytest.mark.ag_prompt_inputs
def test_prompt_inputs():
    """Verify script prompts for both name and age."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 2, f"Expected at least 2 input() calls (for name and age), found {len(input_calls)}."


@pytest.mark.ag_validate_name
def test_validate_name():
    """Verify validation that name is non-empty and non-numeric."""
    res = run_script(ENTRYPOINT, inputs=["123", "Alice", "21"])
    assert res.returncode == 0, f"Script failed with inputs ['123', 'Alice', '21']:\n{res.stderr}"
    stdout_lower = res.stdout.lower()
    assert "invalid" in stdout_lower or "name" in stdout_lower, (
        f"Expected invalid name error message when numeric name '123' is entered. Got:\n{res.stdout}"
    )
    assert "alice" in stdout_lower, f"Expected valid name 'Alice' in output. Got:\n{res.stdout}"


@pytest.mark.ag_try_except_age
def test_try_except_age():
    """Verify script uses try/except to validate age is an integer."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    assert has_try, "Script must use a try/except block to validate integer age conversion."

    res = run_script(ENTRYPOINT, inputs=["Alice", "twenty", "21"])
    assert res.returncode == 0, f"Script failed with invalid age input ['twenty']:\n{res.stderr}"
    stdout_lower = res.stdout.lower()
    assert "invalid" in stdout_lower or "integer" in stdout_lower or "age" in stdout_lower, (
        f"Expected invalid age message when non-integer 'twenty' is entered. Got:\n{res.stdout}"
    )


@pytest.mark.ag_reprompt_loop
def test_reprompt_loop():
    """Verify script continues prompting in a loop until valid inputs are provided."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_loop = any(isinstance(node, (ast.While, ast.For)) for node in ast.walk(tree))
    assert has_loop, "Script must use a loop to continue prompting until inputs are valid."

    res = run_script(ENTRYPOINT, inputs=["888", "Charlie", "not_a_number", "45"])
    assert res.returncode == 0, f"Script failed on loop reprompting:\n{res.stderr}"
    assert "Charlie" in res.stdout, f"Expected final confirmation for Charlie in output:\n{res.stdout}"


@pytest.mark.ag_confirmation_message
def test_confirmation_message():
    """Verify script prints clear confirmation message with name and age."""
    res = run_script(ENTRYPOINT, inputs=["Maya", "28"])
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    assert "Maya" in res.stdout, f"Expected 'Maya' in confirmation message. Got:\n{res.stdout}"
    assert "28" in res.stdout, f"Expected '28' in confirmation message. Got:\n{res.stdout}"

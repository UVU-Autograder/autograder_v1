"""Tests for CS 1400 Module 1 Lab 2: Read Name and UVU ID, Then Print."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        find_assigned_variables,
        run_script,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        find_assigned_variables,
        run_script,
    )

ENTRYPOINT = "greet_user_uvuid.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_code_comment
def test_code_comment():
    """Verify script contains at least one explanatory comment."""
    assert_has_comments(ENTRYPOINT, min_comments=1)


@pytest.mark.ag_input_collected
def test_input_collected():
    """Verify input() is called to collect both name and UVU ID."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 2, (
        f"Expected at least 2 calls to input() for name and UVU ID. Found {len(input_calls)}."
    )


@pytest.mark.ag_variables_stored
def test_variables_stored():
    """Verify values are stored in appropriately named variables."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert len(assigned) >= 2, (
        f"Expected at least two variables to store user input. Found: {list(assigned.keys())}"
    )


@pytest.mark.ag_output_greeting
def test_output_greeting():
    """Verify output contains personalized greeting with both name and ID."""
    # Test run 1
    res1 = run_script(ENTRYPOINT, inputs=["Alice Smith", "12345678"])
    assert res1.returncode == 0, f"Script failed with inputs 'Alice Smith', '12345678':\n{res1.stderr}"
    stdout1 = res1.stdout
    assert "Alice Smith" in stdout1, f"Expected 'Alice Smith' in output. Got:\n{stdout1}"
    assert "12345678" in stdout1, f"Expected '12345678' in output. Got:\n{stdout1}"
    assert "Hello" in stdout1 or "hello" in stdout1.lower(), (
        f"Expected greeting starting with 'Hello'. Got:\n{stdout1}"
    )

    # Test run 2 with different values to confirm dynamic behavior
    res2 = run_script(ENTRYPOINT, inputs=["Bob Jones", "87654321"])
    assert res2.returncode == 0, f"Script failed with inputs 'Bob Jones', '87654321':\n{res2.stderr}"
    stdout2 = res2.stdout
    assert "Bob Jones" in stdout2, f"Expected dynamic name 'Bob Jones' in output. Got:\n{stdout2}"
    assert "87654321" in stdout2, f"Expected dynamic ID '87654321' in output. Got:\n{stdout2}"

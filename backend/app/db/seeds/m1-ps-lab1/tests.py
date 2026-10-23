"""Tests for CS 1400 Module 1 PS Lab 1: Festival Ration Preparation."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        assert_valid_naming,
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
        assert_valid_naming,
        find_assigned_variables,
        run_script,
    )

ENTRYPOINT = "festival_ration.py"


@pytest.mark.ag_clean_run_and_comment
def test_clean_run_and_comment():
    """Verify program runs without syntax errors and contains explanatory comments."""
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)
    res = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res.returncode == 0, f"Program exited with non-zero status:\n{res.stderr}"


@pytest.mark.ag_naming_and_formatting
def test_naming_and_formatting():
    """Verify snake_case/camelCase variable names and clear output formatting."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert len(assigned) >= 2, f"Expected at least two variables defined. Found: {list(assigned.keys())}"
    assert_valid_naming(assigned.keys())

    res = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res.returncode == 0
    stdout = res.stdout.lower()
    assert "original" in stdout or "supply" in stdout, "Output should label the original supply."
    assert "ration" in stdout, "Output should label the ration allocation."
    assert "remaining" in stdout or "stockpile" in stdout, "Output should label remaining festival stockpile."


@pytest.mark.ag_input_and_types
def test_input_and_types():
    """Verify input collection and integer type conversion."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)

    # Check for calls to int() and input()
    has_input = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
        for node in ast.walk(tree)
    )
    has_int = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int"
        for node in ast.walk(tree)
    )
    assert has_input, "Program must use input() to collect data from user."
    assert has_int, "Program must convert input strings to integers."


@pytest.mark.ag_calculation_accuracy
def test_calculation_accuracy():
    """Verify calculation accuracy for multiple sets of test inputs."""
    # Case 1: 25 colonists, 1200 units -> ration: 100, remaining: 1100
    res1 = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res1.returncode == 0, f"Script failed on inputs 25, 1200:\n{res1.stderr}"
    stdout1 = res1.stdout
    assert "100" in stdout1, f"Expected ration allocation of 100 in output:\n{stdout1}"
    assert "1100" in stdout1, f"Expected remaining stockpile of 1100 in output:\n{stdout1}"

    # Case 2: 10 colonists, 500 units -> ration: 40, remaining: 460
    res2 = run_script(ENTRYPOINT, inputs=["10", "500"])
    assert res2.returncode == 0, f"Script failed on inputs 10, 500:\n{res2.stderr}"
    stdout2 = res2.stdout
    assert "40" in stdout2, f"Expected ration allocation of 40 in output:\n{stdout2}"
    assert "460" in stdout2, f"Expected remaining stockpile of 460 in output:\n{stdout2}"

"""Tests for CS 1400 Module 1 Lab 1: Sum of Two Numbers."""

from __future__ import annotations

import ast
import re
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

ENTRYPOINT = "sum_two_numbers.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_code_comment
def test_code_comment():
    """Verify script contains at least one explanatory comment."""
    assert_has_comments(ENTRYPOINT, min_comments=1)


@pytest.mark.ag_variables_declared
def test_variables_declared():
    """Verify at least two integer variables are declared in the script."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    int_vars = [
        k for k, v in assigned.items()
        if isinstance(v, ast.Constant) and isinstance(v.value, int)
    ]
    assert len(int_vars) >= 2 or len(assigned) >= 2, (
        f"Expected at least two integer variables declared. Found assigned variables: {list(assigned.keys())}"
    )


@pytest.mark.ag_sum_calculated
def test_sum_calculated():
    """Verify the sum of numbers is calculated."""
    res = run_script(ENTRYPOINT, inputs=["10", "20"])
    assert res.returncode == 0, f"Script crashed during execution:\n{res.stderr}"

    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_add_op = any(
        isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
        for node in ast.walk(tree)
    )
    has_sum_call = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sum"
        for node in ast.walk(tree)
    )
    assert has_add_op or has_sum_call or "30" in res.stdout, (
        "Script should calculate the sum of the numbers using addition."
    )


@pytest.mark.ag_output_formatted
def test_output_formatted():
    """Verify output displays a clear formatted message with print()."""
    res = run_script(ENTRYPOINT, inputs=["10", "20"])
    assert res.returncode == 0, f"Script failed to run:\n{res.stderr}"
    stdout = res.stdout.strip()
    assert stdout, "Script did not produce any output."
    has_sum_phrase = bool(re.search(r"sum.*(?:is|:|=)\s*(\d+)", stdout, re.IGNORECASE))
    assert has_sum_phrase or ("30" in stdout), (
        f"Output should display a clear message with the sum. Got:\n{stdout}"
    )

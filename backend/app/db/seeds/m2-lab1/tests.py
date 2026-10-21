"""Tests for CS 1400 Module 2 Lab 1: Evaluate Equations with Different Parentheses Scopes."""

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

ENTRYPOINT = "evaluate_equations.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_explanatory_comments
def test_explanatory_comments():
    """Verify script includes comments explaining the effect of parentheses."""
    assert_has_comments(ENTRYPOINT, min_comments=2)


@pytest.mark.ag_three_equations_defined
def test_three_equations_defined():
    """Verify script defines at least three different equations with arithmetic operations."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    binops = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv))
    ]
    assert len(binops) >= 3, (
        f"Expected at least 3 arithmetic expressions using +, -, *, or /. Found {len(binops)}."
    )


@pytest.mark.ag_parentheses_variations
def test_parentheses_variations():
    """Verify that multiple variations and evaluation results are generated."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script crashed:\n{res.stderr}"
    stdout = res.stdout
    # Expect multiple cases shown in output
    assert stdout.count("Case") >= 4 or stdout.count("=") >= 4, (
        f"Expected multiple cases/variations showing evaluated results. Got output:\n{stdout}"
    )


@pytest.mark.ag_results_printed
def test_results_printed():
    """Verify results and equations are printed in a clear and formatted way."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed to run:\n{res.stderr}"
    stdout = res.stdout.strip()
    assert stdout, "Script did not produce any output."
    assert "Equation" in stdout or "case" in stdout.lower() or "=" in stdout, (
        f"Output should clearly display equations and case results. Got:\n{stdout}"
    )

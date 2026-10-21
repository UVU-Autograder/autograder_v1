"""Tests for CS 1400 Module 3 Lab 2: Basic Arithmetic Function."""

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

ENTRYPOINT = "basic_ops.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify code contains comments or docstrings."""
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


@pytest.mark.ag_function_defined
def test_function_defined():
    """Verify a function is defined that accepts two parameters."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    two_param_funcs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and len(node.args.args) >= 2
    ]
    assert len(two_param_funcs) >= 1, "Script must define a function taking two numeric parameters."


@pytest.mark.ag_operations_computed
def test_operations_computed():
    """Verify addition, subtraction, multiplication, and division are computed."""
    res = run_script(ENTRYPOINT, inputs=["12", "5", "all"])
    assert res.returncode == 0, f"Script failed with inputs 12, 5, all:\n{res.stderr}"
    stdout = res.stdout
    assert "17" in stdout, f"Missing addition result (17) in output:\n{stdout}"
    assert "7" in stdout, f"Missing subtraction result (7) in output:\n{stdout}"
    assert "60" in stdout, f"Missing multiplication result (60) in output:\n{stdout}"
    assert "2.4" in stdout, f"Missing division result (2.4) in output:\n{stdout}"


@pytest.mark.ag_formatted_output
def test_formatted_output():
    """Verify output has clear labels for each operation."""
    res = run_script(ENTRYPOINT, inputs=["12", "5", "all"])
    assert res.returncode == 0
    stdout = res.stdout.lower()
    assert "addition" in stdout, "Output should clearly label Addition."
    assert "subtraction" in stdout, "Output should clearly label Subtraction."
    assert "multiplication" in stdout, "Output should clearly label Multiplication."
    assert "division" in stdout, "Output should clearly label Division."

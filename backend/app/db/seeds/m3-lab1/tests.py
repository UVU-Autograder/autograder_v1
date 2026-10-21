"""Tests for CS 1400 Module 3 Lab 1: Count Occurrences of a Character in a String."""

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

ENTRYPOINT = "count_chars.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_comments_or_docstring
def test_comments_or_docstring():
    """Verify code includes comments or docstrings."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_docstring = any(
        isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for node in ast.walk(tree)
    )
    try:
        assert_has_comments(ENTRYPOINT, min_comments=1)
        has_comment = True
    except AssertionError:
        has_comment = False

    assert has_docstring or has_comment, "Script must include at least one explanatory comment or docstring."


@pytest.mark.ag_function_returns_count
def test_function_returns_count():
    """Verify that a function is defined and correctly returns character counts."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name != "main"
    ]
    assert len(functions) >= 1, "Script must define a function that counts characters."

    # Test via execution
    res1 = run_script(ENTRYPOINT, inputs=["APPLE CAT!", "A"])
    assert res1.returncode == 0, f"Script failed with inputs 'APPLE CAT!', 'A':\n{res1.stderr}"
    assert "2" in res1.stdout, f"Expected count of 2 in output. Got:\n{res1.stdout}"

    res2 = run_script(ENTRYPOINT, inputs=["banana", "a"])
    assert res2.returncode == 0
    assert "3" in res2.stdout, f"Expected count of 3 in output. Got:\n{res2.stdout}"


@pytest.mark.ag_result_printed
def test_result_printed():
    """Verify output is stored and printed in a formatted message."""
    res = run_script(ENTRYPOINT, inputs=["APPLE CAT!", "A"])
    assert res.returncode == 0
    stdout = res.stdout
    assert "appears 2 time" in stdout.lower() or "2" in stdout, (
        f"Expected formatted message showing character count. Got:\n{stdout}"
    )

"""Tests for CS 1400 Module 4 Lab 2: Even or Odd Checker."""

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

ENTRYPOINT = "even_odd_checker.py"


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


@pytest.mark.ag_option_prompt
def test_option_prompt():
    """Verify script prompts user for option ('c' to check, 'q' to quit)."""
    res = run_script(ENTRYPOINT, inputs=["q"])
    assert res.returncode == 0, f"Script failed on immediate quit ('q'):\n{res.stderr}"
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 1, "Script must use input() to prompt the user."


@pytest.mark.ag_loop_until_quit
def test_loop_until_quit():
    """Verify script uses a while loop to repeatedly prompt until user enters 'q'."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_while = any(isinstance(node, ast.While) for node in ast.walk(tree))
    assert has_while, "Script must use a while loop to repeatedly prompt for options."

    # Test that multiple checks work sequentially in one run
    res = run_script(ENTRYPOINT, inputs=["c", "12", "c", "17", "q"])
    assert res.returncode == 0, f"Script failed when looping through multiple checks:\n{res.stderr}"
    stdout_lower = res.stdout.lower()
    assert "even" in stdout_lower and "odd" in stdout_lower, (
        f"Expected multiple results in loop output. Got:\n{res.stdout}"
    )


@pytest.mark.ag_even_odd_logic
def test_even_odd_logic():
    """Verify code accurately identifies even and odd numbers."""
    # Test positive even and odd
    res = run_script(ENTRYPOINT, inputs=["c", "4", "c", "7", "q"])
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    stdout = res.stdout.lower()
    assert "even" in stdout, f"Expected 'even' in output for 4. Got:\n{res.stdout}"
    assert "odd" in stdout, f"Expected 'odd' in output for 7. Got:\n{res.stdout}"

    # Test 0 and negative numbers
    res2 = run_script(ENTRYPOINT, inputs=["c", "0", "c", "-9", "q"])
    assert res2.returncode == 0, f"Script failed with 0 and negative numbers:\n{res2.stderr}"
    stdout2 = res2.stdout.lower()
    assert "even" in stdout2, f"Expected 'even' in output for 0. Got:\n{res2.stdout}"
    assert "odd" in stdout2, f"Expected 'odd' in output for -9. Got:\n{res2.stdout}"


@pytest.mark.ag_formatted_output
def test_formatted_output():
    """Verify program prints formatted results and terminates gracefully."""
    res = run_script(ENTRYPOINT, inputs=["c", "42", "q"])
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    assert "42" in res.stdout, f"Expected checked number '42' in output:\n{res.stdout}"
    assert "even" in res.stdout.lower(), f"Expected 'even' in output for 42:\n{res.stdout}"

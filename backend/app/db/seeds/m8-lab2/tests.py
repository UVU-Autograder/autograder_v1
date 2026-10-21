"""Tests for CS 1400 Module 8 Lab 2: Tuple-Based Number Guessing Game."""

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

ENTRYPOINT = "tuple_guess_game.py"


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify script exists, compiles with no syntax errors, and includes comments."""
    assert_no_syntax_errors(ENTRYPOINT)
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


@pytest.mark.ag_generate_random_tuple
def test_generate_random_tuple():
    """Verify script imports random and constructs a tuple of random numbers."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert "random" in source, "Script must import and use the random module."
    has_tuple = "tuple(" in source or any(isinstance(n, ast.Tuple) for n in ast.walk(tree))
    assert has_tuple, "Script must generate a tuple of target numbers."


@pytest.mark.ag_input_to_tuple
def test_input_to_tuple():
    """Verify user input is converted into a tuple of integers."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert "input" in source and "tuple(" in source, (
        "Script must accept input and convert it into a tuple of integers."
    )


@pytest.mark.ag_compare_and_feedback
def test_compare_and_feedback():
    """Verify feedback indicates number of values matched in correct positions."""
    inputs = [
        "1 2 3 4 5",
        "6 7 8 9 10",
        "11 12 13 14 15",
        "16 17 18 19 20",
        "1 1 1 1 1",
    ]
    res = run_script(ENTRYPOINT, inputs=inputs)
    assert res.returncode == 0, f"Script failed on game execution:\n{res.stderr}"
    stdout_lower = res.stdout.lower()
    assert "matched" in stdout_lower or "correct" in stdout_lower, (
        f"Expected feedback on matching numbers in stdout. Got:\n{res.stdout}"
    )


@pytest.mark.ag_track_best_attempt
def test_track_best_attempt():
    """Verify script reveals correct combination and percentage match after attempts."""
    inputs = [
        "1 2 3 4 5",
        "6 7 8 9 10",
        "11 12 13 14 15",
        "16 17 18 19 20",
        "2 2 2 2 2",
    ]
    res = run_script(ENTRYPOINT, inputs=inputs)
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    stdout = res.stdout
    assert "correct" in stdout.lower() or "combination" in stdout.lower(), (
        f"Expected correct combination revelation in output:\n{stdout}"
    )
    assert "%" in stdout or "best" in stdout.lower(), (
        f"Expected best match percentage in output:\n{stdout}"
    )

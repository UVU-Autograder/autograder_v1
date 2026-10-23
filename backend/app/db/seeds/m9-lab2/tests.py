"""Tests for CS 1400 Module 9 Lab 2: Student Scorebook with Dictionary."""

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

ENTRYPOINT = "student_scorebook.py"


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


@pytest.mark.ag_init_populate_dict
def test_init_populate_dict():
    """Verify dictionary is initialized and populated with student scores."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_dict = "{}" in source or "dict(" in source or any(isinstance(n, ast.Dict) for n in ast.walk(tree))
    assert has_dict, "Script must create a dictionary named scorebook."
    assert "Alice" in source and "Bob" in source and "Charlie" in source and "Dana" in source, (
        "Script must populate initial scores for Alice, Bob, Charlie, and Dana."
    )


@pytest.mark.ag_for_loop_items
def test_for_loop_items():
    """Verify .items() and for loop are used to print dictionary contents."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_for = any(isinstance(n, ast.For) for n in ast.walk(tree))
    assert has_for and ".items()" in source, "Script must iterate through scorebook using a for loop and .items()."


@pytest.mark.ag_update_and_remove
def test_update_and_remove():
    """Verify Dana's score is updated and Bob is removed via pop or del."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_pop_or_del = ".pop(" in source or any(isinstance(n, ast.Delete) for n in ast.walk(tree))
    assert has_pop_or_del, "Script must remove Bob from scorebook using .pop() or del."
    assert "85" in source, "Script must update Dana's score to 85."


@pytest.mark.ag_check_key_exists
def test_check_key_exists():
    """Verify script checks for Eve using .get() or in."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_get_or_in = ".get(" in source or " in " in source
    assert has_get_or_in and "Eve" in source, "Script must check for student 'Eve' using .get() or in."


@pytest.mark.ag_average_score
def test_average_score():
    """Verify script prints the average score of remaining students (88.67)."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout
    assert "88.67" in stdout or "88.7" in stdout, (
        f"Expected average score (88.67) in output. Got:\n{stdout}"
    )
    assert "Eve" in stdout, f"Expected message about Eve in output:\n{stdout}"

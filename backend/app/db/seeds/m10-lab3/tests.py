"""Tests for CS 1400 Module 10 Lab 3: Student Club Memberships Using Sets."""

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

ENTRYPOINT = "student_club_sets.py"


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


@pytest.mark.ag_init_club_sets
def test_init_club_sets():
    """Verify script initializes coding_club and robotics_club sets."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_set = "set(" in source or any(isinstance(n, ast.Set) for n in ast.walk(tree))
    assert has_set, "Script must initialize sets for club memberships."
    assert "Alice" in source and "Charlie" in source and "Eve" in source, (
        "Script must include student names in initial club sets."
    )


@pytest.mark.ag_intersection_clubs
def test_intersection_clubs():
    """Verify script computes intersection of clubs."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_inter = "&" in source or ".intersection(" in source
    assert has_inter, "Script must use & or .intersection() to find students in both clubs."

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout
    assert "both" in stdout.lower() and "Charlie" in stdout and "Bob" in stdout, (
        f"Expected intersection with Charlie and Bob in output:\n{stdout}"
    )


@pytest.mark.ag_diff_and_symm_diff
def test_diff_and_symm_diff():
    """Verify script computes symmetric difference and difference."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_symm = "^" in source or ".symmetric_difference(" in source
    has_diff = "-" in source or ".difference(" in source
    assert has_symm and has_diff, (
        "Script must compute symmetric difference (^ or .symmetric_difference) and difference (- or .difference)."
    )


@pytest.mark.ag_add_and_discard
def test_add_and_discard():
    """Verify script uses .add() for Grace and .discard() for Eve."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert ".add(" in source and "Grace" in source, "Script must add 'Grace' using .add()."
    assert ".discard(" in source and "Eve" in source, "Script must remove 'Eve' using .discard()."


@pytest.mark.ag_union_clubs
def test_union_clubs():
    """Verify script computes union to find all unique students."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_union = "|" in source or ".union(" in source
    assert has_union, "Script must use | or .union() to find all unique students."

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    stdout = res.stdout
    assert "Grace" in stdout, f"Expected added member 'Grace' in output:\n{stdout}"
    assert "Alice" in stdout and "Dana" in stdout, f"Expected unique students in output:\n{stdout}"

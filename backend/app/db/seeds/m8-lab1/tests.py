"""Tests for CS 1400 Module 8 Lab 1: Analyze Student Grades Using Tuples."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_file_exists,
        assert_has_comments,
        assert_no_syntax_errors,
        run_script,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_file_exists,
        assert_has_comments,
        assert_no_syntax_errors,
        run_script,
    )

ENTRYPOINT = "analyze_student_grades.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("analyze_student_grades", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["analyze_student_grades"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify script exists, compiles without errors, and includes comments."""
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


@pytest.mark.ag_store_tuples
def test_store_tuples():
    """Verify student data is stored as tuples."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_tuple = any(isinstance(node, ast.Tuple) for node in ast.walk(tree))
    assert has_tuple, "Script must store student name/grade pairs using tuples."


@pytest.mark.ag_analyze_grades_computation
def test_analyze_grades_computation():
    """Verify analyze_grades computes average, min, max, and student names correctly."""
    mod = _load_module()
    assert hasattr(mod, "analyze_grades"), "Script must define 'analyze_grades(student_data)' function."
    analyze_fn = getattr(mod, "analyze_grades")

    test_data = [("Alice", 87), ("Bob", 92), ("Charlie", 78), ("Dana", 85)]
    res = analyze_fn(test_data)

    # Flatten res if nested
    res_str = str(res)
    assert "85.5" in res_str or pytest.approx(85.5) in [x for x in res if isinstance(x, (int, float))], (
        f"Expected average 85.5 in result: {res}"
    )
    assert "Bob" in res_str, f"Expected 'Bob' as top student in result: {res}"
    assert "92" in res_str, f"Expected highest grade 92 in result: {res}"
    assert "Charlie" in res_str, f"Expected 'Charlie' as lowest student in result: {res}"
    assert "78" in res_str, f"Expected lowest grade 78 in result: {res}"


@pytest.mark.ag_return_unpack_tuple
def test_return_unpack_tuple():
    """Verify analyze_grades returns a tuple."""
    mod = _load_module()
    analyze_fn = getattr(mod, "analyze_grades")
    res = analyze_fn([("Emma", 90), ("Liam", 80)])
    assert isinstance(res, tuple), f"Expected analyze_grades to return a tuple, got {type(res)}"


@pytest.mark.ag_formatted_output
def test_formatted_output():
    """Verify main script prints formatted statistics."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout
    assert "85.5" in stdout, f"Expected average grade 85.5 in output:\n{stdout}"
    assert "92" in stdout and "Bob" in stdout, f"Expected 92 (Bob) in output:\n{stdout}"
    assert "78" in stdout and "Charlie" in stdout, f"Expected 78 (Charlie) in output:\n{stdout}"

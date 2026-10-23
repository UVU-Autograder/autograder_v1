"""Tests for CS 1400 Module 11 Lab 1: Grade Summary Generator."""

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

ENTRYPOINT = "grade_summary.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("grade_summary", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["grade_summary"] = mod
    spec.loader.exec_module(mod)
    return mod


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


@pytest.mark.ag_helper_avg_calc
def test_helper_avg_calc():
    """Verify calculate_average computes mean and returns 'N/A' on empty list."""
    mod = _load_module()
    assert hasattr(mod, "calculate_average"), "Script must define 'calculate_average(grades)'."
    calc_fn = getattr(mod, "calculate_average")
    assert calc_fn([80, 90]) == 85.0
    assert calc_fn([]) == "N/A"


@pytest.mark.ag_list_comp_filter
def test_list_comp_filter():
    """Verify process_grades uses a list comprehension to filter invalid grades."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_comp = any(isinstance(n, ast.ListComp) for n in ast.walk(tree))
    assert has_comp, "Script must use list comprehension to filter invalid grades."

    mod = _load_module()
    valid_grades, _, _ = mod.process_grades([95, 82, -10, 76, 59, 89, 101])
    assert valid_grades == [95, 82, 76, 59, 89], f"Unexpected filtered grades: {valid_grades}"


@pytest.mark.ag_inner_grade_dist
def test_inner_grade_dist():
    """Verify grade_distribution is an inner function inside process_grades."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    process_node = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "process_grades"),
        None,
    )
    assert process_node is not None, "Function 'process_grades' not found."

    inner_funcs = [n for n in process_node.body if isinstance(n, ast.FunctionDef)]
    assert len(inner_funcs) >= 1, "process_grades must define an inner function (grade_distribution)."


@pytest.mark.ag_closure_scope
def test_closure_scope():
    """Verify the inner function uses closure rather than passing grades as parameter."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    process_node = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "process_grades"),
        None,
    )
    inner_func = next((n for n in process_node.body if isinstance(n, ast.FunctionDef)), None)
    assert inner_func is not None
    assert len(inner_func.args.args) == 0, (
        "Inner function grade_distribution should take 0 parameters and access valid_grades via closure."
    )


@pytest.mark.ag_formatted_result
def test_formatted_result():
    """Verify final results are printed in a readable format."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout
    assert "80.2" in stdout, f"Expected average 80.2 in stdout:\n{stdout}"
    assert "Valid grades" in stdout or "82" in stdout
    assert "Grade distribution" in stdout or "'A': 1" in stdout

"""Tests for CS 1400 Module 10 Lab 2: Course Enrollment System."""

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

ENTRYPOINT = "course_enrollment.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("course_enrollment", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["course_enrollment"] = mod
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


@pytest.mark.ag_nested_dict_init
def test_nested_dict_init():
    """Verify student data is stored as a nested dictionary."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    dicts = [n for n in ast.walk(tree) if isinstance(n, ast.Dict)]
    assert len(dicts) >= 2, "Script must define a nested dictionary modeling student records."


@pytest.mark.ag_print_student_info_fn
def test_print_student_info_fn():
    """Verify print_student_info is defined and uses .get()."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert "print_student_info" in source, "Script must define 'print_student_info(student_id)'."
    assert ".get(" in source, "print_student_info should use .get() for safe lookup."


@pytest.mark.ag_enroll_student_fn
def test_enroll_student_fn():
    """Verify enroll_student adds a course to student's course list."""
    mod = _load_module()
    assert hasattr(mod, "enroll_student"), "Script must define 'enroll_student(student_id, course_code)'."
    mod.enroll_student("S001", "CS2810")
    s1 = getattr(mod, "students", {}).get("S001", {})
    assert "CS2810" in s1.get("courses", []), "Enrolled course must be added to student's courses."


@pytest.mark.ag_drop_student_fn
def test_drop_student_fn():
    """Verify drop_student removes student record using .pop()."""
    mod = _load_module()
    assert hasattr(mod, "drop_student"), "Script must define 'drop_student(student_id)'."
    mod.drop_student("S003")
    students = getattr(mod, "students", {})
    assert "S003" not in students, "Dropped student must be removed from dictionary."


@pytest.mark.ag_display_methods
def test_display_methods():
    """Verify script uses keys(), items(), or values() to display records."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_display = ".keys()" in source or ".items()" in source or ".values()" in source
    assert has_display, "Script must use .keys(), .items(), or .values() to display student info."

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    assert "Alice" in res.stdout, f"Expected student 'Alice' in output:\n{res.stdout}"

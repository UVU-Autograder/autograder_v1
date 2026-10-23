"""Tests for CS 1400 Module 14 Lab 1: Student Grade Management System."""

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

ENTRYPOINT = "student_grade_manager.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("student_grade_manager", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_program_design
def test_program_design():
    assert_file_exists(ENTRYPOINT)
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=2)

    # Check for design / pseudocode plan in comments or docstring
    source_lower = source.lower()
    has_design_terms = (
        "design" in source_lower
        or "pseudocode" in source_lower
        or "plan" in source_lower
        or "tasks" in source_lower
    )
    assert has_design_terms, (
        "Script must include a program design plan or pseudocode in header comments."
    )


@pytest.mark.ag_program_implementation
def test_program_implementation():
    mod = _load_module()
    assert hasattr(mod, "add_student"), "Must define add_student() function."
    assert hasattr(mod, "calculate_average"), "Must define calculate_average() function."
    assert hasattr(mod, "find_student"), "Must define find_student() function."

    gradebook = {}
    mod.add_student("Sara", 90, gradebook)
    mod.add_student("Liam", 80, gradebook)

    avg = mod.calculate_average(gradebook)
    assert avg == 85.0, f"Expected average 85.0, got {avg}."

    found = mod.find_student("Sara", gradebook)
    assert found == 90.0 or found == 90, f"Expected 90, got {found}."


@pytest.mark.ag_debugging_and_error_handling
def test_debugging_and_error_handling():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_try_except = any(
        isinstance(node, ast.Try) for node in ast.walk(tree)
    )
    assert has_try_except, "Program must use try/except for input validation and error handling."

    mod = _load_module()
    gradebook = {}
    # Out of range test
    try:
        mod.add_student("BadScore", 150, gradebook)
        # If no exception raised, verify it did not add the invalid score
        assert "BadScore" not in gradebook, "Scores > 100 must be rejected."
    except ValueError:
        pass


@pytest.mark.ag_testing_demonstration
def test_testing_demonstration():
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_asserts = any(
        isinstance(node, ast.Assert) for node in ast.walk(tree)
    )
    has_test_fn = any(
        isinstance(node, ast.FunctionDef) and "test" in node.name.lower()
        for node in ast.walk(tree)
    )
    assert has_asserts or has_test_fn or "test" in source.lower(), (
        "Script must include test cases demonstrating functionality."
    )


@pytest.mark.ag_code_quality
def test_code_quality():
    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "Class Report" in out or "Average" in out or "grade" in out.lower(), (
        "Script output must display class report."
    )

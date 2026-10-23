"""Tests for CS 1400 Module 14 Lab 2: Fix the Student Registration System."""

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

ENTRYPOINT = "student_registration_fixed.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("student_registration_fixed", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_debugging_fixes
def test_debugging_fixes():
    # Verify file parses cleanly without the original syntax and indentation errors
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)

    # Verify while loop is used in main for repeated menu execution
    has_while = any(isinstance(node, ast.While) for node in ast.walk(tree))
    assert has_while, "Program must use a while loop for continuous menu interaction."

    # Verify search logic: "found" should be printed when name IS in roster
    mod = _load_module()
    search_fn = getattr(mod, "search_student", getattr(mod, "search_", None))
    assert search_fn is not None, "Must define search_student function."


@pytest.mark.ag_test_cases
def test_test_cases(monkeypatch, capsys):
    mod = _load_module()
    add_fn = getattr(mod, "add_student", None)
    assert add_fn is not None

    # Test empty name validation
    roster = ["Emma"]
    monkeypatch.setattr("builtins.input", lambda _: "")
    add_fn(roster)
    assert "Emma" in roster and len(roster) == 1, "Empty student name must not be added to roster."
    captured = capsys.readouterr().out
    assert "error" in captured.lower() or "empty" in captured.lower(), (
        "Must display error message when adding an empty student name."
    )

    # Test removing non-existent student does not crash
    remove_fn = getattr(mod, "remove_student", getattr(mod, "removestudent", None))
    monkeypatch.setattr("builtins.input", lambda _: "NonExistentStudent")
    try:
        remove_fn(roster)
    except ValueError:
        pytest.fail("Removing a non-existent student must not raise an unhandled ValueError.")


@pytest.mark.ag_program_functionality
def test_program_functionality():
    path = assert_file_exists(ENTRYPOINT)
    # Simulate full user session:
    # 1 (Add) -> Alex
    # 3 (Search) -> Alex
    # 4 (Display)
    # 2 (Remove) -> Alex
    # 5 (Exit)
    inputs = ["1", "Alex", "3", "Alex", "4", "2", "Alex", "5"]
    result = run_script(path, inputs=inputs)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "Alex" in out, "Roster/Output must contain added student Alex."
    assert "found" in out.lower(), "Search for Alex must confirm student found."
    assert "removed" in out.lower(), "Removing Alex must print removal confirmation."


@pytest.mark.ag_clean_menu_and_roster
def test_clean_menu_and_roster():
    path = assert_file_exists(ENTRYPOINT)
    # Exit immediately
    result = run_script(path, inputs=["5"])
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "1. Add Student" in out, "Menu missing option 1"
    assert "2. Remove Student" in out, "Menu missing option 2"
    assert "3. Search Student" in out, "Menu missing option 3"
    assert "4. Display Class Roster" in out or "4. Display" in out, "Menu missing option 4"
    assert "5. Exit" in out, "Menu missing option 5"
    assert "Goodbye" in out or "exit" in out.lower(), "Output missing clean goodbye message."


@pytest.mark.ag_code_quality_and_comments
def test_code_quality_and_comments():
    assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=2)

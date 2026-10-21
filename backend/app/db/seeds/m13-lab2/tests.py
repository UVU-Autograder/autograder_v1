"""Tests for CS 1400 Module 13 Lab 2: Build a Student Record System Using Objects."""

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

ENTRYPOINT = "student_oop_records.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("student_oop_records", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_student_class_def
def test_student_class_def():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    classes = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]
    assert "Student" in classes, "Code must define a class named 'Student'."

    mod = _load_module()
    s = mod.Student("Carlos Vance", 1001, "Cybersecurity", 3.75)
    assert hasattr(s, "name"), "Student must have 'name' attribute."
    assert hasattr(s, "student_id"), "Student must have 'student_id' attribute."
    assert hasattr(s, "major"), "Student must have 'major' attribute."
    assert hasattr(s, "gpa"), "Student must have 'gpa' attribute."
    assert s.name == "Carlos Vance"
    assert s.gpa == 3.75


@pytest.mark.ag_init_and_str
def test_init_and_str():
    mod = _load_module()
    s = mod.Student("Diana Prince", 2045, "Mathematics", 4.0)
    rep = str(s)
    assert "Diana Prince" in rep, "__str__ output must include the student name."
    assert "2045" in rep, "__str__ output must include the student ID."
    assert "Mathematics" in rep, "__str__ output must include the major."
    assert "4.0" in rep or "4" in rep, "__str__ output must include the GPA."


@pytest.mark.ag_instance_methods
def test_instance_methods(capsys):
    mod = _load_module()
    s = mod.Student("Elena Ramos", 3050, "Physics", 3.20)
    assert hasattr(s, "update_gpa"), "Student must have update_gpa() method."
    assert hasattr(s, "change_major"), "Student must have change_major() method."
    assert hasattr(s, "display_summary"), "Student must have display_summary() method."

    s.update_gpa(3.80)
    assert s.gpa == 3.80, "update_gpa() must update the student's GPA."

    s.change_major("Astrophysics")
    assert s.major == "Astrophysics", "change_major() must update the student's major."

    s.display_summary()
    captured = capsys.readouterr().out
    assert "Elena Ramos" in captured, "display_summary() must print student name."
    assert "Astrophysics" in captured, "display_summary() must print updated major."


@pytest.mark.ag_object_list_loop
def test_object_list_loop():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_loop = any(
        isinstance(node, (ast.For, ast.While))
        for node in ast.walk(tree)
    )
    assert has_loop, "main() must iterate over the students list using a loop."

    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"
    out = result.stdout
    assert "Student Summary" in out or "Updating GPA" in out or "Changing Major" in out, (
        "Script output must display student records."
    )


@pytest.mark.ag_comments_and_clean_run
def test_comments_and_clean_run():
    path = assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)

    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

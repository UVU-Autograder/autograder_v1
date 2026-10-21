"""Tests for CS 1400 Module 7 Problem Solving Lab 1: Save Number Series."""

from __future__ import annotations

import ast
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

ENTRYPOINT = "save_number_series.py"


@pytest.mark.ag_print_message_and_clean_code
def test_print_message_and_clean_code():
    """Verify script exists, compiles with no syntax errors, and prints completion message."""
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

    res = run_script(ENTRYPOINT, inputs=["10", "100", "15"])
    assert res.returncode == 0, f"Script failed to run:\n{res.stderr}"
    assert "saved" in res.stdout.lower() or "number_series.txt" in res.stdout.lower(), (
        f"Expected final confirmation message in stdout. Got:\n{res.stdout}"
    )


@pytest.mark.ag_collect_inputs
def test_collect_inputs():
    """Verify script prompts user for start, end, and step."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 3, f"Expected 3 input() calls. Found {len(input_calls)}."


@pytest.mark.ag_for_loop_sequence
def test_for_loop_sequence():
    """Verify a for loop is used to generate the sequence."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
    assert has_for, "Script must use a 'for' loop to generate the numbers."


@pytest.mark.ag_stores_in_list
def test_stores_in_list():
    """Verify numbers are stored in a list before writing."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_list = any(isinstance(node, (ast.List, ast.ListComp)) for node in ast.walk(tree))
    assert has_list, "Script must store the numbers in a list."


@pytest.mark.ag_writes_to_file
def test_writes_to_file():
    """Verify numbers are written to number_series.txt with one number per line."""
    script_path = assert_file_exists(ENTRYPOINT)
    target_file = script_path.parent / "number_series.txt"
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT, inputs=["10", "100", "15"])
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"

    assert target_file.is_file(), f"number_series.txt was not created at {target_file}."
    lines = [line.strip() for line in target_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected = ["10", "25", "40", "55", "70", "85", "100"]
    assert lines == expected, f"Expected {expected} in number_series.txt, got {lines}"

    # Cleanup
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

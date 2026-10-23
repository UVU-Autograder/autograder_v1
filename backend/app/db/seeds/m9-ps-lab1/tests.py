"""Tests for CS 1400 Module 9 Problem Solving Lab 1: Log Line Analyzer."""

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

ENTRYPOINT = "log_analyzer.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify script includes comments or docstrings."""
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


@pytest.mark.ag_read_and_parse
def test_read_and_parse():
    """Verify script reads file and parses lines with split('|')."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert "|" in source and "split" in source, "Script must parse each line using .split('|')."


@pytest.mark.ag_count_severity
def test_count_severity():
    """Verify script uses a dictionary or counters to tally severity counts."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_dict = any(isinstance(n, (ast.Dict, ast.Subscript)) for n in ast.walk(tree))
    assert has_dict, "Script must use a dictionary to track severity counts."


@pytest.mark.ag_longest_message
def test_longest_message():
    """Verify script identifies the longest log message."""
    script_path = assert_file_exists(ENTRYPOINT)
    target_file = script_path.parent / "log_summary.txt"
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"

    assert target_file.is_file(), f"log_summary.txt was not created at {target_file}."
    content = target_file.read_text(encoding="utf-8")
    assert "Failed to connect to database" in content, (
        f"Expected 'Failed to connect to database' as longest message in {target_file}."
    )


@pytest.mark.ag_write_summary_file
def test_write_summary_file():
    """Verify script writes output in specified format to log_summary.txt."""
    script_path = assert_file_exists(ENTRYPOINT)
    target_file = script_path.parent / "log_summary.txt"
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"

    assert target_file.is_file(), f"log_summary.txt was not created at {target_file}."
    content = target_file.read_text(encoding="utf-8")
    assert "Log Summary" in content
    assert "INFO: 2" in content
    assert "WARNING: 1" in content
    assert "ERROR: 1" in content
    assert "Longest message:" in content

    # Cleanup
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

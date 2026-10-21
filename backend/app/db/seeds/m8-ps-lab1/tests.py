"""Tests for CS 1400 Module 8 Problem Solving Lab 1: Quote Sorter & Stats."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_file_exists,
        assert_no_syntax_errors,
        run_script,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_file_exists,
        assert_no_syntax_errors,
        run_script,
    )

ENTRYPOINT = "quote_sort_stats.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("quote_sort_stats", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["quote_sort_stats"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_user_defined_function
def test_user_defined_function():
    """Verify script defines at least one function."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert len(funcs) >= 1, "Script must use at least one user-defined function."


@pytest.mark.ag_parse_lines_tuples
def test_parse_lines_tuples():
    """Verify lines are parsed into tuples using split('|')."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert "|" in source and "split" in source, "Script must use .split('|') to parse quote lines."


@pytest.mark.ag_sort_quotes_logic
def test_sort_quotes_logic():
    """Verify sorting logic: longest quote first, with author ID tiebreaker."""
    mod = _load_module()
    sort_fn = getattr(mod, "sort_quotes", None)
    if sort_fn:
        sample = [
            ("Short", "B02"),
            ("Longest quote here in this test", "A01"),
            ("Short", "A01"),
        ]
        res = sort_fn(sample)
        assert res[0][0] == "Longest quote here in this test"
        assert res[1] == ("Short", "A01")
        assert res[2] == ("Short", "B02")


@pytest.mark.ag_average_quote_length
def test_average_quote_length():
    """Verify correct calculation of average quote length."""
    mod = _load_module()
    compute_fn = getattr(mod, "compute_stats", None)
    if compute_fn:
        sample = [
            ("1234567890", "A1"),  # 10
            ("12345678901234567890", "A2"),  # 20
        ]
        total, avg_len, most_words = compute_fn(sample)
        assert total == 2
        assert avg_len == 15


@pytest.mark.ag_quote_most_words
def test_quote_most_words():
    """Verify script identifies quote with most words and writes sorted_quotes.txt."""
    script_path = assert_file_exists(ENTRYPOINT)
    target_file = script_path.parent / "sorted_quotes.txt"
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"

    assert target_file.is_file(), f"sorted_quotes.txt was not created at {target_file}."
    content = target_file.read_text(encoding="utf-8")
    assert "Sorted Quotes" in content
    assert "Statistics" in content
    assert "Total quotes:" in content
    assert "Average quote length:" in content
    assert "Quote with most words:" in content

    # Cleanup
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

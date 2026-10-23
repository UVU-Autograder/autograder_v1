"""Tests for CS 1400 Module 9 Lab 1: Country Medal Analysis."""

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

ENTRYPOINT = "olympic_medal_analysis.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("olympic_medal_analysis", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["olympic_medal_analysis"] = mod
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


@pytest.mark.ag_nested_tuples_data
def test_nested_tuples_data():
    """Verify data structure uses nested tuples."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    tuples = [n for n in ast.walk(tree) if isinstance(n, ast.Tuple)]
    assert len(tuples) >= 4, "Script must define country data using nested tuples."


@pytest.mark.ag_define_analyze_medals
def test_define_analyze_medals():
    """Verify analyze_medals is defined and accepts data."""
    mod = _load_module()
    assert hasattr(mod, "analyze_medals"), "Script must define a function named 'analyze_medals(data)'."


@pytest.mark.ag_sorted_totals_list
def test_sorted_totals_list():
    """Verify analyze_medals returns correctly sorted totals list."""
    mod = _load_module()
    analyze_fn = getattr(mod, "analyze_medals")
    sample_data = [
        ("USA", (10, 8, 6)),
        ("China", (8, 10, 5)),
        ("Germany", (5, 3, 4)),
        ("Japan", (6, 5, 7)),
    ]
    res = analyze_fn(sample_data)
    expected = [("USA", 24), ("China", 23), ("Japan", 18), ("Germany", 12)]
    assert res == expected, f"Expected sorted totals {expected}, got {res}"


@pytest.mark.ag_most_gold_country
def test_most_gold_country():
    """Verify script correctly identifies USA as having the most gold medals."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout
    assert "most gold" in stdout.lower() or "gold medals" in stdout.lower(), (
        f"Expected country with most gold medals in output:\n{stdout}"
    )
    assert "USA" in stdout, f"Expected 'USA' identified as top gold medal winner:\n{stdout}"


@pytest.mark.ag_formatted_output
def test_formatted_output():
    """Verify formatted rankings are printed."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    stdout = res.stdout
    assert "24 medals" in stdout or "24" in stdout, f"Expected '24 medals' in stdout:\n{stdout}"
    assert "China" in stdout and "Japan" in stdout, f"Expected all countries printed in rankings:\n{stdout}"

"""Tests for CS 1400 Module 11 Lab 2: Product Rating Analyzer."""

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

ENTRYPOINT = "product_rating_analyzer.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("product_rating_analyzer", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)


@pytest.mark.ag_map_descriptions
def test_map_descriptions():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    map_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "map"
    ]
    assert map_calls, "Code must call map() to convert ratings to descriptions."
    has_lambda_arg = any(
        any(isinstance(arg, ast.Lambda) for arg in call.args)
        for call in map_calls
    )
    assert has_lambda_arg, "map() must take a lambda expression as an argument."


@pytest.mark.ag_filter_positive
def test_filter_positive():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    filter_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "filter"
    ]
    assert filter_calls, "Code must call filter() to extract positive ratings."
    has_lambda_arg = any(
        any(isinstance(arg, ast.Lambda) for arg in call.args)
        for call in filter_calls
    )
    assert has_lambda_arg, "filter() must take a lambda expression as an argument."


@pytest.mark.ag_reduce_average
def test_reduce_average():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    reduce_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and (
            getattr(node.func, "id", None) == "reduce"
            or getattr(node.func, "attr", None) == "reduce"
        )
    ]
    assert reduce_calls, "Code must call functools.reduce() to compute the total rating."
    has_lambda_arg = any(
        any(isinstance(arg, ast.Lambda) for arg in call.args)
        for call in reduce_calls
    )
    assert has_lambda_arg, "reduce() must take a lambda expression as an argument."


@pytest.mark.ag_comprehensions_defined
def test_comprehensions_defined():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fn_map = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    assert "generate_recommendation_flags" in fn_map, (
        "Must define function generate_recommendation_flags(ratings)."
    )
    flags_func = fn_map["generate_recommendation_flags"]
    assert any(isinstance(n, ast.ListComp) for n in ast.walk(flags_func)), (
        "generate_recommendation_flags must use a list comprehension."
    )

    assert "rating_summary" in fn_map, (
        "Must define function rating_summary(ratings)."
    )
    summary_func = fn_map["rating_summary"]
    assert any(isinstance(n, ast.DictComp) for n in ast.walk(summary_func)), (
        "rating_summary must use a dictionary comprehension."
    )

    mod = _load_module()
    sample = [5, 4, 3, 2, 1]
    flags = mod.generate_recommendation_flags(sample)
    assert flags == [True, True, False, False, False]
    summary = mod.rating_summary(sample)
    assert summary[5] == 1 and summary[1] == 1


@pytest.mark.ag_formatted_output
def test_formatted_output():
    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "Original Ratings:" in out, "Output missing 'Original Ratings:'"
    assert "Descriptions:" in out, "Output missing 'Descriptions:'"
    assert "Positive Ratings:" in out, "Output missing 'Positive Ratings:'"
    assert "3.45" in out or "3.55" in out, "Output missing average rating (expected 3.45)"
    assert "Recommendation Flags:" in out, "Output missing 'Recommendation Flags:'"
    assert "Rating Summary:" in out, "Output missing 'Rating Summary:'"
    assert "{1: 1, 2: 2, 3: 2, 4: 3, 5: 3}" in out or "1: 1" in out, (
        "Output missing rating summary counts dictionary"
    )

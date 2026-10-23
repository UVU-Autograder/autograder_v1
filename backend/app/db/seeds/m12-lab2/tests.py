"""Tests for CS 1400 Module 12 Lab 2: Optimize UVUnacci Using Memoization and Iteration."""

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

ENTRYPOINT = "uvunacci_optimized.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("uvunacci_optimized", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_baseline_recursive
def test_baseline_recursive():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fn_map = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "uvunacci_recursive" in fn_map, "Must define baseline uvunacci_recursive(n)."

    mod = _load_module()
    assert mod.uvunacci_recursive(0) == 0
    assert mod.uvunacci_recursive(1) == 1
    assert mod.uvunacci_recursive(2) == 2
    assert mod.uvunacci_recursive(5) == 11


@pytest.mark.ag_memoized_version
def test_memoized_version():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fn_map = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "uvunacci_memoized" in fn_map, "Must define uvunacci_memoized(n, memo_dict)."

    memo_func = fn_map["uvunacci_memoized"]
    # Check decorators: should NOT use lru_cache
    for dec in memo_func.decorator_list:
        dec_id = getattr(dec, "id", getattr(getattr(dec, "func", None), "id", ""))
        assert "lru_cache" not in dec_id, "uvunacci_memoized must use manual dictionary memoization, not @lru_cache."

    mod = _load_module()
    memo = {}
    val = mod.uvunacci_memoized(10, memo)
    assert val == 230, f"Expected uvunacci_memoized(10) == 230, got {val}"
    assert len(memo) > 0, "memo dictionary must store computed sub-results."


@pytest.mark.ag_iterative_version
def test_iterative_version():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fn_map = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "uvunacci_iterative" in fn_map, "Must define uvunacci_iterative(n)."

    iter_func = fn_map["uvunacci_iterative"]
    has_loop = any(
        isinstance(node, (ast.For, ast.While))
        for node in ast.walk(iter_func)
    )
    assert has_loop, "uvunacci_iterative must use a loop."

    mod = _load_module()
    assert mod.uvunacci_iterative(0) == 0
    assert mod.uvunacci_iterative(1) == 1
    assert mod.uvunacci_iterative(2) == 2
    assert mod.uvunacci_iterative(5) == 11
    assert mod.uvunacci_iterative(10) == 230
    assert mod.uvunacci_iterative(20) == 101902


@pytest.mark.ag_execution_timer
def test_execution_timer():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    time_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) in ("perf_counter", "time")
    ]
    assert time_calls, "Code must use time.perf_counter() or time.time() to measure execution times."


@pytest.mark.ag_printed_comparison
def test_printed_comparison():
    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "Recursive:" in out, "Output missing 'Recursive:'"
    assert "Memoized:" in out, "Output missing 'Memoized:'"
    assert "Iterative:" in out, "Output missing 'Iterative:'"
    assert "Summary:" in out or "summary" in out.lower(), "Output missing summary section"


@pytest.mark.ag_docstrings_comments
def test_docstrings_comments():
    assert_file_exists(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)

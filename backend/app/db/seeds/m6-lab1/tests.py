"""Tests for CS 1400 Module 6 Lab 1: Split a List into Even and Odd Numbers."""

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

ENTRYPOINT = "split_even_odd.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("split_even_odd", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["split_even_odd"] = mod
    spec.loader.exec_module(mod)
    return mod


def _get_split_func(mod):
    # Find any function that is not main
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj) and name not in ("main", "_load_module") and not name.startswith("__"):
            return obj
    pytest.fail("Could not find split function in module.")


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify code contains comments or docstrings."""
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


@pytest.mark.ag_define_function
def test_define_function():
    """Verify a function accepting a list is defined."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name != "main"]
    assert len(func_defs) >= 1, "Script must define a function to split numbers into even and odd lists."
    assert len(func_defs[0].args.args) >= 1, "Function must accept at least one argument (the list of integers)."


@pytest.mark.ag_odd_values_list
def test_odd_values_list():
    """Verify function extracts all odd values correctly without mutating original."""
    mod = _load_module()
    split_fn = _get_split_func(mod)
    orig = [1, 2, 3, 4, 5, 6, 7, 8]
    orig_copy = list(orig)
    res = split_fn(orig)
    assert orig == orig_copy, "Original list must not be modified."

    # Identify odd list from the return tuple
    if isinstance(res, (tuple, list)) and len(res) == 2:
        l1, l2 = list(res[0]), list(res[1])
        odd_list = l1 if (l1 and l1[0] % 2 != 0) else l2
        assert sorted(odd_list) == [1, 3, 5, 7], f"Expected odds [1, 3, 5, 7], got {odd_list}"
    else:
        pytest.fail(f"Expected function to return two lists, got: {res}")


@pytest.mark.ag_even_values_list
def test_even_values_list():
    """Verify function extracts all even values correctly without mutating original."""
    mod = _load_module()
    split_fn = _get_split_func(mod)
    orig = [1, 2, 3, 4, 5, 6, 7, 8]
    res = split_fn(orig)
    l1, l2 = list(res[0]), list(res[1])
    even_list = l1 if (l1 and l1[0] % 2 == 0) else l2
    assert sorted(even_list) == [2, 4, 6, 8], f"Expected evens [2, 4, 6, 8], got {even_list}"


@pytest.mark.ag_returns_and_prints
def test_returns_and_prints():
    """Verify output contains formatted original, odd, and even lists."""
    res = run_script(ENTRYPOINT, inputs=["1 2 3 4 5 6 7 8"])
    assert res.returncode == 0, f"Script failed on sample run:\n{res.stderr}"
    stdout = res.stdout
    assert "1, 2, 3, 4, 5, 6, 7, 8" in stdout or "1, 3, 5, 7" in stdout, (
        f"Expected formatted list output. Got:\n{stdout}"
    )
    assert "2, 4, 6, 8" in stdout, f"Expected even values [2, 4, 6, 8] in output. Got:\n{stdout}"

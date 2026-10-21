"""Tests for CS 1400 Module 6 Lab 2: Interleave Odd and Even Integer Lists."""

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

ENTRYPOINT = "interleave_lists.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("interleave_lists", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["interleave_lists"] = mod
    spec.loader.exec_module(mod)
    return mod


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


@pytest.mark.ag_create_predefined_lists
def test_create_predefined_lists():
    """Verify script defines odds and evens lists with specified elements."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    # Check for presence of [11, 33, 55] and [22, 44, 66, 88] in source or AST
    assert "11" in source and "33" in source and "55" in source, (
        "Script should create the predefined list odds = [11, 33, 55]."
    )
    assert "22" in source and "44" in source and "66" in source and "88" in source, (
        "Script should create the predefined list evens = [22, 44, 66, 88]."
    )


@pytest.mark.ag_define_interleave
def test_define_interleave():
    """Verify interleave(odds, evens) is defined with 2 parameters."""
    mod = _load_module()
    assert hasattr(mod, "interleave"), "Script must define a function named 'interleave(odds, evens)'."
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fdef = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "interleave"),
        None,
    )
    assert fdef is not None, "Function 'interleave' not found in AST."
    assert len(fdef.args.args) == 2, f"Expected 2 parameters for interleave, got {len(fdef.args.args)}."


@pytest.mark.ag_interleave_logic
def test_interleave_logic():
    """Verify interleave returns correctly interleaved list without modifying inputs."""
    mod = _load_module()
    interleave_fn = getattr(mod, "interleave")

    # Sample case
    o1 = [11, 33, 55]
    e1 = [22, 44, 66, 88]
    res1 = interleave_fn(o1, e1)
    assert res1 == [11, 22, 33, 44, 55, 66, 88], f"Expected [11, 22, 33, 44, 55, 66, 88], got {res1}"
    assert o1 == [11, 33, 55], "Original odds list must not be modified."
    assert e1 == [22, 44, 66, 88], "Original evens list must not be modified."

    # First list longer
    o2 = [1, 3, 5, 7]
    e2 = [2, 4]
    res2 = interleave_fn(o2, e2)
    assert res2 == [1, 2, 3, 4, 5, 7], f"Expected [1, 2, 3, 4, 5, 7], got {res2}"

    # Empty list edge case
    assert interleave_fn([], [2, 4]) == [2, 4]
    assert interleave_fn([1, 3], []) == [1, 3]


@pytest.mark.ag_prints_result
def test_prints_result():
    """Verify printed output contains the interleaved list result."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on execution:\n{res.stderr}"
    assert "11, 22, 33, 44, 55, 66, 88" in res.stdout, (
        f"Expected interleaved list in stdout. Got:\n{res.stdout}"
    )

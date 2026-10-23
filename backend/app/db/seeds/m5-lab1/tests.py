"""Tests for CS 1400 Module 5 Lab 1: Area of Multiple Regular Pentagons."""

from __future__ import annotations

import ast
import importlib.util
import math
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_file_exists,
        assert_has_comments,
        assert_no_syntax_errors,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_file_exists,
        assert_has_comments,
        assert_no_syntax_errors,
    )

ENTRYPOINT = "area_multiple_pentagons.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("area_multiple_pentagons", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["area_multiple_pentagons"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_docstring_or_comment
def test_docstring_or_comment():
    """Verify code includes docstrings or comments explaining the functions."""
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

    assert has_doc or has_comment, "Script must include an explanatory docstring or comment."


@pytest.mark.ag_define_area_multiple
def test_define_area_multiple():
    """Verify areaMultiplePentagons is defined with two parameters."""
    mod = _load_module()
    func = getattr(mod, "areaMultiplePentagons", None) or getattr(mod, "area_multiple_pentagons", None)
    assert func is not None, "Function 'areaMultiplePentagons(numPentagons, lengthSide)' must be defined."

    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fdef = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in ("areaMultiplePentagons", "area_multiple_pentagons")),
        None,
    )
    assert fdef is not None, "Function definition not found in AST."
    assert len(fdef.args.args) == 2, f"Expected 2 parameters for areaMultiplePentagons, got {len(fdef.args.args)}."


@pytest.mark.ag_calls_helper
def test_calls_helper():
    """Verify areaMultiplePentagons calls areaRegularPentagon instead of duplicating the formula."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fdef = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in ("areaMultiplePentagons", "area_multiple_pentagons")),
        None,
    )
    assert fdef is not None, "areaMultiplePentagons definition not found."

    calls = [
        n.func.id for n in ast.walk(fdef)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    called_helper = "areaRegularPentagon" in calls or "area_regular_pentagon" in calls
    assert called_helper, (
        "areaMultiplePentagons must call areaRegularPentagon to compute the area of one pentagon."
    )


@pytest.mark.ag_correct_total_area
def test_correct_total_area():
    """Verify correct area calculation for various input values."""
    mod = _load_module()
    single_func = getattr(mod, "areaRegularPentagon", None) or getattr(mod, "area_regular_pentagon", None)
    multiple_func = getattr(mod, "areaMultiplePentagons", None) or getattr(mod, "area_multiple_pentagons", None)
    assert single_func is not None, "areaRegularPentagon function not found."
    assert multiple_func is not None, "areaMultiplePentagons function not found."

    # Side = 7 -> ~84.30337
    single_7 = single_func(7)
    expected_single_7 = (5 * 49) / (4 * math.tan(math.pi / 5))
    assert single_7 == pytest.approx(expected_single_7, rel=1e-4)

    # 3 pentagons with side 7 -> ~252.9101
    assert multiple_func(3, 7) == pytest.approx(expected_single_7 * 3, rel=1e-4)

    # 5 pentagons with side 10
    expected_single_10 = (5 * 100) / (4 * math.tan(math.pi / 5))
    assert multiple_func(5, 10) == pytest.approx(expected_single_10 * 5, rel=1e-4)

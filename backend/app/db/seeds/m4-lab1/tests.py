"""Tests for CS 1400 Module 4 Lab 1: UVU Bookstore Discount Calculator."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        run_script,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        run_script,
    )

ENTRYPOINT = "uvu_discount.py"


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


@pytest.mark.ag_user_inputs
def test_user_inputs():
    """Verify script prompts for price and buyer type."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 2, f"Expected at least 2 input() calls. Found {len(input_calls)}."


@pytest.mark.ag_discount_rates
def test_discount_rates():
    """Verify conditional statements (if/elif) are used to handle buyer roles."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_if = any(isinstance(node, ast.If) for node in ast.walk(tree))
    assert has_if, "Script must use conditional statements (if/elif) to determine discount rates."


@pytest.mark.ag_final_price_calc
def test_final_price_calc():
    """Verify final prices for student (5%) and faculty (8%) discounts."""
    # Student discount: 120.00 -> 114.00
    res_s = run_script(ENTRYPOINT, inputs=["120.00", "s"])
    assert res_s.returncode == 0, f"Script failed with student input:\n{res_s.stderr}"
    assert "114.00" in res_s.stdout or "114" in res_s.stdout, (
        f"Expected final price $114.00 in output. Got:\n{res_s.stdout}"
    )

    # Faculty discount: 250 -> 230.00
    res_f = run_script(ENTRYPOINT, inputs=["250", "f"])
    assert res_f.returncode == 0, f"Script failed with faculty input:\n{res_f.stderr}"
    assert "230.00" in res_f.stdout or "230" in res_f.stdout, (
        f"Expected final price $230.00 in output. Got:\n{res_f.stdout}"
    )


@pytest.mark.ag_formatted_output
def test_formatted_output():
    """Verify output contains formatted final price with currency symbol."""
    res = run_script(ENTRYPOINT, inputs=["120.00", "s"])
    assert res.returncode == 0
    stdout = res.stdout
    assert "$" in stdout, f"Expected currency symbol '$' in output:\n{stdout}"
    assert "114.00" in stdout, f"Expected price formatted to two decimals (114.00) in output:\n{stdout}"

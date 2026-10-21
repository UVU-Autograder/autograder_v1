"""Tests for CS 1400 Module 6 Problem Solving Lab 1: Bacteria Growth."""

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

ENTRYPOINT = "bacteria_growth.py"


@pytest.mark.ag_clean_code
def test_clean_code():
    """Verify script exists, compiles with no syntax errors, and includes comments."""
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


@pytest.mark.ag_gather_inputs
def test_gather_inputs():
    """Verify script uses input() to gather starting population, rate, and hours."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 3, f"Expected at least 3 input() calls. Found {len(input_calls)}."


@pytest.mark.ag_track_with_list
def test_track_with_list():
    """Verify code creates and appends to a list to track population over time."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_list = any(isinstance(node, (ast.List, ast.ListComp)) for node in ast.walk(tree))
    assert has_list, "Script must use a list to store population history."


@pytest.mark.ag_loop_growth_logic
def test_loop_growth_logic():
    """Verify population calculations across simulation steps."""
    # Test sample run: 100 starting, 1.2 rate, 5 hours
    res = run_script(ENTRYPOINT, inputs=["100", "1.2", "5"])
    assert res.returncode == 0, f"Script failed on sample run:\n{res.stderr}"
    stdout = res.stdout
    assert "100" in stdout, f"Expected 100 in output:\n{stdout}"
    assert "120" in stdout, f"Expected 120 in output:\n{stdout}"
    assert "144" in stdout, f"Expected 144 in output:\n{stdout}"
    assert "172.8" in stdout, f"Expected 172.8 in output:\n{stdout}"
    assert "207.36" in stdout, f"Expected 207.36 in output:\n{stdout}"
    assert "248.83" in stdout or "248.8" in stdout, f"Expected ~248.83 in output:\n{stdout}"

    # Test another run: 50 starting, 2.0 rate, 3 hours
    res2 = run_script(ENTRYPOINT, inputs=["50", "2.0", "3"])
    assert res2.returncode == 0, f"Script failed on secondary run:\n{res2.stderr}"
    out2 = res2.stdout
    assert "50" in out2 and "100" in out2 and "200" in out2 and "400" in out2, (
        f"Expected doubling population sequence (50, 100, 200, 400). Got:\n{out2}"
    )


@pytest.mark.ag_decimal_output
def test_decimal_output():
    """Verify each hour is formatted clearly with 2 decimal places."""
    res = run_script(ENTRYPOINT, inputs=["100", "1.2", "5"])
    assert res.returncode == 0, f"Script failed:\n{res.stderr}"
    stdout = res.stdout
    assert "Hour 0:" in stdout or "hour 0" in stdout.lower(), (
        f"Expected 'Hour 0:' labeled in output:\n{stdout}"
    )
    assert "100.00" in stdout or "120.00" in stdout, (
        f"Expected 2 decimal formatting (e.g. 100.00, 120.00) in output:\n{stdout}"
    )

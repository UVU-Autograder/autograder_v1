"""Tests for CS 1400 Module 2 Lab 2: Compute Areas of Geometric Shapes."""

from __future__ import annotations

import ast
import math
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

ENTRYPOINT = "compute_areas.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_code_comment
def test_code_comment():
    """Verify script contains explanatory comments."""
    assert_has_comments(ENTRYPOINT, min_comments=1)


@pytest.mark.ag_user_input_prompts
def test_user_input_prompts():
    """Verify user input is prompted for radius, width, height, and base."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    input_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input"
    ]
    assert len(input_calls) >= 5, (
        f"Expected at least 5 input() prompts (radius, width, height, base, height). Found {len(input_calls)}."
    )


@pytest.mark.ag_formulas_and_math_pi
def test_formulas_and_math_pi():
    """Verify import math and use of math.pi."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    imports_math = any(
        (isinstance(node, ast.Import) and any(alias.name == "math" for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module == "math")
        for node in ast.walk(tree)
    )
    assert imports_math, "Script must import math module."
    assert "math.pi" in source or "pi" in source, "Script must use math.pi for the circle area formula."


@pytest.mark.ag_formatted_output
def test_formatted_output():
    """Verify output displays calculated areas with clear messages and formatting."""
    # Run with sample values: radius=3.5, width=10, height=4, base=6, height=8
    sample_inputs = ["3.5", "10", "4", "6", "8"]
    res = run_script(ENTRYPOINT, inputs=sample_inputs)
    assert res.returncode == 0, f"Script failed with inputs {sample_inputs}:\n{res.stderr}"
    stdout = res.stdout

    expected_circle = math.pi * (3.5 ** 2)
    assert f"{expected_circle:.2f}" in stdout or "38.48" in stdout, (
        f"Expected circle area approx 38.4845 in output. Got:\n{stdout}"
    )
    assert "40" in stdout, f"Expected rectangle area 40 in output. Got:\n{stdout}"
    assert "24" in stdout, f"Expected triangle area 24 in output. Got:\n{stdout}"

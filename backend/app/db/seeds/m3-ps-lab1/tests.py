"""Tests for CS 1400 Module 3 PS Lab 1: Character Shifter - Forward and Reverse."""

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

ENTRYPOINT = "character_shifter.py"


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)


@pytest.mark.ag_case_preservation
def test_case_preservation():
    """Verify function shifts uppercase and lowercase letters properly."""
    # Test uppercase forward
    res_upper = run_script(ENTRYPOINT, inputs=["A", "3", "forward"])
    assert res_upper.returncode == 0
    assert "D" in res_upper.stdout, f"Expected 'D' for 'A' shifted 3 forward. Got:\n{res_upper.stdout}"

    # Test lowercase forward
    res_lower = run_script(ENTRYPOINT, inputs=["x", "3", "forward"])
    assert res_lower.returncode == 0
    assert "a" in res_lower.stdout, f"Expected 'a' for 'x' shifted 3 forward (wrap). Got:\n{res_lower.stdout}"

    # Test backward direction
    res_back = run_script(ENTRYPOINT, inputs=["D", "3", "backward"])
    assert res_back.returncode == 0
    assert "A" in res_back.stdout, f"Expected 'A' for 'D' shifted 3 backward. Got:\n{res_back.stdout}"


@pytest.mark.ag_non_alpha_preserved
def test_non_alpha_preserved():
    """Verify non-alphabetic characters are preserved unchanged."""
    res_num = run_script(ENTRYPOINT, inputs=["5", "4", "forward"])
    assert res_num.returncode == 0
    assert "5" in res_num.stdout, f"Expected '5' to remain unchanged. Got:\n{res_num.stdout}"

    res_punct = run_script(ENTRYPOINT, inputs=["!", "2", "backward"])
    assert res_punct.returncode == 0
    assert "!" in res_punct.stdout, f"Expected '!' to remain unchanged. Got:\n{res_punct.stdout}"


@pytest.mark.ag_user_input_and_call
def test_user_input_and_call():
    """Verify script prompts for input and outputs result."""
    res = run_script(ENTRYPOINT, inputs=["A", "3", "forward"])
    assert res.returncode == 0
    stdout = res.stdout
    assert "shifted character:" in stdout.lower() or "d" in stdout.lower(), (
        f"Expected formatted output indicating shifted character. Got:\n{stdout}"
    )


@pytest.mark.ag_fstring_formatting
def test_fstring_formatting():
    """Verify use of f-strings or clean output formatting."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_fstring = any(
        isinstance(node, ast.JoinedStr)
        for node in ast.walk(tree)
    )
    assert has_fstring or "f\"" in source or "f'" in source or "%s" in source or ".format" in source, (
        "Script should format output using f-strings."
    )

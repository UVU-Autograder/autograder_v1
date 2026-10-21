"""Tests for CS 1400 Module 2 Project 1: Resource Allocation System - ARC-9 Dispenser Protocol."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        assert_valid_naming,
        find_assigned_variables,
        run_script,
    )
except ImportError:
    shared_path = Path(__file__).resolve().parents[1] / "shared"
    if str(shared_path) not in sys.path:
        sys.path.insert(0, str(shared_path))
    from cs1400_test_helpers import (
        assert_has_comments,
        assert_no_syntax_errors,
        assert_valid_naming,
        find_assigned_variables,
        run_script,
    )

ENTRYPOINT = "resource_allocator.py"


@pytest.mark.ag_clean_code
def test_clean_code():
    """Verify code compiles without syntax errors and contains explanatory comments."""
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=2)


@pytest.mark.ag_snake_case
def test_snake_case():
    """Verify all variable names follow snake_case or camelCase."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert len(assigned) >= 3, f"Expected multiple variables defined. Found: {list(assigned.keys())}"
    assert_valid_naming(assigned.keys())


@pytest.mark.ag_input_prompt
def test_input_prompt():
    """Verify input prompts match 'How many citizens:' and 'How many total units:'."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_citizens_prompt = "how many citizens" in source.lower()
    has_units_prompt = "how many total units" in source.lower() or "total units" in source.lower()
    assert has_citizens_prompt, "Input prompt should ask 'How many citizens:'."
    assert has_units_prompt, "Input prompt should ask 'How many total units:'."


@pytest.mark.ag_output_pattern
def test_output_pattern():
    """Verify output contains exact label patterns: Mira's share:, Tov's share:, Crew's share:."""
    res = run_script(ENTRYPOINT, inputs=["20", "1000"])
    assert res.returncode == 0, f"Script crashed:\n{res.stderr}"
    stdout = res.stdout.lower()
    assert "mira's share:" in stdout, f"Missing 'Mira's share:' in output:\n{res.stdout}"
    assert "tov's share:" in stdout, f"Missing 'Tov's share:' in output:\n{res.stdout}"
    assert "crew's share:" in stdout, f"Missing 'Crew's share:' in output:\n{res.stdout}"


@pytest.mark.ag_rounded_values
def test_rounded_values():
    """Verify output values are rounded to 2 decimal places."""
    res = run_script(ENTRYPOINT, inputs=["20", "1000"])
    assert res.returncode == 0
    decimals = re.findall(r"\d+\.\d{2}", res.stdout)
    assert len(decimals) >= 3, (
        f"Expected at least 3 values formatted to 2 decimal places. Found {decimals} in:\n{res.stdout}"
    )


@pytest.mark.ag_fstring_formatting
def test_fstring_formatting():
    """Verify use of f-strings or format specifiers for formatting display."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_fstring = any(
        isinstance(node, ast.JoinedStr)
        for node in ast.walk(tree)
    )
    assert has_fstring or ".2f" in source or "%0.2f" in source, "Code must format units using f-strings with 2 decimals."


@pytest.mark.ag_calculation_accuracy
def test_calculation_accuracy():
    """Verify calculation accuracy for the sample input run (20 citizens, 1000 units)."""
    res = run_script(ENTRYPOINT, inputs=["20", "1000"])
    assert res.returncode == 0, f"Script failed on inputs 20, 1000:\n{res.stderr}"
    stdout = res.stdout
    assert "159.60" in stdout, f"Expected Mira's share 159.60 in output:\n{stdout}"
    assert "127.15" in stdout or "127.16" in stdout, (
        f"Expected Tov's share 127.15 (or 127.16 with float precision) in output:\n{stdout}"
    )
    assert "39.62" in stdout, f"Expected Crew's share 39.62 in output:\n{stdout}"


@pytest.mark.ag_unknown_input
def test_unknown_input():
    """Verify calculation accuracy for an unknown input vector (50 citizens, 5000 units)."""
    res = run_script(ENTRYPOINT, inputs=["50", "5000"])
    assert res.returncode == 0, f"Script failed on inputs 50, 5000:\n{res.stderr}"
    stdout = res.stdout
    assert "706.48" in stdout, f"Expected Mira's share 706.48 for 50 citizens / 5000 units in output:\n{stdout}"
    assert "539.92" in stdout, f"Expected Tov's share 539.92 for 50 citizens / 5000 units in output:\n{stdout}"
    assert "78.20" in stdout, f"Expected Crew's share 78.20 for 50 citizens / 5000 units in output:\n{stdout}"

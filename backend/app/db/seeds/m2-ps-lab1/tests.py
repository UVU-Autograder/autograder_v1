"""Tests for CS 1400 Module 2 PS Lab 1: Festival Resource Distribution - Percent Allocations."""

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

ENTRYPOINT = "festival_distribution.py"


@pytest.mark.ag_naming_and_comments
def test_naming_and_comments():
    """Verify code includes comments and adheres to naming conventions."""
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert len(assigned) >= 3, f"Expected multiple variables defined. Found: {list(assigned.keys())}"
    assert_valid_naming(assigned.keys())


@pytest.mark.ag_zerin_share_calc
def test_zerin_share_calc():
    """Verify calculation of Zerin's share across test inputs."""
    # Case 1: 25 colonists, 1200 food -> Zerin: 202.66
    res1 = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res1.returncode == 0, f"Script failed on 25, 1200:\n{res1.stderr}"
    assert "202.66" in res1.stdout, f"Expected Zerin's share 202.66 in output:\n{res1.stdout}"

    # Case 2: 10 colonists, 600 food -> Zerin: 130.84
    res2 = run_script(ENTRYPOINT, inputs=["10", "600"])
    assert res2.returncode == 0, f"Script failed on 10, 600:\n{res2.stderr}"
    assert "130.84" in res2.stdout, f"Expected Zerin's share 130.84 in output:\n{res2.stdout}"


@pytest.mark.ag_lyra_share_calc
def test_lyra_share_calc():
    """Verify calculation of Lyra's share across test inputs."""
    # Case 1: 25 colonists, 1200 food -> Lyra: 131.16
    res1 = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res1.returncode == 0
    assert "131.16" in res1.stdout, f"Expected Lyra's share 131.16 in output:\n{res1.stdout}"

    # Case 2: 10 colonists, 600 food -> Lyra: 94.44
    res2 = run_script(ENTRYPOINT, inputs=["10", "600"])
    assert res2.returncode == 0
    assert "94.44" in res2.stdout, f"Expected Lyra's share 94.44 in output:\n{res2.stdout}"


@pytest.mark.ag_equal_distribution
def test_equal_distribution():
    """Verify even distribution among colonists."""
    # Case 1: 25 colonists, 1200 food -> Colonist: 37.66
    res1 = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res1.returncode == 0
    assert "37.66" in res1.stdout, f"Expected colonist share 37.66 in output:\n{res1.stdout}"

    # Case 2: 10 colonists, 600 food -> Colonist: 46.84
    res2 = run_script(ENTRYPOINT, inputs=["10", "600"])
    assert res2.returncode == 0
    assert "46.84" in res2.stdout, f"Expected colonist share 46.84 in output:\n{res2.stdout}"


@pytest.mark.ag_fstring_formatting
def test_fstring_formatting():
    """Verify outputs are formatted with 2 decimal places using f-strings or format specifiers."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_fstring = any(
        isinstance(node, ast.JoinedStr)
        for node in ast.walk(tree)
    )
    assert has_fstring or ".2f" in source or "%0.2f" in source, "Script must use f-strings formatted to 2 decimal places."

    res = run_script(ENTRYPOINT, inputs=["25", "1200"])
    assert res.returncode == 0
    # Verify decimal formatting pattern in output
    decimals = re.findall(r"\d+\.\d{2}", res.stdout)
    assert len(decimals) >= 3, f"Expected at least 3 numbers formatted to 2 decimal places. Found {decimals}."

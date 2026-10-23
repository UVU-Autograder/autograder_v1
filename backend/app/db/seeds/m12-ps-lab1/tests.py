"""Tests for CS 1400 Module 12 PS Lab 1: Weighted Movement and Frequency Counter."""

from __future__ import annotations

import ast
import re
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

ENTRYPOINT = "sophie_biased_walk.py"


@pytest.mark.ag_random_choices_weighted
def test_random_choices_weighted():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    choices_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and (
            getattr(node.func, "attr", None) == "choices"
            or getattr(node.func, "id", None) == "choices"
        )
    ]
    assert choices_calls, "Code must call random.choices() for weighted movement selection."
    has_weights = any(
        any(kw.arg == "weights" for kw in call.keywords) or len(call.args) >= 2
        for call in choices_calls
    )
    assert has_weights, "random.choices() must include directional weights."


@pytest.mark.ag_track_position_steps
def test_track_position_steps():
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_loop = any(
        isinstance(node, (ast.For, ast.While))
        for node in ast.walk(tree)
    )
    assert has_loop, "Code must use a loop to simulate the 200 movement steps."
    assert "200" in source, "Simulation must run for 200 steps."


@pytest.mark.ag_direction_counts
def test_direction_counts():
    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    # Parse counts for Up, Down, Left, Right
    up_match = re.search(r"Up:\s*(\d+)", out, re.IGNORECASE)
    down_match = re.search(r"Down:\s*(\d+)", out, re.IGNORECASE)
    left_match = re.search(r"Left:\s*(\d+)", out, re.IGNORECASE)
    right_match = re.search(r"Right:\s*(\d+)", out, re.IGNORECASE)

    assert up_match and down_match and left_match and right_match, (
        "Output must report counts for Up, Down, Left, and Right directions."
    )
    total_steps = (
        int(up_match.group(1))
        + int(down_match.group(1))
        + int(left_match.group(1))
        + int(right_match.group(1))
    )
    assert total_steps == 200, f"Total counted steps must equal 200, got {total_steps}."
    # Up should be the most frequent due to 50% weighting
    assert int(up_match.group(1)) > int(down_match.group(1)), (
        "Up should occur more frequently than Down given the 50% weight bias."
    )


@pytest.mark.ag_display_final_stats
def test_display_final_stats():
    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "Final position:" in out, "Output missing 'Final position:' label"
    assert "Direction counts:" in out or "counts:" in out.lower(), "Output missing direction counts header"


@pytest.mark.ag_comments_and_organization
def test_comments_and_organization():
    assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)

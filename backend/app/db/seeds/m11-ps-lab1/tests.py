"""Tests for CS 1400 Module 11 PS Lab 1: Simulate Random Grid Movement."""

from __future__ import annotations

import ast
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

ENTRYPOINT = "random_walk_basic.py"


@pytest.mark.ag_random_choice_directions
def test_random_choice_directions():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and (
            getattr(node.func, "attr", None) == "choice"
            or getattr(node.func, "id", None) == "choice"
        )
    ]
    assert calls, "Code must call random.choice() to pick movement direction."


@pytest.mark.ag_track_positions_list
def test_track_positions_list():
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    # Check that positions list contains (0, 0)
    assert "(0, 0)" in source or "(0,0)" in source, (
        "Astronaut must start at coordinate (0, 0)."
    )
    # AST check: look for list append or list addition of tuples
    has_tuple_in_tree = any(
        isinstance(node, ast.Tuple) for node in ast.walk(tree)
    )
    assert has_tuple_in_tree, "Positions must be stored as coordinate tuples."


@pytest.mark.ag_loop_updates_position
def test_loop_updates_position():
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_loop = any(
        isinstance(node, (ast.For, ast.While)) for node in ast.walk(tree)
    )
    assert has_loop, "Code must use a loop to simulate the walk."
    assert "100" in source, "Simulation must run for 100 steps."


@pytest.mark.ag_matplotlib_plot
def test_matplotlib_plot():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    imports_mpl = any(
        (isinstance(node, ast.Import) and any("matplotlib" in alias.name for alias in node.names))
        or (isinstance(node, ast.ImportFrom) and node.module and "matplotlib" in node.module)
        for node in ast.walk(tree)
    )
    assert imports_mpl, "Program must import matplotlib to plot the walk."

    calls_plot = any(
        isinstance(node, ast.Call) and (
            getattr(node.func, "attr", None) in ("plot", "scatter", "show", "savefig")
        )
        for node in ast.walk(tree)
    )
    assert calls_plot, "Program must call matplotlib functions to plot the path."


@pytest.mark.ag_comment_and_syntax
def test_comment_and_syntax():
    path = assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)

    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"
    assert "Final position" in result.stdout or "100" in result.stdout, (
        "Script output must print the final position."
    )

    # Clean up any image file generated during the test run
    img = path.parent / "random_walk.png"
    if img.exists():
        try:
            img.unlink()
        except OSError:
            pass

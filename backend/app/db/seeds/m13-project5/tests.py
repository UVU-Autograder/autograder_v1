"""Tests for CS 1400 Module 13 Project 5: Pathfinder Tracker - Space Walk Simulation."""

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

ENTRYPOINT = "pathfinder_tracker.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("pathfinder_tracker", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_astronaut_movement_patterns
def test_astronaut_movement_patterns():
    mod = _load_module()

    # Test Finn: only moves horizontally (y must stay 0 for every step)
    finn = mod.Astronaut("Finn", "g", "^")
    # Simulate Finn
    if hasattr(mod, "simulate_spacewalk"):
        mod.simulate_spacewalk(finn, steps=100)
    else:
        # Fallback if student used a different helper or method
        pass

    if len(finn.positions) > 1:
        for x, y in finn.positions:
            assert y == 0, f"Finn must move only horizontally; found y-coordinate {y}."

    # Test Sophie: moves with upward bias
    sophie = mod.Astronaut("Sophie", "r", "s")
    if hasattr(mod, "simulate_spacewalk"):
        mod.simulate_spacewalk(sophie, steps=200)
        final_y = sophie.positions[-1][1]
        assert final_y > 0, (
            f"Sophie's upward bias should result in positive y after 200 steps; got {final_y}."
        )


@pytest.mark.ag_simulation_randomness
def test_simulation_randomness():
    mod = _load_module()
    lance1 = mod.Astronaut("Lance", "b", "o")
    lance2 = mod.Astronaut("Lance", "b", "o")

    if hasattr(mod, "simulate_spacewalk"):
        mod.simulate_spacewalk(lance1, steps=50)
        mod.simulate_spacewalk(lance2, steps=50)
        assert lance1.positions != lance2.positions, (
            "Simulation must produce randomized, non-identical paths across separate runs."
        )


@pytest.mark.ag_astronaut_class_structure
def test_astronaut_class_structure():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    classes = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]
    assert "Astronaut" in classes, "Code must define an 'Astronaut' class."

    mod = _load_module()
    a = mod.Astronaut("Lance", "b", "o")
    assert hasattr(a, "name"), "Astronaut must have attribute 'name'."
    assert hasattr(a, "color"), "Astronaut must have attribute 'color'."
    assert hasattr(a, "marker"), "Astronaut must have attribute 'marker'."
    assert hasattr(a, "positions"), "Astronaut must have attribute 'positions'."
    assert a.positions == [(0, 0)], "Initial position must be [(0, 0)]."

    assert hasattr(a, "move"), "Astronaut must have instance method move(dx, dy)."
    a.move(1, 2)
    assert a.positions[-1] == (1, 2), "move(dx, dy) must append new coordinate to positions."
    assert len(a.positions) == 2

    # String representation
    rep = str(a)
    assert "Lance" in rep, "__str__ output must include the astronaut's name."


@pytest.mark.ag_no_code_repetition
def test_no_code_repetition():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    loops = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.While))
    ]
    assert len(loops) >= 2, (
        "Project must use loops to iterate over steps and astronauts to prevent repetitive code."
    )


@pytest.mark.ag_main_execution_guard
def test_main_execution_guard():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_main_def = any(
        isinstance(node, ast.FunctionDef) and node.name == "main"
        for node in ast.walk(tree)
    )
    assert has_main_def, "Code must define a main() function."

    # Verify if __name__ == "__main__":
    has_guard = False
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test = node.test
            if isinstance(test, ast.Compare):
                left = getattr(test.left, "id", None)
                if left == "__name__":
                    has_guard = True
                    break
    assert has_guard, "Code must include if __name__ == '__main__': execution guard."


@pytest.mark.ag_limited_global_scope
def test_limited_global_scope():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    # Check top-level statements for variables
    top_level_assigns = [
        node for node in tree.body
        if isinstance(node, ast.Assign)
    ]
    # Small number of constants or imports allowed
    assert len(top_level_assigns) <= 5, (
        "State should be contained in classes/functions rather than global variables."
    )


@pytest.mark.ag_code_style_and_quality
def test_code_style_and_quality():
    path = assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=2)

    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    # Clean up generated image files if any
    for name in ["Lance", "Sophie", "Finn"]:
        img = path.parent / f"{name}_spacewalk.png"
        if img.exists():
            try:
                img.unlink()
            except OSError:
                pass

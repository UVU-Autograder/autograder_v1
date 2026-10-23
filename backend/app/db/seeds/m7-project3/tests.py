"""Tests for CS 1400 Module 7 Project 3: Gaia Viability Estimator."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
        assert_file_exists,
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
        assert_file_exists,
        assert_no_syntax_errors,
        assert_valid_naming,
        find_assigned_variables,
        run_script,
    )

ENTRYPOINT = "gaia_growth_simulator.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("gaia_growth_simulator", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gaia_growth_simulator"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_code_file_name
def test_code_file_name():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_main_conditional
def test_main_conditional():
    """Verify program contains a main function with conditional execution guard."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree))
    assert has_main, "Script must define a 'main()' function."
    assert "__name__" in source and "__main__" in source, (
        "Script must include conditional execution guard: if __name__ == '__main__':"
    )


@pytest.mark.ag_style_snake_case
def test_style_snake_case():
    """Verify variable and function names follow snake_case or camelCase."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert_valid_naming(assigned.keys())


@pytest.mark.ag_equation_function
def test_equation_function():
    """Verify the logistic equation is defined in its own function."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fn_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name != "main"]
    assert len(fn_defs) >= 1, "Script must define functions for the logistic model."

    # Test numerical accuracy of the logistic equation function
    mod = _load_module()
    equation_fn = None
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj) and "pop" in name.lower() or "equation" in name.lower() or "logistic" in name.lower():
            equation_fn = obj
            break

    if equation_fn:
        # P_1 = 2.5 * 0.1 * (1 - 0.1) = 0.225
        assert equation_fn(0.1, 2.5) == pytest.approx(0.225, rel=1e-3)


@pytest.mark.ag_cli_args_parsing
def test_cli_args_parsing():
    """Verify script parses command line arguments using sys.argv."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert "sys.argv" in source or "argv" in source, "Script must use sys.argv to parse command-line arguments."


@pytest.mark.ag_list_accumulator
def test_list_accumulator():
    """Verify code uses a list to accumulate population values over time."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_list = any(isinstance(node, (ast.List, ast.ListComp)) for node in ast.walk(tree))
    assert has_list, "Script must use a list to capture simulation values."


@pytest.mark.ag_range_validation
def test_range_validation():
    """Verify script validates input parameter ranges."""
    script_path = assert_file_exists(ENTRYPOINT)
    out_file = script_path.parent / "invalid_test.txt"

    # Out of range p0 (1.5)
    res_bad_p0 = run_script(ENTRYPOINT, args=["1.5", "2.5", "10", str(out_file)])
    assert res_bad_p0.returncode != 0 or "error" in res_bad_p0.stdout.lower(), (
        "Script must reject initial population outside (0, 1)."
    )

    # Out of range rate (5.0)
    res_bad_r = run_script(ENTRYPOINT, args=["0.2", "5.0", "10", str(out_file)])
    assert res_bad_r.returncode != 0 or "error" in res_bad_r.stdout.lower(), (
        "Script must reject growth rate outside (0, 4)."
    )

    if out_file.exists():
        try:
            out_file.unlink()
        except OSError:
            pass


@pytest.mark.ag_loops_and_functions
def test_loops_and_functions():
    """Verify code uses loops, conditionals, and functions."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_loop = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))
    has_if = any(isinstance(n, ast.If) for n in ast.walk(tree))
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    assert has_loop, "Script must use a loop to simulate steps."
    assert has_if, "Script must use conditional statements for validation."
    assert len(funcs) >= 2, "Script must be modularized into multiple functions."


@pytest.mark.ag_output_to_file
def test_output_to_file():
    """Verify simulation writes results formatted to 3 decimal places to specified output file."""
    script_path = assert_file_exists(ENTRYPOINT)
    out_file = script_path.parent / "output.txt"
    if out_file.exists():
        try:
            out_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT, args=["0.1", "2.5", "20", "output.txt"])
    assert res.returncode == 0, f"Script failed with sample args:\n{res.stderr}"

    assert out_file.is_file(), f"Output file was not created at {out_file}."
    lines = [line.strip() for line in out_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 21, f"Expected 21 lines (step 0 through 20), got {len(lines)}"

    # Check first few entries:
    # 0   0.100
    # 1   0.225
    # 2   0.436
    assert "0.100" in lines[0], f"Expected 0.100 at step 0, got: {lines[0]}"
    assert "0.225" in lines[1], f"Expected 0.225 at step 1, got: {lines[1]}"
    assert "0.436" in lines[2], f"Expected 0.436 at step 2, got: {lines[2]}"

    if out_file.exists():
        try:
            out_file.unlink()
        except OSError:
            pass


@pytest.mark.ag_unknown_input
def test_unknown_input():
    """Verify simulation works for different parameter combinations."""
    script_path = assert_file_exists(ENTRYPOINT)
    custom_out = script_path.parent / "custom_output.txt"
    if custom_out.exists():
        try:
            custom_out.unlink()
        except OSError:
            pass

    # p0 = 0.2, rate = 2.0, steps = 5
    # step 0: 0.200
    # step 1: 2.0 * 0.2 * 0.8 = 0.320
    # step 2: 2.0 * 0.32 * 0.68 = 0.4352 -> 0.435
    res = run_script(ENTRYPOINT, args=["0.2", "2.0", "5", "custom_output.txt"])
    assert res.returncode == 0, f"Script failed with custom parameters:\n{res.stderr}"

    assert custom_out.is_file(), f"Output file was not created at {custom_out}."
    lines = [line.strip() for line in custom_out.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 6, f"Expected 6 lines (step 0 through 5), got {len(lines)}"
    assert "0.200" in lines[0]
    assert "0.320" in lines[1]
    assert "0.435" in lines[2]

    if custom_out.exists():
        try:
            custom_out.unlink()
        except OSError:
            pass

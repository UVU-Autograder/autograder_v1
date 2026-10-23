"""Tests for CS 1400 Module 12 Lab 1: UVUnacci Series Using Recursion."""

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

ENTRYPOINT = "uvunacci_recursive.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("uvunacci_recursive", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_recursive_function_logic
def test_recursive_function_logic():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    fn_map = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    assert "uvunacci_recursive" in fn_map, "Must define function uvunacci_recursive(n)."

    # Verify recursion: function calls itself inside its body
    func_node = fn_map["uvunacci_recursive"]
    recursive_calls = [
        call for call in ast.walk(func_node)
        if isinstance(call, ast.Call) and getattr(call.func, "id", None) == "uvunacci_recursive"
    ]
    assert len(recursive_calls) >= 2, (
        "uvunacci_recursive must recursively call itself to compute the sequence."
    )

    mod = _load_module()
    # Test base cases and initial terms
    assert mod.uvunacci_recursive(0) == 0, "uvunacci_recursive(0) must equal 0"
    assert mod.uvunacci_recursive(1) == 1, "uvunacci_recursive(1) must equal 1"
    assert mod.uvunacci_recursive(2) == 2, "uvunacci_recursive(2) must equal 2"
    assert mod.uvunacci_recursive(3) == 3, "uvunacci_recursive(3) must equal 3 (0 + 1 + 2)"
    assert mod.uvunacci_recursive(4) == 6, "uvunacci_recursive(4) must equal 6 (1 + 2 + 3)"
    assert mod.uvunacci_recursive(5) == 11, "uvunacci_recursive(5) must equal 11 (2 + 3 + 6)"


@pytest.mark.ag_sequence_generation
def test_sequence_generation():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_loop_or_comp = any(
        isinstance(node, (ast.For, ast.ListComp))
        for node in ast.walk(tree)
    )
    assert has_loop_or_comp, (
        "Main code must use a loop or list comprehension to generate the sequence."
    )


@pytest.mark.ag_correct_output_terms
def test_correct_output_terms():
    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

    out = result.stdout
    assert "UVUnacci" in out or "[" in out, "Output must print the sequence terms"
    # Check that sample terms are in output
    for term in ["0, 1, 2, 3, 6, 11", "20", "37"]:
        assert term in out or ("0" in out and "11" in out and "20" in out), (
            f"Expected term {term} in output sequence."
        )


@pytest.mark.ag_comments_and_docstrings
def test_comments_and_docstrings():
    assert_file_exists(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)

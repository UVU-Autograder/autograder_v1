"""Tests for CS 1400 Module 5 Project 2: Lost Language Decoder."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

try:
    from cs1400_test_helpers import (
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
        assert_no_syntax_errors,
        assert_valid_naming,
        find_assigned_variables,
        run_script,
    )

ENTRYPOINT = "lost_language_decoder.py"


@pytest.mark.ag_sample_cases
def test_sample_cases():
    """Verify string transformation on the sample cases from the specification."""
    # Example 1: Encoding "attack at dawn", shift 3 -> "dwwdfn dw gdzq"
    res1 = run_script(ENTRYPOINT, inputs=["attack at dawn", "3", "e"])
    assert res1.returncode == 0, f"Example 1 failed:\n{res1.stderr}"
    assert "dwwdfn dw gdzq" in res1.stdout, f"Expected 'dwwdfn dw gdzq' in output. Got:\n{res1.stdout}"

    # Example 2: Decoding "dwwdfn dw gdzq", shift 3 -> "attack at dawn"
    res2 = run_script(ENTRYPOINT, inputs=["dwwdfn dw gdzq", "3", "d"])
    assert res2.returncode == 0, f"Example 2 failed:\n{res2.stderr}"
    assert "attack at dawn" in res2.stdout, f"Expected 'attack at dawn' in output. Got:\n{res2.stdout}"

    # Example 3: Non-alphabet characters "secure data 123!", shift 4 -> "wigyvi hexe 123!"
    res3 = run_script(ENTRYPOINT, inputs=["secure data 123!", "4", "e"])
    assert res3.returncode == 0, f"Example 3 failed:\n{res3.stderr}"
    assert "wigyvi hexe 123!" in res3.stdout, f"Expected 'wigyvi hexe 123!' in output. Got:\n{res3.stdout}"


@pytest.mark.ag_unknown_cases
def test_unknown_cases():
    """Verify transformation on unknown texts, mixed-case, and large shift values."""
    # Mixed case with shift > 26 (shift 29 is equivalent to shift 3)
    res_enc = run_script(ENTRYPOINT, inputs=["Hello, World! 2026", "29", "e"])
    assert res_enc.returncode == 0, f"Unknown test encode failed:\n{res_enc.stderr}"
    # H -> K, e -> h, l -> o, o -> r, W -> Z, o -> r, r -> u, l -> o, d -> g
    assert "Khoor, Zruog! 2026" in res_enc.stdout, (
        f"Expected 'Khoor, Zruog! 2026' in output. Got:\n{res_enc.stdout}"
    )

    # Decode mixed case
    res_dec = run_script(ENTRYPOINT, inputs=["Khoor, Zruog! 2026", "29", "d"])
    assert res_dec.returncode == 0, f"Unknown test decode failed:\n{res_dec.stderr}"
    assert "Hello, World! 2026" in res_dec.stdout, (
        f"Expected 'Hello, World! 2026' in output. Got:\n{res_dec.stdout}"
    )


@pytest.mark.ag_for_loop
def test_for_loop():
    """Verify code uses at least one for loop."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
    assert has_for, "Script must use at least one 'for' loop."


@pytest.mark.ag_while_loop
def test_while_loop():
    """Verify code uses at least one while loop."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_while = any(isinstance(node, ast.While) for node in ast.walk(tree))
    assert has_while, "Script must use at least one 'while' loop."


@pytest.mark.ag_if_statement
def test_if_statement():
    """Verify code contains if statements."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_if = any(isinstance(node, ast.If) for node in ast.walk(tree))
    assert has_if, "Script must use 'if' statements to handle cipher logic."


@pytest.mark.ag_encode_decode_functions
def test_encode_decode_functions():
    """Verify dedicated functions exist for encoding and decoding."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    functions = [node.name.lower() for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    has_encode = any("encode" in name for name in functions)
    has_decode = any("decode" in name for name in functions)
    assert has_encode and has_decode, (
        f"Script must define separate functions for encoding and decoding. Found functions: {functions}"
    )


@pytest.mark.ag_main_conditional
def test_main_conditional():
    """Verify program contains a main function with conditional execution (if __name__ == '__main__':)."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_main_def = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree))
    assert has_main_def, "Script must define a 'main()' function."

    assert "__name__" in source and "__main__" in source, (
        "Script must include conditional execution guard: if __name__ == '__main__':"
    )


@pytest.mark.ag_snake_or_camel_case
def test_snake_or_camel_case():
    """Verify all variable names follow snake_case or camelCase."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert len(assigned) >= 2, f"Expected multiple variables defined. Found: {list(assigned.keys())}"
    assert_valid_naming(assigned.keys())

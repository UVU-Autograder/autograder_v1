"""Tests for CS 1400 Module 4 Problem Solving Lab 1: Word Encoder."""

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

ENTRYPOINT = "simple_word_encoder.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("simple_word_encoder", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["simple_word_encoder"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_shift_comment
def test_shift_comment():
    """Verify code includes comments or docstrings explaining the shift."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_doc = any(
        isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
        for node in ast.walk(tree)
    )
    try:
        assert_has_comments(ENTRYPOINT, min_comments=1)
        has_comment = True
    except AssertionError:
        has_comment = False

    assert has_doc or has_comment, "Code must include at least one comment or docstring explaining the shift."


@pytest.mark.ag_shift_letter_logic
def test_shift_letter_logic():
    """Verify shift_letter() correctly shifts characters and wraps around 'z' to 'a'."""
    mod = _load_module()
    assert hasattr(mod, "shift_letter"), "Script must define a function named 'shift_letter(char, shift)'."
    shift_letter = getattr(mod, "shift_letter")

    # Basic shift
    assert shift_letter("a", 1) == "b", f"Expected shift_letter('a', 1) == 'b', got {shift_letter('a', 1)!r}"
    assert shift_letter("a", 2) == "c", f"Expected shift_letter('a', 2) == 'c', got {shift_letter('a', 2)!r}"

    # Wrap around tests
    assert shift_letter("z", 1) == "a", f"Expected shift_letter('z', 1) == 'a', got {shift_letter('z', 1)!r}"
    assert shift_letter("y", 3) == "b", f"Expected shift_letter('y', 3) == 'b', got {shift_letter('y', 3)!r}"
    assert shift_letter("w", 5) == "b", f"Expected shift_letter('w', 5) == 'b', got {shift_letter('w', 5)!r}"


@pytest.mark.ag_encode_word_logic
def test_encode_word_logic():
    """Verify encode_word() uses a loop and calls shift_letter to transform each character."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    encode_func_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "encode_word":
            encode_func_node = node
            break

    assert encode_func_node is not None, "Script must define a function named 'encode_word(word, shift)'."

    # Verify loop inside encode_word
    has_loop = any(isinstance(sub, (ast.For, ast.While)) for sub in ast.walk(encode_func_node))
    assert has_loop, "'encode_word' must use a loop to iterate through the characters in the word."

    mod = _load_module()
    assert hasattr(mod, "encode_word"), "Script must define a function named 'encode_word'."
    encode_word = getattr(mod, "encode_word")

    assert encode_word("hello", 2) == "jgnnq", (
        f"Expected encode_word('hello', 2) == 'jgnnq', got {encode_word('hello', 2)!r}"
    )
    assert encode_word("xyz", 3) == "abc", (
        f"Expected encode_word('xyz', 3) == 'abc', got {encode_word('xyz', 3)!r}"
    )


@pytest.mark.ag_user_io
def test_user_io():
    """Verify interactive execution with input prompts and printed encoded result."""
    res = run_script(ENTRYPOINT, inputs=["hello", "2"])
    assert res.returncode == 0, f"Script failed with input ['hello', '2']:\n{res.stderr}"
    assert "jgnnq" in res.stdout, f"Expected encoded word 'jgnnq' in output:\n{res.stdout}"

    res2 = run_script(ENTRYPOINT, inputs=["python", "5"])
    assert res2.returncode == 0, f"Script failed with input ['python', '5']:\n{res2.stderr}"
    # 'p' + 5 = 'u', 'y' + 5 = 'd', 't' + 5 = 'y', 'h' + 5 = 'm', 'o' + 5 = 't', 'n' + 5 = 's'
    assert "udymts" in res2.stdout, f"Expected encoded word 'udymts' in output:\n{res2.stdout}"

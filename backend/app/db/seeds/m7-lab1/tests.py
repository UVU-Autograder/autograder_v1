"""Tests for CS 1400 Module 7 Lab 1: Random Text File Generator."""

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

ENTRYPOINT = "random_text_generator.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("random_text_generator", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["random_text_generator"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_no_syntax_errors
def test_no_syntax_errors():
    """Verify script exists and compiles with no syntax errors."""
    assert_no_syntax_errors(ENTRYPOINT)


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify code contains comments or docstrings."""
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

    assert has_doc or has_comment, "Script must include an explanatory comment or docstring."


@pytest.mark.ag_make_word_logic
def test_make_word_logic():
    """Verify make_word returns words with length between 5 and 10 of lowercase letters."""
    mod = _load_module()
    assert hasattr(mod, "make_word"), "Script must define a function named 'make_word()'."
    make_word = getattr(mod, "make_word")

    for _ in range(30):
        w = make_word()
        assert isinstance(w, str), f"make_word must return a string, got {type(w)}"
        assert 5 <= len(w) <= 10, f"make_word returned word with invalid length {len(w)}: '{w}'"
        assert w.islower() and w.isalpha(), f"make_word must only contain lowercase letters: '{w}'"


@pytest.mark.ag_make_line_logic
def test_make_line_logic():
    """Verify make_line returns 8 to 10 space-separated random words."""
    mod = _load_module()
    assert hasattr(mod, "make_line"), "Script must define a function named 'make_line()'."
    make_line = getattr(mod, "make_line")

    for _ in range(20):
        line = make_line()
        assert isinstance(line, str), f"make_line must return a string, got {type(line)}"
        words = line.strip().split(" ")
        assert 8 <= len(words) <= 10, f"Expected 8 to 10 words in line, got {len(words)}: '{line}'"


@pytest.mark.ag_write_random_text_logic
def test_write_random_text_logic():
    """Verify write_random_text writes 100+ lines to randomText.txt ending with newlines."""
    script_path = assert_file_exists(ENTRYPOINT)
    target_file = script_path.parent / "randomText.txt"
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed during execution:\n{res.stderr}"

    # Check for randomText.txt in script's directory
    assert target_file.is_file(), f"randomText.txt was not generated at {target_file}."
    lines = target_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 100, f"Expected at least 100 lines in randomText.txt, found {len(lines)}"

    # Cleanup after test
    if target_file.exists():
        try:
            target_file.unlink()
        except OSError:
            pass

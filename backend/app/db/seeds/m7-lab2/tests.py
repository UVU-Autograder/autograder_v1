"""Tests for CS 1400 Module 7 Lab 2: Count Vowels in randomText.txt."""

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

ENTRYPOINT = "count_vowels.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("count_vowels", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["count_vowels"] = mod
    spec.loader.exec_module(mod)
    return mod


def _get_vowel_fn(mod):
    for name in dir(mod):
        obj = getattr(mod, name)
        if callable(obj) and name not in ("main", "_load_module") and not name.startswith("__"):
            return obj
    pytest.fail("Could not find vowel counting function in module.")


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


@pytest.mark.ag_define_count_function
def test_define_count_function():
    """Verify a vowel counting function is defined."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name != "main"]
    assert len(func_defs) >= 1, "Script must define a function to read the file and count vowels."


@pytest.mark.ag_count_vowels_accuracy
def test_count_vowels_accuracy():
    """Verify vowel counting correctly counts a, e, i, o, u, y case-insensitively."""
    mod = _load_module()
    fn = _get_vowel_fn(mod)

    # Resolve randomText.txt
    sample_file = assert_file_exists("randomText.txt")
    import inspect
    sig = inspect.signature(fn)
    if len(sig.parameters) >= 1:
        res = fn(str(sample_file))
    else:
        res = fn()

    # res can be dict or tuple
    if isinstance(res, dict):
        assert res.get("a", 0) == 6, f"Expected 6 'a's, got {res.get('a')}"
        assert res.get("e", 0) == 7, f"Expected 7 'e's, got {res.get('e')}"
        assert res.get("i", 0) == 3, f"Expected 3 'i's, got {res.get('i')}"
        assert res.get("o", 0) == 8, f"Expected 8 'o's, got {res.get('o')}"
        assert res.get("u", 0) == 2, f"Expected 2 'u's, got {res.get('u')}"
        assert res.get("y", 0) == 6, f"Expected 6 'y's, got {res.get('y')}"
    elif isinstance(res, (tuple, list)):
        assert len(res) == 6, f"Expected 6 vowel counts (a, e, i, o, u, y), got {len(res)}"
    else:
        pytest.fail(f"Vowel count function must return a dict or tuple/list of counts, got {type(res)}")


@pytest.mark.ag_format_summary_output
def test_format_summary_output():
    """Verify main script prints clear formatted summary message."""
    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout.lower()
    # Check for mentions of vowel names and counts
    for vowel in ["a", "e", "i", "o", "u", "y"]:
        assert vowel in stdout, f"Expected vowel '{vowel}' in formatted summary: {res.stdout}"


@pytest.mark.ag_file_error_handling
def test_file_error_handling():
    """Verify try/except is used to gracefully handle missing file errors."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    assert has_try, "Script must use a try/except block to handle missing file errors gracefully."

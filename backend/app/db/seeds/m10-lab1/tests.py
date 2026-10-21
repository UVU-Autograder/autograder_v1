"""Tests for CS 1400 Module 10 Lab 1: Word Frequency Counter."""

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

ENTRYPOINT = "word_frequency.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("word_frequency", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["word_frequency"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_comment_or_docstring
def test_comment_or_docstring():
    """Verify script exists, compiles with no syntax errors, and includes comments."""
    assert_no_syntax_errors(ENTRYPOINT)
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


@pytest.mark.ag_tokenizes_and_counts
def test_tokenizes_and_counts():
    """Verify word_count returns lowercased word frequencies."""
    mod = _load_module()
    assert hasattr(mod, "word_count"), "Script must define 'word_count(text)'."
    counts = mod.word_count("The dog ran and the dog slept")
    assert counts.get("the") == 2, f"Expected 2 for 'the', got {counts.get('the')}"
    assert counts.get("dog") == 2, f"Expected 2 for 'dog', got {counts.get('dog')}"
    assert counts.get("ran") == 1, f"Expected 1 for 'ran', got {counts.get('ran')}"


@pytest.mark.ag_uses_get_or_in
def test_uses_get_or_in():
    """Verify script builds counts manually with get() or in without Counter."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    # Ensure Counter is not imported
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imports.append(f"{node.module}.{alias.name}")

    assert not any("Counter" in imp for imp in imports), "Script should not import collections.Counter."
    has_get_or_in = ".get(" in source or " in " in source
    assert has_get_or_in, "Script must build frequencies using .get() or 'in' check."


@pytest.mark.ag_prints_with_items
def test_prints_with_items():
    """Verify script uses .items() to iterate and print dictionary."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert ".items()" in source, "Script must use .items() to print dictionary contents."


@pytest.mark.ag_removes_single_occurrences
def test_removes_single_occurrences():
    """Verify script removes single-occurrence entries safely using a copy."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    assert ".copy()" in source or "copy(" in source or "{" in source, (
        "Script should use .copy() or dict comprehension to avoid modifying while iterating."
    )

    res = run_script(ENTRYPOINT)
    assert res.returncode == 0, f"Script failed on run:\n{res.stderr}"
    stdout = res.stdout
    assert "Original Word Frequencies:" in stdout or "the: 3" in stdout
    assert "After removing" in stdout or "dog: 2" in stdout

"""Tests for CS 1400 Module 13 Lab 1: Build a Simple Library Using Objects."""

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

ENTRYPOINT = "library_system.py"


def _load_module():
    path = assert_file_exists(ENTRYPOINT)
    spec = importlib.util.spec_from_file_location("library_system", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.ag_book_class_def
def test_book_class_def():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    class_names = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]
    assert "Book" in class_names, "Code must define a class named 'Book'."

    mod = _load_module()
    assert hasattr(mod, "Book"), "Module must export Book class."
    b = mod.Book("Test Title", "Test Author", 2024)
    assert hasattr(b, "title"), "Book must have 'title' attribute."
    assert hasattr(b, "author"), "Book must have 'author' attribute."
    assert hasattr(b, "year"), "Book must have 'year' attribute."
    assert hasattr(b, "available"), "Book must have 'available' attribute."
    assert b.available is True, "Default available status must be True."


@pytest.mark.ag_init_and_str
def test_init_and_str():
    mod = _load_module()
    b = mod.Book("1984", "George Orwell", 1949)
    rep = str(b)
    assert "1984" in rep, "__str__ output must include the book title."
    assert "George Orwell" in rep, "__str__ output must include the author."
    assert "1949" in rep, "__str__ output must include the publication year."
    assert "Available" in rep or "available" in rep.lower(), "__str__ must include availability state."


@pytest.mark.ag_instance_methods
def test_instance_methods():
    mod = _load_module()
    b = mod.Book("Clean Architecture", "Robert Martin", 2017)
    assert hasattr(b, "borrow"), "Book must have instance method borrow()."
    assert hasattr(b, "return_book"), "Book must have instance method return_book()."
    assert hasattr(b, "is_available"), "Book must have instance method is_available()."

    assert b.is_available() is True
    b.borrow()
    assert b.available is False
    assert b.is_available() is False
    b.return_book()
    assert b.available is True
    assert b.is_available() is True


@pytest.mark.ag_object_list_display
def test_object_list_display():
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    has_loop = any(
        isinstance(node, (ast.For, ast.While))
        for node in ast.walk(tree)
    )
    assert has_loop, "main() must use a loop to display books in the list."

    path = assert_file_exists(ENTRYPOINT)
    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"
    out = result.stdout
    assert "Library Collection" in out or "borrowed" in out.lower(), (
        "Output must display library collection status."
    )


@pytest.mark.ag_comments_and_clean_run
def test_comments_and_clean_run():
    path = assert_file_exists(ENTRYPOINT)
    assert_no_syntax_errors(ENTRYPOINT)
    assert_has_comments(ENTRYPOINT, min_comments=1)

    result = run_script(path)
    assert result.returncode == 0, f"Script failed with code {result.returncode}: {result.stderr}"

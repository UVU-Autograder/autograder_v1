"""Tests for CS 1400 Module 10 Project 4: LORE Vault Recompiler."""

from __future__ import annotations

import ast
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

ENTRYPOINT = "lore_vault.py"


@pytest.mark.ag_main_function_conditional
def test_main_function_conditional():
    """Verify script contains main() with if __name__ == '__main__': guard."""
    _, tree, source = assert_no_syntax_errors(ENTRYPOINT)
    has_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree))
    assert has_main, "Script must define a 'main()' function."
    assert "__name__" in source and "__main__" in source, (
        "Script must include conditional execution guard: if __name__ == '__main__':"
    )


@pytest.mark.ag_no_global_code
def test_no_global_code():
    """Verify there is no top-level global execution code."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    disallowed = (ast.For, ast.While, ast.Call)
    for node in tree.body:
        if isinstance(node, disallowed):
            pytest.fail(f"Disallowed top-level global execution found: {type(node).__name__}")
        if isinstance(node, ast.If):
            # Allowed only if it is the __name__ == '__main__' guard
            test_src = ast.unparse(node.test)
            assert "__main__" in test_src, f"Unexpected top-level if statement: {test_src}"


@pytest.mark.ag_snake_or_camel_case
def test_snake_or_camel_case():
    """Verify variable names follow snake_case or camelCase."""
    _, tree, _ = assert_no_syntax_errors(ENTRYPOINT)
    assigned = find_assigned_variables(tree)
    assert_valid_naming(assigned.keys())


@pytest.mark.ag_given_file_output
def test_given_file_output():
    """Verify reconstruction of given sample file (TTL.txt -> TTL_book.txt)."""
    script_path = assert_file_exists(ENTRYPOINT)
    out_file = script_path.parent / "TTL_book.txt"
    if out_file.exists():
        try:
            out_file.unlink()
        except OSError:
            pass

    res = run_script(ENTRYPOINT, args=["TTL.txt"])
    assert res.returncode == 0, f"Script failed on TTL.txt execution:\n{res.stderr}"

    assert out_file.is_file(), f"Output file TTL_book.txt was not generated at {out_file}."
    lines = [line.rstrip("\r\n") for line in out_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Header check
    assert lines[0] == "TTL", f"First line must be book code 'TTL', got: {lines[0]}"
    assert lines[1].startswith("Longest line (14153):"), f"Expected longest line header, got: {lines[1]}"
    assert "Ecclesiastes" in lines[1]
    assert lines[2].startswith("Average length:"), f"Expected average length header, got: {lines[2]}"

    # Content order check: line 3, line 4, line 5, line 14153
    assert "Twenty Thousand Leagues" in lines[3]
    assert "An Underwater Tour" in lines[4]
    assert "JULES VERNE" in lines[5]
    assert "Ecclesiastes" in lines[6]

    # Cleanup
    if out_file.exists():
        try:
            out_file.unlink()
        except OSError:
            pass


@pytest.mark.ag_unknown_file_output
def test_unknown_file_output():
    """Verify sorting, average calculation, and tie-breaking by higher line number on unknown archive."""
    script_path = assert_file_exists(ENTRYPOINT)
    test_in = script_path.parent / "TEST_ARCHIVE.txt"
    test_out = script_path.parent / "TEST_ARCHIVE_book.txt"

    # Line 2 and Line 4 have the same length (10 chars), higher line number (4) should win
    content = "Line two!!|2\nLine one!|1\nLine four!|4\nLine three|3\n"
    test_in.write_text(content, encoding="utf-8")

    try:
        res = run_script(ENTRYPOINT, args=["TEST_ARCHIVE.txt"])
        assert res.returncode == 0, f"Script failed on unknown archive test:\n{res.stderr}"

        assert test_out.is_file(), f"Expected output file {test_out} not found."
        lines = [line.rstrip("\r\n") for line in test_out.read_text(encoding="utf-8").splitlines() if line.strip()]

        assert lines[0] == "TEST_ARCHIVE"
        # Tie breaker: line 4 has length 10, line 2 has length 10. Line 4 should win
        assert "Longest line (4): Line four!" in lines[1]
        assert "Line one!" in lines[3]
        assert "Line two!!" in lines[4]
        assert "Line three" in lines[5]
        assert "Line four!" in lines[6]
    finally:
        if test_in.exists():
            test_in.unlink()
        if test_out.exists():
            test_out.unlink()

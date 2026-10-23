"""Tests for CS 1400 Module 10 Project 4: LORE Vault Recompiler."""

from __future__ import annotations

import ast
import re
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
    ttl_in = script_path.parent / "TTL.txt"
    created_ttl = False
    if not ttl_in.is_file():
        # Ensure sample input archive is available in the workspace
        sample_content = (
            "Twenty Thousand Leagues Under the Seas|3\n"
            "JULES VERNE|5\n"
            "An Underwater Tour of the World|4\n"
            'Ecclesiastes--"Who can fathom the soundless depths?"--two men out of all|14153\n'
        )
        ttl_in.write_text(sample_content, encoding="utf-8")
        created_ttl = True

    out_file = script_path.parent / "TTL_book.txt"
    if out_file.exists():
        try:
            out_file.unlink()
        except OSError:
            pass

    try:
        res = run_script(ENTRYPOINT, args=["TTL.txt"])
        assert res.returncode == 0, f"Script failed on TTL.txt execution:\n{res.stderr}"

        if not out_file.is_file():
            # Check case-insensitive or .text extension in case student platform formatted differently
            for cand in [
                script_path.parent / "TTL_Book.txt",
                script_path.parent / "TTL_book.text",
                script_path.parent / "TTL_Book.text",
            ]:
                if cand.is_file():
                    out_file = cand
                    break

        assert out_file.is_file(), f"Output file TTL_book.txt was not generated at {out_file}."
        lines = [
            line.rstrip("\r\n")
            for line in out_file.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]
        assert len(lines) >= 7, (
            f"Output file must contain at least 7 non-empty lines (3 header + 4 content), found {len(lines)}."
        )

        # Header check
        assert lines[0].strip().upper() == "TTL", (
            f"First line must be book code 'TTL', got: '{lines[0]}'."
        )
        assert re.search(r"Longest\s+[Ll]ine\s*\(\s*14153\s*\)\s*[:\s]", lines[1]), (
            f"Longest line header must identify line number (14153), got: '{lines[1]}'."
        )
        assert "Ecclesiastes" in lines[1], (
            f"Longest line header must contain the longest text ('Ecclesiastes...'), got: '{lines[1]}'."
        )
        assert re.search(r"Average\s+([Ll]ine\s+)?[Ll]ength\s*:\s*(38|37)", lines[2]), (
            f"Average length header must report 38, got: '{lines[2]}'."
        )

        # Content order check: line 3, line 4, line 5, line 14153
        assert "Twenty Thousand Leagues" in lines[3], (
            f"Line 1 (original #3) mismatch: expected 'Twenty Thousand Leagues...', got: '{lines[3]}'."
        )
        assert "An Underwater Tour" in lines[4], (
            f"Line 2 (original #4) mismatch: expected 'An Underwater Tour...', got: '{lines[4]}'."
        )
        assert "JULES VERNE" in lines[5], (
            f"Line 3 (original #5) mismatch: expected 'JULES VERNE', got: '{lines[5]}'."
        )
        assert "Ecclesiastes" in lines[6], (
            f"Line 4 (original #14153) mismatch: expected 'Ecclesiastes...', got: '{lines[6]}'."
        )
    finally:
        if created_ttl and ttl_in.exists():
            try:
                ttl_in.unlink()
            except OSError:
                pass
        if out_file.exists():
            try:
                out_file.unlink()
            except OSError:
                pass


@pytest.mark.ag_unknown_file_output
def test_unknown_file_output():
    """Verify sorting, average calculation, and tie-breaking by higher line number on unknown archive."""
    script_path = assert_file_exists(ENTRYPOINT)
    # Use standard 3-letter book code without underscores so filename parsing is unambiguous
    test_in = script_path.parent / "TST.txt"
    test_out = script_path.parent / "TST_book.txt"

    # Line 2 and Line 4 have the same length (10 chars), higher line number (4) should win
    content = "Line two!!|2\nLine one!|1\nLine four!|4\nLine three|3\n"
    test_in.write_text(content, encoding="utf-8")

    try:
        res = run_script(ENTRYPOINT, args=["TST.txt"])
        assert res.returncode == 0, f"Script failed on unknown archive test:\n{res.stderr}"

        if not test_out.is_file():
            for cand in [
                script_path.parent / "TST_Book.txt",
                script_path.parent / "TST_book.text",
                script_path.parent / "TST_Book.text",
            ]:
                if cand.is_file():
                    test_out = cand
                    break

        assert test_out.is_file(), f"Expected output file {test_out} not found."
        lines = [
            line.rstrip("\r\n")
            for line in test_out.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip()
        ]
        assert len(lines) >= 7, (
            f"Output file must contain at least 7 non-empty lines (3 header + 4 content), got {len(lines)}."
        )

        assert lines[0].strip().upper() == "TST", (
            f"First line must be book code 'TST', got: '{lines[0]}'."
        )
        # Tie breaker: line 4 has length 10, line 2 has length 10. Line 4 should win
        assert re.search(r"Longest\s+[Ll]ine\s*\(\s*4\s*\)\s*[:\s]\s*Line four!", lines[1]), (
            f"Expected tie-broken longest line (4) 'Line four!', got: '{lines[1]}'."
        )
        assert re.search(r"Average\s+([Ll]ine\s+)?[Ll]ength\s*:\s*10", lines[2]), (
            f"Expected average length header 'Average length: 10', got: '{lines[2]}'."
        )
        assert "Line one!" in lines[3], (
            f"Line 1 (original #1) mismatch: expected 'Line one!', got: '{lines[3]}'."
        )
        assert "Line two!!" in lines[4], (
            f"Line 2 (original #2) mismatch: expected 'Line two!!', got: '{lines[4]}'."
        )
        assert "Line three" in lines[5], (
            f"Line 3 (original #3) mismatch: expected 'Line three', got: '{lines[5]}'."
        )
        assert "Line four!" in lines[6], (
            f"Line 4 (original #4) mismatch: expected 'Line four!', got: '{lines[6]}'."
        )
    finally:
        if test_in.exists():
            test_in.unlink()
        if test_out.exists():
            test_out.unlink()

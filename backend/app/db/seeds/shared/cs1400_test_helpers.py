"""Shared test helper utilities for CS 1400 autograder assignments."""

from __future__ import annotations

import ast
import io
import os
import re
import subprocess
import sys
import tokenize
from pathlib import Path

SNAKE_OR_CAMEL_RE = re.compile(r"^[a-z][a-z0-9_]*$|^[a-z][a-zA-Z0-9]*$")


def get_submission_path(filename: str) -> Path:
    """Return the resolved path to a submitted file, supporting Canvas resubmission names and flexible fallbacks."""
    env_dir = os.getenv("STUDENT_SUBMISSION_DIR")
    if env_dir:
        # Strictly isolate grading to the student's submission directory
        search_dirs = [Path(env_dir)]
    else:
        search_dirs = [Path.cwd()]
        # Look in the directory of the calling module (e.g. seed directory during local development)
        import inspect

        frame = inspect.currentframe()
        try:
            while frame:
                caller_dir = Path(frame.f_code.co_filename).resolve().parent
                if caller_dir not in search_dirs:
                    search_dirs.append(caller_dir)
                frame = frame.f_back
        finally:
            del frame

    # 1. Exact match across search dirs
    for d in search_dirs:
        cand = d / filename
        if cand.is_file():
            return cand.resolve()

    # 2. Case-insensitive match across search dirs (e.g. Lore_Vault.py -> lore_vault.py)
    for d in search_dirs:
        if d.is_dir():
            for p in d.glob("*.py"):
                if p.name.lower() == filename.lower():
                    return p.resolve()

    # 3. Canvas resubmission suffix on the exact required file (e.g. lore_vault-1.py or lore_vault-<uuid>.py -> lore_vault.py)
    stem = Path(filename).stem.lower()
    suffix = Path(filename).suffix.lower()
    for d in search_dirs:
        if d.is_dir():
            for p in d.glob("*.py"):
                if p.suffix.lower() == suffix and re.match(
                    rf"^{re.escape(stem)}-(?:[0-9]+|[0-9a-fA-F-]{{36}})$", p.stem.lower()
                ):
                    return p.resolve()

    return (search_dirs[0] / filename).resolve()


def assert_file_exists(filename: str) -> Path:
    """Assert that the specified file exists and is a regular file."""
    path = get_submission_path(filename)
    assert path.is_file(), f"Required file '{filename}' was not found in the submission."
    return path


def assert_no_syntax_errors(filename: str) -> tuple[Path, ast.AST, str]:
    """Assert that the file parses without syntax errors; returns (path, ast_tree, source_code)."""
    path = assert_file_exists(filename)
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="latin-1")

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in '{filename}': {exc}") from exc

    return path, tree, source


def assert_has_comments(filename: str, min_comments: int = 1) -> None:
    """Assert that the source code contains at least min_comments comment(s)."""
    path = assert_file_exists(filename)
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="latin-1")

    comment_count = 0
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            # Ignore editor directives like # -*- coding: utf-8 -*-
            comment_text = tok.string.strip()
            if not comment_text.startswith("#!") and "coding:" not in comment_text:
                comment_count += 1

    assert comment_count >= min_comments, (
        f"'{filename}' must include at least {min_comments} comment(s) explaining the code. "
        f"Found {comment_count}."
    )


def run_script(
    filename: str,
    inputs: list[str] | None = None,
    args: list[str] | None = None,
    *,
    timeout: int = 5,
) -> subprocess.CompletedProcess[str]:
    """Execute the Python script in a subprocess with optional standard input and command-line arguments."""
    path = assert_file_exists(filename)
    stdin_data = ("\n".join(inputs) + "\n") if inputs is not None else None
    cmd = [sys.executable, str(path)]
    if args:
        cmd.extend(args)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(path.parent),
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"Execution of '{filename}' timed out after {timeout} seconds. "
            "Ensure the program does not enter an infinite loop or wait for unexpected input."
        ) from exc

    return result


def find_assigned_variables(tree: ast.AST) -> dict[str, ast.AST]:
    """Find all top-level assigned variable names and their AST value nodes."""
    assignments: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                assignments[node.target.id] = node.value
    return assignments


def assert_valid_naming(names: list[str] | set[str]) -> None:
    """Assert that variable names adhere to snake_case or camelCase."""
    for name in names:
        # Ignore dunder or private names
        if name.startswith("_"):
            continue
        assert SNAKE_OR_CAMEL_RE.match(name), (
            f"Variable '{name}' should follow snake_case (e.g., total_count) "
            f"or camelCase (e.g., totalCount)."
        )

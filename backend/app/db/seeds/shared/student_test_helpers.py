import ast
import re
import subprocess
import sys
from pathlib import Path


def assert_test_function_count(file_path: str, *, minimum: int) -> None:
    path = Path(file_path)
    assert path.is_file(), f"{file_path} is missing from submission"

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=file_path)
    except (OSError, SyntaxError) as exc:
        raise AssertionError(f"Could not parse {file_path}: {exc}") from exc

    test_functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    assert len(test_functions) >= minimum, (
        f"{file_path} must define at least {minimum} test functions starting "
        f"with 'test_'. Found {len(test_functions)}: {test_functions}"
    )


def assert_student_pytest_passes(
    file_path: str,
    *,
    minimum: int,
    timeout_seconds: int,
) -> None:
    path = Path(file_path)
    assert path.is_file(), f"{file_path} is missing from submission"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", file_path, "-v"],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"Student test suite execution timed out after {timeout_seconds} seconds."
        ) from exc

    assert result.returncode == 0, (
        f"Student tests failed or crashed. Exit code: {result.returncode}.\n"
        f"Stdout:\n{result.stdout}\nStderr:\n{result.stderr}"
    )

    match = re.search(r"(\d+)\s+passed", result.stdout)
    passed_count = int(match.group(1)) if match else 0
    assert passed_count >= minimum, (
        f"Expected at least {minimum} tests to pass, but only {passed_count} passed.\n"
        f"Pytest Output:\n{result.stdout}"
    )

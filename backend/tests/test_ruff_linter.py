"""Automated Ruff Linter Test.

Executes a full Ruff linting pass across backend application and test modules during pytest runs.
"""

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_ruff_linter_pass():
    """Verify that all Python code in backend app and tests passes Ruff linting with zero errors."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "app", "tests"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Ruff linter check failed with errors:\n\n{result.stdout}\n{result.stderr}"
    )

"""Schemas and diagnostic taxonomy for grading execution failures."""
from __future__ import annotations

from enum import Enum


class ExecutionFailureCategory(str, Enum):
    """Evidence-based taxonomy for test execution and grading failures."""

    SYNTAX_ERROR = "syntax_error"
    IMPORT_ERROR = "import_error"
    ASSERTION_FAILURE = "assertion_failure"
    RUNTIME_EXCEPTION = "runtime_exception"
    RESOURCE_LIMIT_EXCEEDED = "resource_limit_exceeded"
    TEST_HARNESS_DEFECT = "test_harness_defect"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"


INFRASTRUCTURE_FAILURE_CATEGORIES: frozenset[str] = frozenset(
    {
        ExecutionFailureCategory.INFRASTRUCTURE_FAILURE.value,
        ExecutionFailureCategory.TEST_HARNESS_DEFECT.value,
        "judge0_error",
        "cleanup_failure",
        "internal_error",
        "execution_unavailable",
        "execution_interrupted",
    }
)

_RUNTIME_EXCEPTION_MARKERS: tuple[str, ...] = (
    "ZeroDivisionError",
    "IndexError",
    "KeyError",
    "TypeError",
    "ValueError",
    "AttributeError",
    "NameError",
    "RecursionError",
    "EOFError",
    "FileNotFoundError",
    "PermissionError",
    "OSError",
    "RuntimeError",
    "StopIteration",
    "UnboundLocalError",
)


def is_infrastructure_failure(category: str | None) -> bool:
    """Return True if *category* represents an infrastructure or harness defect rather than student code error."""
    if not category:
        return False
    return category in INFRASTRUCTURE_FAILURE_CATEGORIES


def classify_execution_failure(
    *,
    message: str | None = None,
    stderr: str | None = None,
    exit_code: int = -1,
    outcome: str | None = None,
    legacy_category: str | None = None,
) -> ExecutionFailureCategory | None:
    """Classify a test or runner failure using exit codes, stderr, and traceback patterns."""
    if outcome == "passed":
        return None

    combined = "\n".join(part for part in (message, stderr) if part)
    combined_lower = combined.lower()

    if legacy_category in {
        "judge0_error",
        "cleanup_failure",
        "internal_error",
        "infrastructure_failure",
    }:
        return ExecutionFailureCategory.INFRASTRUCTURE_FAILURE

    if (
        legacy_category in {"timeout", "resource_limit_exceeded"}
        or exit_code in (124, 137, 139)
        or "memoryerror" in combined_lower
        or "timed out" in combined_lower
        or "time limit exceeded" in combined_lower
        or "output limit exceeded" in combined_lower
    ):
        return ExecutionFailureCategory.RESOURCE_LIMIT_EXCEEDED

    if any(err in combined for err in ("SyntaxError", "IndentationError", "TabError")):
        return ExecutionFailureCategory.SYNTAX_ERROR

    if (
        "ModuleNotFoundError" in combined
        or "ImportError" in combined
        or "preinstalled dependency" in combined_lower
    ):
        return ExecutionFailureCategory.IMPORT_ERROR

    if (
        exit_code in (2, 3, 4)
        or "internalerror>" in combined_lower
        or ("fixture '" in combined_lower and "not found" in combined_lower)
        or "collection error" in combined_lower
    ):
        return ExecutionFailureCategory.TEST_HARNESS_DEFECT

    if "AssertionError" in combined or (
        outcome == "failed"
        and not any(exc_name in combined for exc_name in _RUNTIME_EXCEPTION_MARKERS)
    ):
        return ExecutionFailureCategory.ASSERTION_FAILURE

    if any(exc_name in combined for exc_name in _RUNTIME_EXCEPTION_MARKERS) or outcome in (
        "failed",
        "error",
    ):
        return ExecutionFailureCategory.RUNTIME_EXCEPTION

    if exit_code not in (0, 1, -1):
        return ExecutionFailureCategory.INFRASTRUCTURE_FAILURE

    if combined.strip():
        return ExecutionFailureCategory.RUNTIME_EXCEPTION

    return None

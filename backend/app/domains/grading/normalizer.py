"""Output normalization utilities for grading comparisons.

Provides functions to normalize program output (strip trailing whitespace,
remove blank lines, unify line endings) so that trivial formatting differences
do not cause grading mismatches.
"""

from __future__ import annotations


def normalize_output(text: str) -> str:
    """Normalize program output for comparison.

    Processing steps, applied in order:
    1. Convert Windows line endings (``\\r\\n``) to Unix (``\\n``).
    2. Strip trailing whitespace from each line.
    3. Remove blank lines.
    4. Strip leading/trailing whitespace from the entire output.

    Args:
        text: Raw program output string.

    Returns:
        The cleaned, normalized output string.
    """
    # Step 1: unify line endings.
    text = text.replace("\r\n", "\n")

    # Step 2 & 3: strip trailing whitespace per line and drop blank lines.
    lines = [line.rstrip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    # Step 4: join and strip the whole result.
    return "\n".join(lines).strip()


def outputs_match(expected: str, actual: str) -> bool:
    """Compare two outputs after normalization.

    Both *expected* and *actual* are passed through :func:`normalize_output`
    before the comparison, so trivial whitespace/line-ending differences are
    ignored.

    Args:
        expected: The reference (correct) output.
        actual: The student program's output.

    Returns:
        ``True`` if the normalized outputs are identical.
    """
    return normalize_output(expected) == normalize_output(actual)

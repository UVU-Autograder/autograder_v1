"""Output normalization utilities for grading comparisons.

Provides functions to normalize program output (strip trailing whitespace,
remove blank lines, unify line endings) so that trivial formatting differences
do not cause grading mismatches.
"""

from __future__ import annotations


def normalize_output(text: str) -> str:
    """Normalize program output for comparison.

    Processing steps, applied in order:
    1. Unify line endings (\r\n, \r, \n) via splitlines.
    2. Strip trailing whitespace from each line.
    3. Remove blank lines.
    4. Strip leading/trailing whitespace from the entire output.

    Args:
        text: Raw program output string.

    Returns:
        The cleaned, normalized output string.
    """
    lines = [stripped for line in text.splitlines() if (stripped := line.rstrip())]
    return "\n".join(lines).strip()



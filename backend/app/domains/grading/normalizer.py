"""Output normalization and comparison utilities for grading.

Provides comparison modes:
- "normalized" (default): Whitespace- and newline-tolerant comparison.
- "exact": Byte/character exact string comparison, normalizing CRLF to LF.
- "numeric_tolerance": Floating-point comparison with relative/absolute tolerance bounds.
- "regex": Pattern matching using regular expressions with MULTILINE mode.
"""

from __future__ import annotations

import math
import re

NUMBER_PATTERN = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
DEFAULT_NUMERIC_TOLERANCE = 1e-4


def normalize_output(text: str) -> str:
    """Normalize program output for comparison.

    Processing steps, applied in order:
    1. Unify line endings (\\r\\n, \\r, \\n) via splitlines.
    2. Strip trailing whitespace from each line.
    3. Remove blank lines.
    4. Strip leading/trailing whitespace from the entire output.

    Args:
        text: Raw program output string.

    Returns:
        The cleaned, normalized output string.
    """
    if not text:
        return ""
    lines = [stripped for line in text.splitlines() if (stripped := line.rstrip())]
    return "\n".join(lines).strip()


def compare_exact(actual: str, expected: str) -> bool:
    """Compare exact strings, normalizing CRLF line endings to LF."""
    act = (actual or "").replace("\r\n", "\n")
    exp = (expected or "").replace("\r\n", "\n")
    return act == exp


def compare_regex(actual: str, pattern: str) -> bool:
    """Match output against configured regular expression pattern using re.MULTILINE."""
    norm_actual = (actual or "").replace("\r\n", "\n")
    norm_pattern = (pattern or "").replace("\r\n", "\n")
    if not norm_pattern:
        return norm_actual == ""
    try:
        compiled = re.compile(norm_pattern, re.MULTILINE)
        return compiled.search(norm_actual) is not None
    except re.error:
        return False


def compare_numeric_tolerance(
    actual: str,
    expected: str,
    tolerance: float | None = None,
) -> bool:
    """Compare numeric or mixed text/number output within tolerance.

    Defaults to tolerance=1e-4 when unspecified.
    """
    if tolerance is None:
        tol = DEFAULT_NUMERIC_TOLERANCE
    else:
        try:
            tol_f = float(tolerance)
            tol = DEFAULT_NUMERIC_TOLERANCE if tol_f < 0 else tol_f
        except (ValueError, TypeError):
            tol = DEFAULT_NUMERIC_TOLERANCE

    act_str = actual or ""
    exp_str = expected or ""

    # Quick check for identical strings
    if act_str.replace("\r\n", "\n") == exp_str.replace("\r\n", "\n"):
        return True

    # Try purely numeric parsing first
    try:
        act_val = float(act_str.strip())
        exp_val = float(exp_str.strip())
        if math.isnan(act_val) and math.isnan(exp_val):
            return True
        return math.isclose(act_val, exp_val, rel_tol=tol, abs_tol=tol)
    except (ValueError, TypeError):
        pass

    # Normalized text with embedded numbers
    norm_act = normalize_output(act_str)
    norm_exp = normalize_output(exp_str)

    if norm_act == norm_exp:
        return True

    act_nums = NUMBER_PATTERN.findall(norm_act)
    exp_nums = NUMBER_PATTERN.findall(norm_exp)

    # Number of numeric tokens must match
    if len(act_nums) != len(exp_nums):
        return False

    act_parts = NUMBER_PATTERN.split(norm_act)
    exp_parts = NUMBER_PATTERN.split(norm_exp)

    if len(act_parts) != len(exp_parts):
        return False

    # Check non-numeric text separators (normalizing multiple spaces/tabs)
    for a_part, e_part in zip(act_parts, exp_parts):
        if re.sub(r"[ \t]+", " ", a_part) != re.sub(r"[ \t]+", " ", e_part):
            return False

    # Check numeric tokens within tolerance
    for a_num, e_num in zip(act_nums, exp_nums):
        try:
            a_f = float(a_num)
            e_f = float(e_num)
        except (ValueError, TypeError):
            return False
        if math.isnan(a_f) and math.isnan(e_f):
            continue
        if not math.isclose(a_f, e_f, rel_tol=tol, abs_tol=tol):
            return False

    return True


def compare_outputs(
    actual: str,
    expected: str,
    mode: str = "normalized",
    tolerance: float | None = None,
) -> bool:
    """Compare outputs according to configured mode.

    Supported modes:
    - "normalized": Whitespace- and newline-tolerant comparison.
    - "exact": Exact comparison normalizing CRLF to LF.
    - "numeric_tolerance": Floating-point comparison with rel_tol/abs_tol.
    - "regex": Regular expression search with re.MULTILINE.
    """
    if mode == "exact":
        return compare_exact(actual, expected)
    elif mode == "numeric_tolerance":
        return compare_numeric_tolerance(actual, expected, tolerance=tolerance)
    elif mode == "regex":
        return compare_regex(actual, expected)
    else:
        # Default: normalized
        return normalize_output(actual or "") == normalize_output(expected or "")

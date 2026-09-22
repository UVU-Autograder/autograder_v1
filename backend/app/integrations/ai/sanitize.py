"""FERPA scrubbing applied to everything that goes into a model prompt.

Lives in the shared prompt package so training data, eval inputs, and live
sandbox prompts are scrubbed identically -- a model trained on unscrubbed text
and served scrubbed text sees two different distributions.
"""

import re


def sanitize_code_and_text(text: str) -> str:
    """Strip student identifiers, emails, and student ID patterns to ensure FERPA compliance."""
    if not text:
        return ""
    # Strip email addresses
    sanitized = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", text)
    # Strip UVU-style IDs (e.g., 10123456 or U10123456 or A12345678)
    sanitized = re.sub(r"\b[AUau]?\d{7,8}\b", "[REDACTED_ID]", sanitized)
    # Strip common name/author header patterns in comments or metadata lines without corrupting code variables
    sanitized = re.sub(
        r"(?im)^([ \t]*(?:#|//|/\*|\*)\s*)(author|student(?:\s*name)?|name|submitted\s*by)\s*[:=]\s*[^\n\r]+",
        r"\1\2: [REDACTED_NAME]",
        sanitized,
    )
    sanitized = re.sub(
        r"(?im)^([ \t]*)(author|student(?:\s*name)?|submitted\s*by)\s*[:=]\s*[^\n\r]+",
        r"\1\2: [REDACTED_NAME]",
        sanitized,
    )
    return sanitized

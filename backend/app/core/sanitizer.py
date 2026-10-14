"""Unified FERPA and PII sanitization registry for logs and AI prompt pipelines.

Maintains distinct, specialized rule sets:
- Log redaction: rewrites Canvas filenames, student workspace segments, emails,
  Judge0 tokens, and UVU-prefixed IDs (preserving bare numbers like ports and counts).
- Prompt scrubbing: rewrites comment author headers, emails, and bare/prefixed
  student IDs ([REDACTED_ID]), leaving declarations like name = "Project" intact.
"""

from __future__ import annotations

import re

# Log-specific and shared patterns
CANVAS_EXPORT_FILENAME_RE = re.compile(
    r"[a-zA-Z0-9\-]+_(?:LATE_)?[0-9]+_[0-9]+_[^\s,;\"']+"
)
STUDENT_WORKSPACE_SEGMENT_RE = re.compile(r"student_[0-9]+")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
JUDGE0_TOKEN_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
UVU_ID_RE = re.compile(r"\b[uU]-?[0-9]{7,8}\b")

# Prompt-specific patterns
PROMPT_ID_RE = re.compile(r"\b[AUau]?\d{7,8}\b")
HEADER_AUTHOR_RE_1 = re.compile(
    r"(?im)^([ \t]*(?:#|//|/\*|\*)\s*)(author|student(?:\s*name)?|name|submitted\s*by)\s*[:=]\s*[^\n\r]+"
)
HEADER_AUTHOR_RE_2 = re.compile(
    r"(?im)^([ \t]*)(author|student(?:\s*name)?|submitted\s*by)\s*[:=]\s*[^\n\r]+"
)

LOG_REDACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (CANVAS_EXPORT_FILENAME_RE, "[REDACTED_CANVAS_FILENAME]"),
    (STUDENT_WORKSPACE_SEGMENT_RE, "student_[REDACTED]"),
    (EMAIL_RE, "[REDACTED_EMAIL]"),
    (JUDGE0_TOKEN_RE, "[REDACTED_TOKEN]"),
    (UVU_ID_RE, "[REDACTED_UVU_ID]"),
)


def redact_sensitive_text(text: str) -> str:
    """Remove education-record identifiers from free-form log text."""
    redacted = text
    for pattern, replacement in LOG_REDACTION_RULES:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def sanitize_code_and_text(text: str) -> str:
    """Strip student identifiers, emails, and student ID patterns from model prompts."""
    if not text:
        return ""
    sanitized = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    sanitized = PROMPT_ID_RE.sub("[REDACTED_ID]", sanitized)
    sanitized = HEADER_AUTHOR_RE_1.sub(r"\1\2: [REDACTED_NAME]", sanitized)
    sanitized = HEADER_AUTHOR_RE_2.sub(r"\1\2: [REDACTED_NAME]", sanitized)
    return sanitized

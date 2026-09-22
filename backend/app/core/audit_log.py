"""Structured audit logging with FERPA-safe field allowlists and PII redaction."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

AUDIT_LOGGER_NAME = "autograder.audit"

ALLOWED_AUDIT_FIELDS = frozenset({
    "actor_user_id",
    "assignment_id",
    "cleaned_runs_count",
    "course_id",
    "error_count",
    "failure_category",
    "failure_count",
    "run_id",
    "sandbox_run_id",
    "section_id",
    "submission_count",
    "success_count",
    "timeout_count",
    "unmatched_count",
    "warning_count",
    "workflow_type",
})

CANVAS_EXPORT_FILENAME_RE = re.compile(
    r"[a-zA-Z0-9\-]+_(?:LATE_)?[0-9]+_[0-9]+_[^\s,;\"']+"
)
STUDENT_WORKSPACE_SEGMENT_RE = re.compile(r"student_[0-9]+")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
JUDGE0_TOKEN_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

_REDACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (CANVAS_EXPORT_FILENAME_RE, "[REDACTED_CANVAS_FILENAME]"),
    (STUDENT_WORKSPACE_SEGMENT_RE, "student_[REDACTED]"),
    (EMAIL_RE, "[REDACTED_EMAIL]"),
    (JUDGE0_TOKEN_RE, "[REDACTED_TOKEN]"),
)


def redact_sensitive_text(text: str) -> str:
    """Remove education-record identifiers from free-form log text."""
    redacted = text
    for pattern, replacement in _REDACTION_RULES:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def sanitize_audit_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive_text(value)
    if isinstance(value, dict):
        return {
            str(key): sanitize_audit_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [sanitize_audit_value(item) for item in value]
    return value


def sanitize_audit_fields(fields: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in ALLOWED_AUDIT_FIELDS:
            continue
        sanitized[key] = sanitize_audit_value(value)
    return sanitized


def audit_event(event: str, **fields: Any) -> None:
    """Emit a structured, allowlisted audit record as JSON."""
    payload = {
        "audit_event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        **sanitize_audit_fields(fields),
    }
    logging.getLogger(AUDIT_LOGGER_NAME).info(json.dumps(payload, sort_keys=True))


class SensitiveDataFilter(logging.Filter):
    """Redact education-record identifiers from all application log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        original = record.getMessage()
        redacted = redact_sensitive_text(original)
        if redacted != original:
            record.msg = redacted
            record.args = ()
            audit_event(
                "audit.pii_redacted",
                workflow_type="logging",
            )
        return True


def configure_audit_logging() -> None:
    """Install the sensitive-data filter once per process."""
    if getattr(configure_audit_logging, "_configured", False):
        return

    root = logging.getLogger()
    if not any(isinstance(item, SensitiveDataFilter) for item in root.filters):
        root.addFilter(SensitiveDataFilter())

    audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
    audit_logger.propagate = True

    configure_audit_logging._configured = True  # type: ignore[attr-defined]

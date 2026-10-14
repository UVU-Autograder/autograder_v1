"""Structured audit logging with FERPA-safe field allowlists and PII redaction."""

from __future__ import annotations

import json
import logging
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from app.core.sanitizer import (
    LOG_REDACTION_RULES,
    redact_sensitive_text,
)

AUDIT_LOGGER_NAME = "autograder.audit"
AUDIT_META_LOGGER_NAME = "autograder.audit.meta"

_REDACTION_RULES = LOG_REDACTION_RULES

ALLOWED_AUDIT_FIELDS = frozenset({
    "actor_user_id",
    "assignment_id",
    "cleaned_runs_count",
    "client_ip",
    "course_id",
    "denial_reason",
    "error_count",
    "failure_category",
    "failure_count",
    "http_method",
    "path",
    "run_id",
    "sandbox_run_id",
    "section_id",
    "status_code",
    "submission_count",
    "success_count",
    "timeout_count",
    "unmatched_count",
    "warning_count",
    "workflow_type",
})

_AUDIT_CONTEXT: ContextVar[dict[str, Any] | None] = ContextVar("audit_context", default=None)


def _validate_and_filter_fields(fields: dict[str, Any], caller_context: str) -> dict[str, Any]:
    """Single-path field validator: fail-fast outside production, drop and warn on meta logger in production."""
    disallowed = set(fields) - ALLOWED_AUDIT_FIELDS
    if not disallowed:
        return fields
    from app.core.settings import get_settings

    if get_settings().environment != "production":
        raise ValueError(f"Unallowlisted fields in {caller_context}: {sorted(disallowed)}")

    logging.getLogger(AUDIT_META_LOGGER_NAME).warning(
        "Dropped unallowlisted audit fields in %s: %s", caller_context, sorted(disallowed)
    )
    return {k: v for k, v in fields.items() if k in ALLOWED_AUDIT_FIELDS}


@contextmanager
def audit_context(**fields: Any) -> Generator[None, None, None]:
    """Scoped copy-on-write ambient context manager for audit fields."""
    validated = _validate_and_filter_fields(fields, "audit_context")
    parent = _AUDIT_CONTEXT.get()
    child = {**(parent or {}), **validated}
    token = _AUDIT_CONTEXT.set(child)
    try:
        yield
    finally:
        _AUDIT_CONTEXT.reset(token)


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
    """Emit a structured, allowlisted audit record as JSON and persist to database."""
    ambient = _AUDIT_CONTEXT.get() or {}
    raw = {**ambient, **fields}
    validated = _validate_and_filter_fields(raw, f"audit_event '{event}'")
    now_dt = datetime.now(UTC)
    sanitized = sanitize_audit_fields(validated)
    payload = {
        "audit_event": event,
        "timestamp": now_dt.isoformat(),
        **sanitized,
    }
    logging.getLogger(AUDIT_LOGGER_NAME).info(json.dumps(payload, sort_keys=True))

    try:
        from app.domains.audit.service import record_audit_event

        record_audit_event(event, now_dt, sanitized)
    except Exception:
        pass



def log_and_audit_error(
    target_logger: logging.Logger,
    message: str,
    event: str,
    **fields: Any,
) -> None:
    """Log an error message on the domain logger and emit a structured audit record."""
    target_logger.error(message)
    audit_event(event, **fields)


def audit_access_denied(
    status_code: int,
    reason: str,
    actor_user_id: int | None = None,
    path: str | None = None,
    http_method: str | None = None,
    client_ip: str | None = None,
    request: Any = None,
) -> None:
    """Emit a structured auth.access_denied audit event with allowlisted metadata."""
    if request is not None:
        if path is None and hasattr(request, "url"):
            path = request.url.path
        if http_method is None and hasattr(request, "method"):
            http_method = request.method
        if client_ip is None and hasattr(request, "client") and request.client:
            client_ip = request.client.host

    fields: dict[str, Any] = {
        "status_code": status_code,
        "denial_reason": reason,
    }
    if actor_user_id is not None:
        fields["actor_user_id"] = actor_user_id
    if path is not None:
        fields["path"] = path
    if http_method is not None:
        fields["http_method"] = http_method
    if client_ip is not None:
        fields["client_ip"] = client_ip

    audit_event("auth.access_denied", **fields)


class SensitiveDataFilter(logging.Filter):
    """Redact education-record identifiers and idempotently tag ambient context on log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not record.name.startswith("autograder.audit") and not getattr(record, "_audit_context_tagged", False):
            ambient = _AUDIT_CONTEXT.get()
            if ambient:
                tags = [
                    f"{k}={ambient[k]}"
                    for k in ("run_id", "course_id", "assignment_id", "workflow_type")
                    if k in ambient
                ]
                if tags:
                    tag_prefix = "[" + " ".join(tags) + "]"
                    record.msg = f"{tag_prefix} {record.getMessage()}"
                    record.args = ()
            record._audit_context_tagged = True

        original = record.getMessage()
        redacted = redact_sensitive_text(original)
        if redacted != original:
            record.msg = redacted
            record.args = ()
            audit_event(
                "audit.pii_redacted",
                workflow_type="logging",
            )
        if record.exc_text:
            record.exc_text = redact_sensitive_text(record.exc_text)
        return True


class RedactingFormatter(logging.Formatter):
    """Wrapper formatter ensuring formatted messages, tracebacks, and stack traces are redacted."""

    def __init__(self, delegate: logging.Formatter | None = None) -> None:
        super().__init__()
        self.delegate = delegate

    def format(self, record: logging.LogRecord) -> str:
        if self.delegate is not None:
            formatted = self.delegate.format(record)
        else:
            formatted = super().format(record)
        if record.exc_text:
            record.exc_text = redact_sensitive_text(record.exc_text)
        return redact_sensitive_text(formatted)

    def formatException(self, exc_info: Any) -> str:
        if self.delegate is not None:
            raw = self.delegate.formatException(exc_info)
        else:
            raw = super().formatException(exc_info)
        return redact_sensitive_text(raw)

    def formatStack(self, stack_info: str) -> str:
        if self.delegate is not None:
            raw = self.delegate.formatStack(stack_info)
        else:
            raw = super().formatStack(stack_info)
        return redact_sensitive_text(raw)

    def __getattr__(self, name: str) -> Any:
        if self.delegate is not None:
            return getattr(self.delegate, name)
        raise AttributeError(f"{type(self).__name__} has no attribute {name!r}")


def wrap_formatter_with_redaction(
    formatter: logging.Formatter | None,
) -> RedactingFormatter:
    """Ensure a handler's formatter is wrapped with RedactingFormatter."""
    if isinstance(formatter, RedactingFormatter):
        return formatter
    return RedactingFormatter(delegate=formatter)


KNOWN_FRAMEWORK_LOGGERS = (
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "celery",
    "celery.task",
    "celery.worker",
    "sqlalchemy",
    "sqlalchemy.engine",
)


def _apply_redaction_to_logger(target_logger: logging.Logger) -> None:
    if not any(isinstance(f, SensitiveDataFilter) for f in target_logger.filters):
        target_logger.addFilter(SensitiveDataFilter())
    for handler in target_logger.handlers:
        if not any(isinstance(f, SensitiveDataFilter) for f in handler.filters):
            handler.addFilter(SensitiveDataFilter())
        handler.formatter = wrap_formatter_with_redaction(handler.formatter)


def configure_audit_logging() -> None:
    """Install the sensitive-data filter and redacting formatters process-wide."""
    root = logging.getLogger()
    _apply_redaction_to_logger(root)

    for logger_name in KNOWN_FRAMEWORK_LOGGERS:
        _apply_redaction_to_logger(logging.getLogger(logger_name))

    for _name, logger_obj in list(logging.Logger.manager.loggerDict.items()):
        if isinstance(logger_obj, logging.Logger):
            _apply_redaction_to_logger(logger_obj)

    audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
    audit_logger.propagate = True

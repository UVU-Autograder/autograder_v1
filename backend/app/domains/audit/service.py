from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit_log import ALLOWED_AUDIT_FIELDS
from app.core.sanitizer import LOG_REDACTION_RULES
from app.domains.audit.models import AuditRecord

logger = logging.getLogger(__name__)


def record_audit_event(
    event: str,
    timestamp: datetime,
    sanitized_fields: dict[str, Any],
) -> None:
    """Non-blocking, fail-safe database persistence for structured audit records."""
    try:
        from app.db.session import SessionLocal

        with SessionLocal() as db:
            course_val = sanitized_fields.get("course_id")
            assignment_val = sanitized_fields.get("assignment_id")

            record = AuditRecord(
                event=event,
                timestamp=timestamp,
                workflow_type=sanitized_fields.get("workflow_type"),
                actor_user_id=sanitized_fields.get("actor_user_id"),
                course_id=str(course_val) if course_val is not None else None,
                assignment_id=str(assignment_val) if assignment_val is not None else None,
                run_id=sanitized_fields.get("run_id"),
                status_code=sanitized_fields.get("status_code"),
                payload=sanitized_fields,
            )
            db.add(record)
            db.commit()
    except Exception as exc:
        # DB failure must never break execution or the primary audit logging stream
        logger.debug("Failed to record audit event in database: %s", exc)


def get_audit_records(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    event: str | None = None,
    workflow_type: str | None = None,
    actor_user_id: int | None = None,
    course_id: str | None = None,
    run_id: int | None = None,
    search: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> tuple[list[AuditRecord], int]:
    """Retrieve paginated audit records with optional filters."""
    query = select(AuditRecord)

    if event:
        query = query.where(AuditRecord.event == event)
    if workflow_type:
        query = query.where(AuditRecord.workflow_type == workflow_type)
    if actor_user_id is not None:
        query = query.where(AuditRecord.actor_user_id == actor_user_id)
    if course_id:
        query = query.where(AuditRecord.course_id == course_id)
    if run_id is not None:
        query = query.where(AuditRecord.run_id == run_id)
    if start_time:
        query = query.where(AuditRecord.timestamp >= start_time)
    if end_time:
        query = query.where(AuditRecord.timestamp <= end_time)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            AuditRecord.event.ilike(search_pattern)
            | AuditRecord.course_id.ilike(search_pattern)
            | AuditRecord.workflow_type.ilike(search_pattern)
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    records_query = (
        query.order_by(AuditRecord.timestamp.desc(), AuditRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = list(db.scalars(records_query).all())
    return records, total


def get_audit_stats(db: Session) -> dict[str, Any]:
    """Calculate overview statistics for the administrative dashboard."""
    now = datetime.now(UTC)
    twenty_four_hours_ago = now - timedelta(hours=24)

    total_events = db.scalar(select(func.count(AuditRecord.id))) or 0
    events_24h = (
        db.scalar(
            select(func.count(AuditRecord.id)).where(AuditRecord.timestamp >= twenty_four_hours_ago)
        )
        or 0
    )
    pii_redacted_count = (
        db.scalar(
            select(func.count(AuditRecord.id)).where(AuditRecord.event == "audit.pii_redacted")
        )
        or 0
    )
    access_denied_count = (
        db.scalar(
            select(func.count(AuditRecord.id)).where(AuditRecord.event == "auth.access_denied")
        )
        or 0
    )

    event_distribution_query = (
        select(AuditRecord.event, func.count(AuditRecord.id))
        .group_by(AuditRecord.event)
        .order_by(func.count(AuditRecord.id).desc())
        .limit(10)
    )
    event_counts = dict(db.execute(event_distribution_query).all())

    return {
        "total_events": total_events,
        "events_24h": events_24h,
        "pii_redacted_count": pii_redacted_count,
        "access_denied_count": access_denied_count,
        "event_counts": event_counts,
    }


def verify_audit_records(db: Session, limit: int = 500) -> dict[str, Any]:
    """Scan recent audit records against canonical FERPA regex patterns."""
    records_query = select(AuditRecord).order_by(AuditRecord.id.desc()).limit(limit)
    records = list(db.scalars(records_query).all())

    violations: list[dict[str, Any]] = []

    for record in records:
        payload = record.payload or {}
        # 1. Verify all payload keys are in ALLOWED_AUDIT_FIELDS
        unallowlisted = set(payload.keys()) - ALLOWED_AUDIT_FIELDS
        if unallowlisted:
            violations.append({
                "record_id": record.id,
                "timestamp": record.timestamp.isoformat(),
                "event": record.event,
                "field": sorted(unallowlisted)[0],
                "matched_rule": "ALLOWLIST_VIOLATION",
            })
            continue

        # 2. Verify all string values against canonical PII patterns
        def check_val(key_name: str, val: Any) -> None:
            if isinstance(val, str):
                for pattern, replacement in LOG_REDACTION_RULES:
                    if pattern.search(val):
                        violations.append({
                            "record_id": record.id,
                            "timestamp": record.timestamp.isoformat(),
                            "event": record.event,
                            "field": key_name,
                            "matched_rule": pattern.pattern,
                        })
                        return
            elif isinstance(val, dict):
                for sub_k, sub_v in val.items():
                    check_val(f"{key_name}.{sub_k}", sub_v)
            elif isinstance(val, list | tuple):
                for idx, item in enumerate(val):
                    check_val(f"{key_name}[{idx}]", item)

        for k, v in payload.items():
            check_val(k, v)

    return {
        "compliant": len(violations) == 0,
        "records_scanned": len(records),
        "violations_count": len(violations),
        "violations": violations[:50],  # Return up to 50 violations for inspection
        "checked_at": datetime.now(UTC).isoformat(),
        "disclaimer": (
            "Pattern scanning validates automated scrubbers (Canvas filenames, emails, "
            "U-numbers, workspace segments, tokens); it does not detect unpatterned student names or grades."
        ),
    }


def prune_expired_audit_records(db: Session, retention_days: int = 90) -> int:
    """Prune audit records older than the retention window (default: 90 days)."""
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    result = db.query(AuditRecord).filter(AuditRecord.timestamp < cutoff).delete(synchronize_session=False)
    db.commit()
    return int(result)

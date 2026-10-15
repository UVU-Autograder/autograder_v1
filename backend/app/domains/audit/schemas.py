from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event: str
    workflow_type: str | None = None
    actor_user_id: int | None = None
    course_id: str | None = None
    assignment_id: str | None = None
    run_id: int | None = None
    status_code: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AuditLogListResponse(BaseModel):
    items: list[AuditRecordOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditStatsResponse(BaseModel):
    total_events: int
    events_24h: int
    pii_redacted_count: int
    access_denied_count: int
    event_counts: dict[str, int]


class AuditViolationItem(BaseModel):
    record_id: int
    timestamp: str
    event: str
    field: str
    matched_rule: str


class AuditVerificationResponse(BaseModel):
    compliant: bool
    records_scanned: int
    violations_count: int
    violations: list[AuditViolationItem]
    checked_at: str
    disclaimer: str

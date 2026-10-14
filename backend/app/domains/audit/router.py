from __future__ import annotations

import math
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import DbSession, require_role
from app.domains.audit.schemas import (
    AuditLogListResponse,
    AuditRecordOut,
    AuditStatsResponse,
    AuditVerificationResponse,
)
from app.domains.audit.service import (
    get_audit_records,
    get_audit_stats,
    verify_audit_records,
)

router = APIRouter(
    prefix="/staff/admin/logs",
    tags=["staff-admin"],
    dependencies=[Depends(require_role(["admin"]))],
)


@router.get("", response_model=AuditLogListResponse)
def list_logs_admin(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    event: str | None = Query(default=None),
    workflow_type: str | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    course_id: str | None = Query(default=None),
    run_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
) -> AuditLogListResponse:
    """Retrieve filtered and paginated audit records for administrators."""
    records, total = get_audit_records(
        db=db,
        page=page,
        page_size=page_size,
        event=event,
        workflow_type=workflow_type,
        actor_user_id=actor_user_id,
        course_id=course_id,
        run_id=run_id,
        search=search,
        start_time=start_time,
        end_time=end_time,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return AuditLogListResponse(
        items=[AuditRecordOut.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=AuditStatsResponse)
def get_log_stats_admin(db: DbSession) -> AuditStatsResponse:
    """Retrieve aggregate telemetry and volume counts across audit records."""
    stats = get_audit_stats(db)
    return AuditStatsResponse(**stats)


@router.post("/verify", response_model=AuditVerificationResponse)
def verify_logs_admin(
    db: DbSession,
    limit: int = Query(default=500, ge=10, le=2000),
) -> AuditVerificationResponse:
    """Run an automated FERPA compliance pattern scan across recent audit records."""
    result = verify_audit_records(db, limit=limit)
    return AuditVerificationResponse(**result)

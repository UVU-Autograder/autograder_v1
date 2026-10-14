from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.audit_log import audit_event
from app.db.session import SessionLocal
from app.domains.audit.models import AuditRecord
from app.domains.audit.service import (
    get_audit_records,
    get_audit_stats,
    prune_expired_audit_records,
    verify_audit_records,
)
from app.main import create_app


@pytest.fixture
def db_session(reset_database):
    with SessionLocal() as db:
        yield db


def test_audit_event_persists_to_database(db_session):
    """Verify that calling audit_event writes a structured record to audit_records table."""
    audit_event(
        "official.run_completed",
        run_id=42,
        course_id="cs1400",
        assignment_id="m1",
        workflow_type="official",
        success_count=20,
    )

    records, total = get_audit_records(db_session, event="official.run_completed")
    assert total >= 1
    match = next(r for r in records if r.run_id == 42)
    assert match.event == "official.run_completed"
    assert match.workflow_type == "official"
    assert match.course_id == "cs1400"
    assert match.payload["success_count"] == 20


def test_get_audit_records_filtering_and_search(db_session):
    """Test filtering by event, workflow_type, and search pattern."""
    audit_event("sandbox.run_completed", run_id=101, workflow_type="sandbox")
    audit_event("auth.access_denied", status_code=403, denial_reason="Unauthorized")
    audit_event("audit.pii_redacted", workflow_type="logging")

    # Filter by event
    records, total = get_audit_records(db_session, event="auth.access_denied")
    assert total >= 1
    assert all(r.event == "auth.access_denied" for r in records)

    # Filter by workflow_type
    records, total = get_audit_records(db_session, workflow_type="sandbox")
    assert total >= 1
    assert all(r.workflow_type == "sandbox" for r in records)

    # Search filter
    records, total = get_audit_records(db_session, search="pii_redacted")
    assert total >= 1
    assert any("pii_redacted" in r.event for r in records)


def test_get_audit_stats(db_session):
    """Test overview statistics calculation."""
    audit_event("auth.access_denied", status_code=401, denial_reason="No token")
    audit_event("audit.pii_redacted", workflow_type="logging")
    audit_event("official.run_completed", run_id=102, workflow_type="official")

    stats = get_audit_stats(db_session)
    assert stats["total_events"] >= 3
    assert stats["events_24h"] >= 3
    assert stats["pii_redacted_count"] >= 1
    assert stats["access_denied_count"] >= 1
    assert "auth.access_denied" in stats["event_counts"]


def test_verify_audit_records_clean(db_session):
    """Verify that compliant audit records pass the FERPA pattern verification scan."""
    audit_event("official.run_completed", run_id=105, course_id="cs1400", workflow_type="official")
    audit_event("auth.access_denied", status_code=403, denial_reason="Forbidden")

    result = verify_audit_records(db_session)
    assert result["compliant"] is True
    assert result["violations_count"] == 0
    assert result["records_scanned"] >= 2
    assert "disclaimer" in result


def test_verify_audit_records_detects_violations(db_session):
    """Verify that unallowlisted fields or residual PII patterns are flagged by verify_audit_records."""
    # Manually insert a record with residual PII in payload
    dirty_record = AuditRecord(
        event="test.dirty_event",
        timestamp=datetime.now(UTC),
        payload={"denial_reason": "Failed for student U12345678"},
    )
    db_session.add(dirty_record)

    # Manually insert a record with unallowlisted field
    unallowlisted_record = AuditRecord(
        event="test.unallowlisted_event",
        timestamp=datetime.now(UTC),
        payload={"student_name": "John Doe"},
    )
    db_session.add(unallowlisted_record)
    db_session.commit()

    result = verify_audit_records(db_session)
    assert result["compliant"] is False
    assert result["violations_count"] >= 2
    matched_rules = {v["matched_rule"] for v in result["violations"]}
    assert "UVU_STUDENT_ID" in matched_rules or "ALLOWLIST_VIOLATION" in matched_rules


def test_prune_expired_audit_records(db_session):
    """Verify that records older than retention_days are pruned."""
    now = datetime.now(UTC)
    old_record = AuditRecord(
        event="old.event",
        timestamp=now - timedelta(days=95),
        payload={"workflow_type": "official"},
    )
    recent_record = AuditRecord(
        event="recent.event",
        timestamp=now - timedelta(days=5),
        payload={"workflow_type": "official"},
    )
    db_session.add(old_record)
    db_session.add(recent_record)
    db_session.commit()

    pruned = prune_expired_audit_records(db_session, retention_days=90)
    assert pruned >= 1

    records, _ = get_audit_records(db_session, event="old.event")
    assert len(records) == 0

    records, _ = get_audit_records(db_session, event="recent.event")
    assert len(records) >= 1


def test_admin_logs_api_authorization(reset_database):
    """Verify that /staff/admin/logs requires authentication and admin role."""
    app = create_app()
    client = TestClient(app)

    # Unauthenticated -> 401
    res = client.get("/staff/admin/logs")
    assert res.status_code == 401

    res = client.get("/staff/admin/logs/stats")
    assert res.status_code == 401

    res = client.post("/staff/admin/logs/verify")
    assert res.status_code == 401


def test_admin_logs_api_admin_access(reset_database):
    """Verify that admin user can query logs, stats, and run verification."""
    from app.core.auth_utils import create_access_token
    from app.domains.auth.models import Role, User, StaffAccess

    with SessionLocal() as db:
        admin_user = User(email="admin_user@uvu.edu", display_name="Admin User")
        db.add(admin_user)
        db.flush()

        admin_role = db.query(Role).filter_by(name="admin").first()
        access = StaffAccess(user_id=admin_user.id, role_id=admin_role.id)
        db.add(access)
        db.commit()
        admin_id = admin_user.id

    token = create_access_token(email="admin_user@uvu.edu", display_name="Admin User", user_id=admin_id)
    headers = {"Authorization": f"Bearer {token}"}

    app = create_app()
    client = TestClient(app)

    # Emit an event
    audit_event("official.run_completed", run_id=200, course_id="cs1400", workflow_type="official")

    # GET /staff/admin/logs
    res = client.get("/staff/admin/logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 1
    assert any(item["run_id"] == 200 for item in data["items"])

    # GET /staff/admin/logs/stats
    res = client.get("/staff/admin/logs/stats", headers=headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_events" in stats
    assert stats["total_events"] >= 1

    # POST /staff/admin/logs/verify
    res = client.post("/staff/admin/logs/verify", headers=headers)
    assert res.status_code == 200
    verify_data = res.json()
    assert "compliant" in verify_data
    assert "records_scanned" in verify_data

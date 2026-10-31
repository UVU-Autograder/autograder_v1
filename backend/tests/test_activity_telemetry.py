"""Tests for sandbox activity telemetry aggregation, attempt distributions, and error bottlenecks."""
import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import status
from sqlalchemy import select

from app.core.auth_utils import create_access_token
from app.db.session import SessionLocal
from app.domains.assignments.models import Assignment
from app.domains.auth.models import User
from app.domains.courses.models import Course
from app.domains.runs.activity import (
    get_course_activity_summary,
    get_system_activity_summary,
    record_sandbox_ai_telemetry,
    record_sandbox_telemetry,
)
from app.domains.runs.models import RunSummary


def auth_headers(email: str, display_name: str) -> dict[str, str]:
    token = create_access_token(email=email, display_name=display_name)
    return {"Authorization": f"Bearer {token}"}


def test_record_sandbox_telemetry_persists_anonymized_data(reset_database):
    with SessionLocal() as db:
        assignment = db.scalar(select(Assignment))
        assert assignment is not None

        raw_session = "test_student_session_abc123"
        expected_hash = hashlib.sha256(raw_session.encode("utf-8")).hexdigest()

        record_sandbox_telemetry(
            assignment_id=assignment.id,
            session_id=raw_session,
            status="complete",
            failure_category=None,
            failure_summary={"test_key": "passed"},
            grade_seconds=1.25,
        )

        record = db.scalar(
            select(RunSummary)
            .where(
                RunSummary.assignment_id == assignment.id,
                RunSummary.sandbox_session_hash == expected_hash,
            )
            .order_by(RunSummary.id.desc())
        )

        assert record is not None
        assert record.workflow_type == "sandbox"
        assert record.status == "complete"
        assert record.success_count == 1
        assert record.failure_count == 0
        assert record.export_packaging_seconds == 1.25
        # Ensure raw session is never stored
        assert record.sandbox_session_hash != raw_session
        assert record.sandbox_session_hash == expected_hash


def test_record_sandbox_ai_telemetry(reset_database):
    with SessionLocal() as db:
        assignment = db.scalar(select(Assignment))
        assert assignment is not None

        raw_session = "ai_student_session_xyz"
        record_sandbox_ai_telemetry(
            assignment_id=assignment.id,
            session_id=raw_session,
            token_usage={"total_tokens": 120, "prompt_tokens": 80, "completion_tokens": 40},
        )

        record = db.scalar(
            select(RunSummary)
            .where(
                RunSummary.assignment_id == assignment.id,
                RunSummary.workflow_type == "sandbox_ai",
            )
            .order_by(RunSummary.id.desc())
        )

        assert record is not None
        assert record.token_usage_metadata == {"total_tokens": 120, "prompt_tokens": 80, "completion_tokens": 40}


def test_get_system_and_course_activity_summary(reset_database):
    with SessionLocal() as db:
        course = db.scalar(select(Course).where(Course.code == "cs1400"))
        assert course is not None
        assignment = db.scalar(select(Assignment).where(Assignment.course_id == course.id))
        assert assignment is not None

        # Insert 3 test runs: 2 from session A (1 pass, 1 fail) and 1 from session B (1 fail with syntax error)
        now = datetime.now(UTC)
        hash_a = hashlib.sha256(b"session_a").hexdigest()
        hash_b = hashlib.sha256(b"session_b").hexdigest()

        r1 = RunSummary(
            workflow_type="sandbox",
            assignment_id=assignment.id,
            sandbox_session_hash=hash_a,
            status="complete",
            total_submission_count=1,
            success_count=1,
            failure_count=0,
            created_at=now - timedelta(hours=2),
        )
        r2 = RunSummary(
            workflow_type="sandbox",
            assignment_id=assignment.id,
            sandbox_session_hash=hash_a,
            status="failure",
            total_submission_count=1,
            success_count=0,
            failure_count=1,
            failure_summary={"failure_category": "assertion", "failed_keys": ["ag_test_math"]},
            created_at=now - timedelta(hours=1),
        )
        r3 = RunSummary(
            workflow_type="sandbox",
            assignment_id=assignment.id,
            sandbox_session_hash=hash_b,
            status="failure",
            total_submission_count=1,
            success_count=0,
            failure_count=1,
            failure_summary={"failure_category": "syntax_error"},
            created_at=now - timedelta(minutes=30),
        )
        r_ai = RunSummary(
            workflow_type="sandbox_ai",
            assignment_id=assignment.id,
            sandbox_session_hash=hash_a,
            status="complete",
            token_usage_metadata={"total_tokens": 250},
            created_at=now - timedelta(minutes=15),
        )

        db.add_all([r1, r2, r3, r_ai])
        db.commit()

        # Test System Summary
        sys_summary = get_system_activity_summary(db, window_hours=24)
        assert sys_summary.total_sandbox_runs >= 3
        assert sys_summary.active_student_sessions >= 2
        assert sys_summary.total_ai_tokens >= 250
        assert len(sys_summary.velocity) > 0
        assert len(sys_summary.attempt_distribution) == 5

        # Check that top bottlenecks caught the test failure
        bottleneck_keys = [b.key for b in sys_summary.top_bottlenecks]
        assert "ag_test_math" in bottleneck_keys or "Syntax Error" in bottleneck_keys

        # Test Course Summary
        course_summary = get_course_activity_summary(db, "cs1400", window_hours=24)
        assert course_summary is not None
        assert course_summary.course_code == "cs1400"
        assert course_summary.total_sandbox_runs >= 3
        assert course_summary.active_student_sessions >= 2


def test_admin_activity_endpoint(client):
    headers = auth_headers("dev.staff@uvu.edu", "Admin User")
    res = client.get("/staff/admin/activity?window_hours=48", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    data = res.json()
    assert "total_sandbox_runs" in data
    assert "active_student_sessions" in data
    assert "overall_pass_rate" in data
    assert "velocity" in data
    assert "attempt_distribution" in data
    assert "top_bottlenecks" in data
    assert "assignments" in data


def test_course_activity_endpoint_scoped_access(client):
    admin_headers = auth_headers("dev.staff@uvu.edu", "Admin User")

    # Admin access succeeds
    res = client.get("/staff/courses/cs1400/activity", headers=admin_headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["course_code"] == "cs1400"

    # User with no access receives 403
    with SessionLocal() as db:
        unassigned = User(email="random.staff@uvu.edu", display_name="Random Staff")
        db.add(unassigned)
        db.commit()

    unassigned_headers = auth_headers("random.staff@uvu.edu", "Random Staff")
    res = client.get("/staff/courses/cs1400/activity", headers=unassigned_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

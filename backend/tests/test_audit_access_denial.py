import json
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.audit_log import ALLOWED_AUDIT_FIELDS
from app.core.auth_utils import create_access_token
from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Section
from app.main import create_app


@pytest.fixture(autouse=True)
def initialized_database(reset_database):
    yield


@pytest.fixture
def client():
    return TestClient(create_app())


def get_denial_events(caplog) -> list[dict]:
    events = []
    for record in caplog.records:
        if record.name == "autograder.audit":
            try:
                payload = json.loads(record.message)
                if payload.get("audit_event") == "auth.access_denied":
                    events.append(payload)
            except (json.JSONDecodeError, TypeError):
                pass
    return events


def test_unauthenticated_request_emits_audit_denial(client, caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")
    res = client.get("/staff/courses")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    events = get_denial_events(caplog)
    assert len(events) >= 1
    event = events[-1]
    assert event["status_code"] == 401
    assert event["path"] == "/staff/courses"
    assert event["http_method"] == "GET"
    assert "actor_user_id" not in event
    assert "denial_reason" in event


def test_cross_course_unauthorized_access_emits_audit_denial(client, caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")

    with SessionLocal() as db:
        user = User(email="instructor1400@uvu.edu", display_name="CS1400 Instructor")
        db.add(user)
        role = db.scalar(select(Role).where(Role.name == "instructor"))
        course_1400 = db.scalar(select(Course).where(Course.code == "cs1400"))
        section_1400 = db.scalar(select(Section).where(Section.course_id == course_1400.id))
        access = StaffAccess(user=user, role=role, course=course_1400, section=section_1400, is_active=True)
        db.add(access)
        db.commit()
        user_id = user.id

    token = create_access_token(email="instructor1400@uvu.edu", display_name="CS1400 Instructor", user_id=user_id)
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to access cs1410 assignments (not assigned to this instructor)
    res = client.get("/staff/courses/cs1410/assignments", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    events = get_denial_events(caplog)
    assert len(events) >= 1
    event = events[-1]
    assert event["status_code"] == 403
    assert event["path"] == "/staff/courses/cs1410/assignments"
    assert event["http_method"] == "GET"
    assert event["actor_user_id"] == user_id
    assert "denial_reason" in event


def test_ia_role_mutation_emits_audit_denial(client, caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")

    with SessionLocal() as db:
        ia_user = User(email="ia1400@uvu.edu", display_name="CS1400 IA")
        db.add(ia_user)
        role = db.scalar(select(Role).where(Role.name == "IA"))
        course_1400 = db.scalar(select(Course).where(Course.code == "cs1400"))
        section_1400 = db.scalar(select(Section).where(Section.course_id == course_1400.id))
        access = StaffAccess(user=ia_user, role=role, course=course_1400, section=section_1400, is_active=True)
        db.add(access)
        db.commit()
        ia_id = ia_user.id

    token = create_access_token(email="ia1400@uvu.edu", display_name="CS1400 IA", user_id=ia_id)
    headers = {"Authorization": f"Bearer {token}"}

    # IA attempting mutation on assignment setup
    res = client.put(
        "/staff/courses/cs1400/assignments/simple-python-functions/setup",
        headers=headers,
        json={"title": "Updated Title"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    events = get_denial_events(caplog)
    assert len(events) >= 1
    event = events[-1]
    assert event["status_code"] == 403
    assert event["http_method"] == "PUT"
    assert event["actor_user_id"] == ia_id
    assert event["path"] == "/staff/courses/cs1400/assignments/simple-python-functions/setup"


def test_invalid_and_expired_token_emits_audit_denial(client, caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")

    # 1. Malformed token
    res = client.get("/staff/courses", headers={"Authorization": "Bearer not-a-valid-token"})
    assert res.status_code == status.HTTP_401_UNAUTHORIZED

    events = get_denial_events(caplog)
    assert len(events) >= 1
    event = events[-1]
    assert event["status_code"] == 401
    assert "actor_user_id" not in event

    # 2. Expired token
    settings = get_settings()
    expired_payload = {
        "email": "dev.staff@uvu.edu",
        "name": "Dev Staff",
        "exp": datetime.now(UTC) - timedelta(minutes=10),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    res2 = client.get("/staff/courses", headers={"Authorization": f"Bearer {expired_token}"})
    assert res2.status_code == status.HTTP_401_UNAUTHORIZED

    events2 = get_denial_events(caplog)
    assert len(events2) >= 2
    event2 = events2[-1]
    assert event2["status_code"] == 401
    assert "expired" in event2["denial_reason"].lower()


def test_audit_logs_contain_no_raw_pii_and_only_allowlisted_fields(client, caplog):
    caplog.set_level(logging.INFO, logger="autograder.audit")

    client.get("/staff/courses?raw_student_param=student_12345", headers={"Authorization": "Bearer bad-token"})

    events = get_denial_events(caplog)
    assert len(events) >= 1
    for event in events:
        for key in event:
            if key in ("audit_event", "timestamp"):
                continue
            assert key in ALLOWED_AUDIT_FIELDS, f"Field {key} not in allowlist!"
        if "denial_reason" in event:
            assert "student_12345" not in event["denial_reason"]

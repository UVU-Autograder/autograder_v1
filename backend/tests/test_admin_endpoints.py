import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from app.core.auth_utils import create_access_token
from app.db.session import SessionLocal
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Section
from app.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy import select


@pytest.fixture(autouse=True)
def initialized_database(reset_database):
    yield

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def admin_token():
    # dev.staff@uvu.edu is seeded as an admin role
    return create_access_token(email="dev.staff@uvu.edu", display_name="Dev Admin Staff")

@pytest.fixture
def non_admin_token(db_session):
    # Create an instructor-only user
    email = "instructor.test@uvu.edu"
    user = db_session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, display_name="Test Instructor", is_active=True)
        db_session.add(user)
        db_session.flush()

        role = db_session.scalar(select(Role).where(Role.name == "instructor"))
        course = db_session.scalar(select(Course).where(Course.code == "cs1400"))
        section = db_session.scalar(select(Section).where(Section.course_id == course.id))

        access = StaffAccess(
            user=user,
            role=role,
            course=course,
            section=section,
            is_active=True,
        )
        db_session.add(access)
        db_session.commit()
    return create_access_token(email=email, display_name="Test Instructor")

# 1. Access Control Tests

def test_admin_endpoints_require_admin(client, non_admin_token):
    headers = {"Authorization": f"Bearer {non_admin_token}"}

    # Get courses
    response = client.get("/staff/admin/courses", headers=headers)
    assert response.status_code == 403

    # Post course
    response = client.post("/staff/admin/courses", json={"code": "cs2420", "title": "CS 2420", "term": "Fall 2026"}, headers=headers)
    assert response.status_code == 403

def test_admin_endpoints_allow_admin(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/staff/admin/courses", headers=headers)
    assert response.status_code == 200

# 2. Course CRUD Tests

def test_course_crud(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create
    response = client.post(
        "/staff/admin/courses",
        json={"code": "cs2420", "title": "Data Structures", "term": "Fall 2026", "default_concepts": ["trees", "recursion"]},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "cs2420"
    assert data["title"] == "Data Structures"
    assert "trees" in data["default_concepts"]
    course_id = data["id"]

    # Read/List
    response = client.get("/staff/admin/courses", headers=headers)
    assert response.status_code == 200
    course_codes = [c["code"] for c in response.json()]
    assert "cs2420" in course_codes

    # Update
    response = client.put(
        f"/staff/admin/courses/{course_id}",
        json={"title": "Data Structures & Algorithms", "term": "Spring 2027"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Data Structures & Algorithms"
    assert response.json()["term"] == "Spring 2027"

    # Deactivate (Delete)
    response = client.delete(f"/staff/admin/courses/{course_id}", headers=headers)
    assert response.status_code == 204

    # Verify deactivated
    c = db_session.get(Course, course_id)
    assert c.is_active is False


def test_create_course_with_instructor_grants_section_access(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post(
        "/staff/admin/courses",
        json={
            "code": "cs2550",
            "title": "Networks",
            "term": "Fall 2026",
            "instructor_email": "new.instructor@uvu.edu",
            "instructor_name": "New Instructor",
        },
        headers=headers,
    )
    assert response.status_code == 201
    course_id = response.json()["id"]

    user = db_session.scalar(select(User).where(User.email == "new.instructor@uvu.edu"))
    assert user is not None
    access = db_session.scalar(
        select(StaffAccess).where(
            StaffAccess.user_id == user.id,
            StaffAccess.course_id == course_id,
        )
    )
    assert access is not None
    assert access.section_id is not None
    section = db_session.get(Section, access.section_id)
    assert section is not None
    assert section.course_id == course_id

# 3. Section CRUD Tests

def test_section_crud(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    course = db_session.scalar(select(Course).where(Course.code == "cs1400"))

    # Create
    response = client.post(
        f"/staff/admin/courses/{course.id}/sections",
        json={"crn": "99999"},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["crn"] == "99999"
    section_id = data["id"]

    # List
    response = client.get(f"/staff/admin/courses/{course.id}/sections", headers=headers)
    assert response.status_code == 200
    crns = [s["crn"] for s in response.json()]
    assert "99999" in crns

    # Update
    response = client.put(
        f"/staff/admin/sections/{section_id}",
        json={"crn": "88888"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["crn"] == "88888"

    # Deactivate
    response = client.delete(f"/staff/admin/sections/{section_id}", headers=headers)
    assert response.status_code == 204

    # Verify deactivated
    s = db_session.get(Section, section_id)
    assert s.is_active is False

# 4. Access Grant / Revoke Tests

def test_staff_access_management(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    course = db_session.scalar(select(Course).where(Course.code == "cs1400"))
    section = db_session.scalar(select(Section).where(Section.course_id == course.id))

    email = "new.assistant@uvu.edu"

    # Grant
    response = client.post(
        "/staff/admin/access",
        json={
            "email": email,
            "display_name": "New IA",
            "role_name": "IA",
            "course_id": course.id,
            "section_id": section.id
        },
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_email"] == email
    assert data["role_name"] == "IA"
    assert data["is_active"] is True
    access_id = data["id"]

    # List
    response = client.get("/staff/admin/access", headers=headers)
    assert response.status_code == 200
    emails = [a["user_email"] for a in response.json()]
    assert email in emails

    # Revoke
    response = client.delete(f"/staff/admin/access/{access_id}", headers=headers)
    assert response.status_code == 204

    # Verify revoked
    access = db_session.get(StaffAccess, access_id)
    assert access.is_active is False


def test_staff_access_admin_and_instructor_roles(client, admin_token, db_session):
    headers = {"Authorization": f"Bearer {admin_token}"}
    course = db_session.scalar(select(Course).where(Course.code == "cs1400"))

    # Admin grant (no course_id, no section_id)
    res = client.post(
        "/staff/admin/access",
        json={"email": "global.admin@uvu.edu", "role_name": "admin"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["role_name"] == "admin"
    assert data["course_id"] is None
    assert data["section_id"] is None

    # Instructor grant (course_id provided, section_id omitted)
    res = client.post(
        "/staff/admin/access",
        json={"email": "course.instructor@uvu.edu", "role_name": "instructor", "course_id": course.id},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["role_name"] == "instructor"
    assert data["course_id"] == course.id
    assert data["section_id"] is not None


# 5. Monitoring Test

def test_monitoring_endpoint(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/staff/admin/monitoring", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "active_runs_count" in data
    assert "queued_runs_count" in data
    assert "sandbox_runs_last_hour" in data
    assert "total_token_usage" in data

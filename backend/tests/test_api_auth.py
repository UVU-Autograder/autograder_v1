import sys
from pathlib import Path
import pytest
from fastapi import Depends, status
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app
from app.core.dependencies import get_current_user
from app.domains.auth.models import User, Role, StaffAccess
from app.db.session import SessionLocal, get_db


@pytest.fixture(autouse=True)
def initialized_database(reset_database):
    yield


@pytest.fixture
def client():
    return TestClient(create_app())


def test_staff_endpoints_allow_default_dev_staff(client):
    # By default, require_staff returns dev.staff@uvu.edu (seeded as admin).
    # All staff routes should respond successfully (200 status code).
    from app.core.auth_utils import create_access_token
    token = create_access_token(email="dev.staff@uvu.edu", display_name="Dev Staff")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Courses list
    res = client.get("/staff/courses", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert "courses" in res.json()

    # 2. Assignment setup
    res = client.get("/staff/courses/cs1400/assignments/simple-python-functions/setup", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["assignment_id"] == "simple-python-functions"

    # 3. Artifacts list
    res = client.get("/staff/courses/cs1400/assignments/simple-python-functions/artifacts", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    assert "artifacts" in res.json()


def test_staff_endpoints_block_non_staff_user(client):
    # Seed a non-staff user
    with SessionLocal() as db:
        student = User(email="student@uvu.edu", display_name="Student User")
        db.add(student)
        db.commit()
        student_id = student.id

    app = client.app

    # Override get_current_user to return the student user using the request's db session
    def override_get_current_user(db=Depends(get_db)):
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        stmt = select(User).where(User.id == student_id).options(selectinload(User.staff_access))
        return db.scalar(stmt)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        # 1. Courses list should be Forbidden
        res = client.get("/staff/courses")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert res.json()["detail"] == "Staff access required."

        # 2. Assignment setup should be Forbidden
        res = client.get("/staff/courses/cs1400/assignments/simple-python-functions/setup")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert res.json()["detail"] == "Staff access required."

        # 3. Artifacts list should be Forbidden
        res = client.get("/staff/courses/cs1400/assignments/simple-python-functions/artifacts")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert res.json()["detail"] == "Staff access required."
    finally:
        app.dependency_overrides.clear()


def test_staff_endpoints_allow_other_roles(client):
    # Seed a user with instructor role for CS1400
    with SessionLocal() as db:
        instructor = User(email="instructor@uvu.edu", display_name="Instructor User")
        db.add(instructor)
        
        from sqlalchemy import select
        instructor_role = db.scalar(select(Role).where(Role.name == "instructor"))
        from app.domains.courses.models import Course, Section
        course = db.scalar(select(Course).where(Course.code == "cs1400"))
        section = db.scalar(select(Section).where(Section.course_id == course.id))
        
        access = StaffAccess(
            user=instructor,
            role=instructor_role,
            course=course,
            section=section,
            is_active=True
        )
        db.add(access)
        db.commit()
        instructor_id = instructor.id

    app = client.app

    def override_get_current_user(db=Depends(get_db)):
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        stmt = select(User).where(User.id == instructor_id).options(selectinload(User.staff_access))
        return db.scalar(stmt)

    app.dependency_overrides[get_current_user] = override_get_current_user

    try:
        # Instructor should have access
        res = client.get("/staff/courses")
        assert res.status_code == status.HTTP_200_OK

        res = client.get("/staff/courses/cs1400/assignments/simple-python-functions/setup")
        assert res.status_code == status.HTTP_200_OK
    finally:
        app.dependency_overrides.clear()


def test_ia_cannot_put_assignment_setup(client):
    from sqlalchemy import select
    from app.core.auth_utils import create_access_token
    from app.domains.courses.models import Course, Section

    with SessionLocal() as db:
        ia_role = db.scalar(select(Role).where(Role.name == "IA"))
        course = db.scalar(select(Course).where(Course.code == "cs1400"))
        section = db.scalar(select(Section).where(Section.course_id == course.id))

        ia_user = User(email="ia.only@uvu.edu", display_name="IA Only")
        db.add(ia_user)
        db.flush()
        db.add(
            StaffAccess(
                user=ia_user,
                role=ia_role,
                course=course,
                section=section,
                is_active=True,
            )
        )
        db.commit()

    token = create_access_token(email="ia.only@uvu.edu", display_name="IA Only")
    headers = {"Authorization": f"Bearer {token}"}

    res = client.put(
        "/staff/courses/cs1400/assignments/simple-python-functions/setup",
        headers=headers,
        json={"title": "Updated Title"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

import sys
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.auth_utils import create_access_token
from app.db.session import SessionLocal
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course
from app.main import create_app


@pytest.fixture(autouse=True)
def initialized_database(reset_database):
    yield


@pytest.fixture
def client():
    return TestClient(create_app())


def auth_headers(email: str, display_name: str) -> dict[str, str]:
    token = create_access_token(email=email, display_name=display_name)
    return {"Authorization": f"Bearer {token}"}


def test_admin_has_unrestricted_course_access(client):
    headers = auth_headers("dev.staff@uvu.edu", "Admin User")

    # 1. Sees all courses
    res = client.get("/staff/courses", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    course_ids = [c["id"] for c in res.json()["courses"]]
    assert "cs1400" in course_ids

    # 2. Can read course concepts
    res = client.get("/staff/courses/cs1400/concepts", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # 3. Can update course concepts
    res = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={"default_concepts": ["variables"], "modules": []},
    )
    assert res.status_code == status.HTTP_200_OK

    # 4. Can read assignment setup
    res = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/setup",
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK


def test_course_list_filters_by_active_grants(client):
    with SessionLocal() as db:
        inst_role = db.scalar(select(Role).where(Role.name == "instructor"))
        course_1400 = db.scalar(select(Course).where(Course.code == "cs1400"))

        user = User(email="prof.single@uvu.edu", display_name="Prof Single")
        db.add(user)
        db.flush()
        db.add(
            StaffAccess(
                user=user,
                role=inst_role,
                course=course_1400,
                is_active=True,
            )
        )
        db.commit()

    headers = auth_headers("prof.single@uvu.edu", "Prof Single")
    res = client.get("/staff/courses", headers=headers)
    assert res.status_code == status.HTTP_200_OK
    courses = res.json()["courses"]
    assert len(courses) == 1
    assert courses[0]["id"] == "cs1400"


def test_instructor_cross_course_access_denied(client):
    with SessionLocal() as db:
        inst_role = db.scalar(select(Role).where(Role.name == "instructor"))
        course_1400 = db.scalar(select(Course).where(Course.code == "cs1400"))

        user = User(email="prof.1400only@uvu.edu", display_name="Prof 1400 Only")
        db.add(user)
        db.flush()
        db.add(
            StaffAccess(
                user=user,
                role=inst_role,
                course=course_1400,
                is_active=True,
            )
        )
        db.commit()

    headers = auth_headers("prof.1400only@uvu.edu", "Prof 1400 Only")

    # Accessing cs1400 succeeds
    res = client.get("/staff/courses/cs1400/assignments", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # Accessing cs1410 (unauthorized course) is rejected with 403
    res = client.get("/staff/courses/cs1410/assignments", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.get("/staff/courses/cs1410/concepts", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

    res = client.put(
        "/staff/courses/cs1410/concepts",
        headers=headers,
        json={"default_concepts": [], "modules": []},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_ia_read_only_access_to_assigned_course(client):
    with SessionLocal() as db:
        ia_role = db.scalar(select(Role).where(Role.name == "IA"))
        course_1400 = db.scalar(select(Course).where(Course.code == "cs1400"))

        user = User(email="ia.assigned@uvu.edu", display_name="IA Assigned")
        db.add(user)
        db.flush()
        db.add(
            StaffAccess(
                user=user,
                role=ia_role,
                course=course_1400,
                is_active=True,
            )
        )
        db.commit()

    headers = auth_headers("ia.assigned@uvu.edu", "IA Assigned")

    # 1. IA can list assignments on assigned course
    res = client.get("/staff/courses/cs1400/assignments", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # 2. IA can read concepts on assigned course
    res = client.get("/staff/courses/cs1400/concepts", headers=headers)
    assert res.status_code == status.HTTP_200_OK

    # 3. IA can read assignment setup on assigned course
    res = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/setup",
        headers=headers,
    )
    assert res.status_code == status.HTTP_200_OK

    # 4. IA CANNOT mutate concepts on assigned course
    res = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={"default_concepts": [], "modules": []},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 5. IA CANNOT mutate assignment setup on assigned course
    res = client.put(
        "/staff/courses/cs1400/assignments/simple-python-functions/setup",
        headers=headers,
        json={"title": "Hacked Title"},
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # 6. IA CANNOT access unassigned course
    res = client.get("/staff/courses/cs1410/assignments", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN

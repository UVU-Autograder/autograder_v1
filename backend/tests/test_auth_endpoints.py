import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unittest.mock import patch

import pytest
from app.core.auth_utils import create_access_token
from app.db.session import SessionLocal
from app.domains.auth.models import User
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

def test_mock_login_success(client, db_session):
    email = "new.staff@uvu.edu"
    # Ensure user does not exist initially
    user_before = db_session.scalar(select(User).where(User.email == email))
    if user_before:
        for access in user_before.staff_access:
            db_session.delete(access)
        db_session.delete(user_before)
        db_session.commit()

    response = client.post("/auth/mock-login", json={"email": email, "display_name": "New Staff"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == email
    assert data["display_name"] == "New Staff"
    assert data["roles"] == []

    # Verify user was provisioned
    user_after = db_session.scalar(select(User).where(User.email == email))
    assert user_after is not None
    assert user_after.display_name == "New Staff"
    assert user_after.is_active is True

def test_mock_login_invalid_email(client):
    response = client.post("/auth/mock-login", json={"email": "hacker@gmail.com"})
    assert response.status_code == 400
    assert "restricted to @uvu.edu" in response.json()["detail"]

def test_mock_login_disabled_in_prod(client):
    with patch("app.domains.auth.router.get_settings") as mock_settings:
        mock_settings.return_value.mock_login_enabled = False
        response = client.post("/auth/mock-login", json={"email": "prod.staff@uvu.edu"})
        assert response.status_code == 403
        assert "Mock login is disabled" in response.json()["detail"]

def test_get_current_user_dependency_missing_token(client):
    # Call a protected staff endpoint without header
    response = client.get("/staff/courses")
    assert response.status_code == 401
    assert "Authentication credentials were not provided" in response.json()["detail"]

def test_get_current_user_dependency_valid_token(client, db_session):
    email = "dev.staff@uvu.edu"
    token = create_access_token(email=email, display_name="Dev Staff")

    response = client.get("/staff/courses", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

def test_get_current_user_dependency_auto_provision(client, db_session):
    email = "unregistered.staff@uvu.edu"
    # Ensure user does not exist
    user = db_session.scalar(select(User).where(User.email == email))
    if user:
        for access in user.staff_access:
            db_session.delete(access)
        db_session.delete(user)
        db_session.commit()

    token = create_access_token(email=email, display_name="Unregistered User")

    # Calling `/staff/courses` should result in 403 Forbidden because they are
    # authenticated but have no staff access roles.
    response = client.get("/staff/courses", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert "Staff access required" in response.json()["detail"]

    # Verify user was automatically created in DB
    user_created = db_session.scalar(select(User).where(User.email == email))
    assert user_created is not None
    assert user_created.display_name == "Unregistered User"
    assert user_created.is_active is True

def test_get_current_user_dependency_inactive_user(client, db_session):
    email = "inactive.staff@uvu.edu"
    # Create inactive user in DB
    user = db_session.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email, display_name="Inactive User", is_active=False)
        db_session.add(user)
    else:
        user.is_active = False
    db_session.commit()

    token = create_access_token(email=email)

    response = client.get("/staff/courses", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "User is inactive" in response.json()["detail"]


def test_auth_me_returns_admin_roles(client):
    token = create_access_token(email="dev.staff@uvu.edu", display_name="Dev Staff")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "dev.staff@uvu.edu"
    assert "admin" in body["roles"]


def test_auth_me_non_admin_has_no_admin_role(client, db_session):
    from app.domains.auth.models import Role, StaffAccess

    email = "instructor.only@uvu.edu"
    user = db_session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, display_name="Instructor Only", is_active=True)
        db_session.add(user)
        db_session.flush()
    instructor_role = db_session.scalar(select(Role).where(Role.name == "instructor"))
    assert instructor_role is not None
    existing = [
        a for a in user.staff_access if a.role_id == instructor_role.id and a.is_active
    ]
    if not existing:
        db_session.add(
            StaffAccess(
                user_id=user.id,
                role_id=instructor_role.id,
                course_id=None,
                section_id=None,
                is_active=True,
            )
        )
    db_session.commit()

    token = create_access_token(email=email, display_name="Instructor Only")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert "instructor" in body["roles"]
    assert "admin" not in body["roles"]

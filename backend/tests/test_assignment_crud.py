import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domains.assignments.models import Assignment
from app.domains.courses.models import Course, Module
from sqlalchemy import select


# 1. Access Control Tests

def test_crud_endpoints_require_admin_or_instructor(client, ia_token, student_token):
    # Test IA role is blocked
    headers_ia = {"Authorization": f"Bearer {ia_token}"}
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json={"slug": "new-task", "title": "New Task"},
        headers=headers_ia,
    )
    assert response.status_code == 403

    response = client.delete(
        "/staff/courses/cs1400/assignments/simple-python-functions",
        headers=headers_ia,
    )
    assert response.status_code == 403

    # Test Student role is blocked
    headers_student = {"Authorization": f"Bearer {student_token}"}
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json={"slug": "new-task", "title": "New Task"},
        headers=headers_student,
    )
    assert response.status_code == 403


# 2. Assignment CRUD Tests

def test_create_assignment_success(client, instructor_token, db_session):
    headers = {"Authorization": f"Bearer {instructor_token}"}
    payload = {
        "slug": "lab-2-loops",
        "title": "Lab 2: Loops",
        "language": "python",
        "canvas_ref": "canvas:lab-2",
        "sandbox_enabled": True,
    }

    response = client.post(
        "/staff/courses/cs1400/assignments",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["assignment_id"] == "lab-2-loops"
    assert data["title"] == "Lab 2: Loops"
    assert data["language"] == "python"
    assert data["canvas_ref"] == "canvas:lab-2"
    assert data["sandbox_enabled"] is True
    assert data["base_points"] == 25  # Seed default has 25 base points
    assert len(data["scoring_items"]) == 3
    assert data["scoring_items"][0]["key"] == "add_numbers"

    # Verify db entry
    assignment = db_session.scalar(
        select(Assignment).where(
            Assignment.slug == "lab-2-loops",
            Assignment.is_active.is_(True)
        )
    )
    assert assignment is not None
    assert assignment.title == "Lab 2: Loops"
    assert assignment.config is not None


def test_create_assignment_duplicate_slug_blocked(client, instructor_token):
    headers = {"Authorization": f"Bearer {instructor_token}"}
    url = "/staff/courses/cs1400/assignments/simple-python-functions/setup"
    before = client.get(url, headers=headers).json()
    payload = {
        "slug": "simple-python-functions",
        "title": "Duplicate assignment",
        "canvas_ref": "canvas:replacement",
        "sandbox_enabled": False,
        "module_id": None,
    }
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 409
    assert client.get(url, headers=headers).json() == before


@pytest.mark.parametrize("module_source", ["other_course", "missing"])
def test_create_assignment_rejects_invalid_module_without_creating_assignment(
    client, instructor_token, db_session, module_source,
):
    headers = {"Authorization": f"Bearer {instructor_token}"}
    module_id = 999999
    if module_source == "other_course":
        module_id = db_session.scalar(select(Module.id).join(Module.course).where(Course.code == "cs1410"))
        assert module_id is not None
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json={"slug": "invalid-module", "title": "Invalid module", "module_id": module_id},
        headers=headers,
    )
    assert response.status_code == 400
    assert "module" in response.json()["detail"].lower()
    assert db_session.scalar(select(Assignment).where(Assignment.slug == "invalid-module")) is None


@pytest.mark.parametrize("module_source", ["other_course", "missing"])
def test_update_assignment_rejects_invalid_module_before_changing_setup(
    client, instructor_token, db_session, module_source,
):
    headers = {"Authorization": f"Bearer {instructor_token}"}
    url = "/staff/courses/cs1400/assignments/simple-python-functions/setup"
    before = client.get(url, headers=headers).json()
    module_id = 999999
    if module_source == "other_course":
        module_id = db_session.scalar(select(Module.id).join(Module.course).where(Course.code == "cs1410"))
        assert module_id is not None
    response = client.put(
        url,
        json={"title": "Should not save", "config": before["config"], "module_id": module_id},
        headers=headers,
    )
    assert response.status_code == 400
    assert "module" in response.json()["detail"].lower()
    assert client.get(url, headers=headers).json() == before


def test_assignment_accepts_course_owned_module_and_can_clear_it(client, instructor_token, db_session):
    headers = {"Authorization": f"Bearer {instructor_token}"}
    module_id = db_session.scalar(select(Module.id).join(Module.course).where(Course.code == "cs1400"))
    assert module_id is not None
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json={"slug": "owned-module", "title": "Owned module", "module_id": module_id},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["module_id"] == module_id
    response = client.put(
        "/staff/courses/cs1400/assignments/owned-module/setup",
        json={"config": response.json()["config"], "module_id": None},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["module_id"] is None


def test_create_assignment_invalid_slug(client, instructor_token):
    headers = {"Authorization": f"Bearer {instructor_token}"}

    # Slug with spaces/uppercase
    payload = {
        "slug": "Invalid Slug",
        "title": "Invalid assignment",
    }
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 422


def test_create_assignment_invalid_course(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "slug": "valid-slug",
        "title": "Valid title",
    }
    response = client.post(
        "/staff/courses/nonexistent-course/assignments",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 404


def test_delete_assignment_success(client, instructor_token, db_session):
    headers = {"Authorization": f"Bearer {instructor_token}"}

    # Delete existing seeded assignment "simple-python-functions"
    response = client.delete(
        "/staff/courses/cs1400/assignments/simple-python-functions",
        headers=headers,
    )
    assert response.status_code == 204

    # Verify db entry is deactivated
    assignment = db_session.scalar(
        select(Assignment).where(Assignment.slug == "simple-python-functions")
    )
    assert assignment is not None
    assert assignment.is_active is False

    # Verify it is no longer returned in staff setup read
    response_get = client.get(
        "/staff/courses/cs1400/assignments/simple-python-functions/setup",
        headers=headers,
    )
    assert response_get.status_code == 404


def test_delete_assignment_nonexistent(client, instructor_token):
    headers = {"Authorization": f"Bearer {instructor_token}"}

    response = client.delete(
        "/staff/courses/cs1400/assignments/nonexistent-slug",
        headers=headers,
    )
    assert response.status_code == 404


# 3. Reactivation Behavior

def test_reactivate_deleted_assignment(client, instructor_token, db_session):
    headers = {"Authorization": f"Bearer {instructor_token}"}

    # 1. Delete the assignment
    response_delete = client.delete(
        "/staff/courses/cs1400/assignments/simple-python-functions",
        headers=headers,
    )
    assert response_delete.status_code == 204

    # Verify it is inactive
    assignment_deleted = db_session.scalar(
        select(Assignment).where(Assignment.slug == "simple-python-functions")
    )
    assert assignment_deleted.is_active is False
    original_id = assignment_deleted.id

    # 2. Re-create it with new details
    payload = {
        "slug": "simple-python-functions",
        "title": "Reactivated Python Functions",
        "language": "python",
        "canvas_ref": "canvas:reactivated",
        "sandbox_enabled": False,
    }
    response_create = client.post(
        "/staff/courses/cs1400/assignments",
        json=payload,
        headers=headers,
    )
    assert response_create.status_code == 201
    data = response_create.json()
    assert data["title"] == "Reactivated Python Functions"
    assert data["canvas_ref"] == "canvas:reactivated"
    assert data["sandbox_enabled"] is False

    # Verify db entry is reactivated and has the SAME database ID
    db_session.expire_all()
    assignment_reactivated = db_session.scalar(
        select(Assignment).where(Assignment.slug == "simple-python-functions")
    )
    assert assignment_reactivated.is_active is True
    assert assignment_reactivated.id == original_id
    assert assignment_reactivated.title == "Reactivated Python Functions"


def test_create_assignment_seeds_from_db_seeds(client, instructor_token, db_session):
    headers = {"Authorization": f"Bearer {instructor_token}"}
    payload = {
        "slug": "ds1-test-seed",
        "title": "Dessert Shop Test Seed",
        "language": "python",
        "canvas_ref": "canvas:test-ds1",
        "sandbox_enabled": True,
    }
    response = client.post(
        "/staff/courses/cs1400/assignments",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 201

    setup_response = client.get(
        "/staff/courses/cs1400/assignments/ds1-test-seed/setup",
        headers=headers,
    )
    assert setup_response.status_code == 200
    setup = setup_response.json()
    assert setup["entrypoint_path"] == "student_functions.py"
    scoring_item_keys = [item["key"] for item in setup["scoring_items"]]
    assert "add_numbers" in scoring_item_keys
    artifact_keys = [art["artifact_key"] for art in setup["artifacts"]]
    assert "assignment_tests" in artifact_keys

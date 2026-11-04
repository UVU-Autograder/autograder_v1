from fastapi import status
from sqlalchemy.orm import Session

from app.domains.assignments.service import effective_allowed_concepts, get_assignment_for_course
from app.domains.courses.models import Course
from app.integrations.ast_checker.validator import ASTCodeInspector


def test_course_creation_allowed_concepts_optional(client, admin_token, db_session: Session):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. When omitted, use_allowed_concepts defaults to True
    res_default = client.post(
        "/staff/admin/courses",
        json={
            "code": "test101",
            "title": "Default Concepts Course",
            "term": "Fall 2026",
            "default_concepts": ["variables"],
        },
        headers=headers,
    )
    assert res_default.status_code == status.HTTP_201_CREATED
    data_default = res_default.json()
    assert data_default["use_allowed_concepts"] is True

    # 2. When explicitly set to False, use_allowed_concepts is False
    res_false = client.post(
        "/staff/admin/courses",
        json={
            "code": "test102",
            "title": "No Concepts Course",
            "term": "Fall 2026",
            "default_concepts": [],
            "use_allowed_concepts": False,
        },
        headers=headers,
    )
    assert res_false.status_code == status.HTTP_201_CREATED
    data_false = res_false.json()
    assert data_false["use_allowed_concepts"] is False

    # 3. Supports allowed_concepts_enabled alias
    res_alias = client.post(
        "/staff/admin/courses",
        json={
            "code": "test103",
            "title": "Alias Course",
            "term": "Fall 2026",
            "default_concepts": [],
            "allowed_concepts_enabled": False,
        },
        headers=headers,
    )
    assert res_alias.status_code == status.HTTP_201_CREATED
    assert res_alias.json()["use_allowed_concepts"] is False


def test_course_update_allowed_concepts_in_admin(client, admin_token, db_session: Session):
    headers = {"Authorization": f"Bearer {admin_token}"}

    res_create = client.post(
        "/staff/admin/courses",
        json={
            "code": "test201",
            "title": "Admin Update Course",
            "term": "Spring 2027",
            "default_concepts": ["variables"],
            "use_allowed_concepts": True,
        },
        headers=headers,
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    course_id = res_create.json()["id"]

    # Toggle to False
    res_update = client.put(
        f"/staff/admin/courses/{course_id}",
        json={"use_allowed_concepts": False},
        headers=headers,
    )
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["use_allowed_concepts"] is False

    # Check persistence in db
    c = db_session.get(Course, course_id)
    assert c is not None
    assert c.use_allowed_concepts is False
    assert c.allowed_concepts_enabled is False

    # Toggle back to True
    res_update2 = client.put(
        f"/staff/admin/courses/{course_id}",
        json={"use_allowed_concepts": True},
        headers=headers,
    )
    assert res_update2.status_code == status.HTTP_200_OK
    assert res_update2.json()["use_allowed_concepts"] is True


def test_course_settings_concepts_endpoint(client, instructor_token, db_session: Session):
    headers = {"Authorization": f"Bearer {instructor_token}"}

    # 1. GET concepts includes use_allowed_concepts
    res_get = client.get("/staff/courses/cs1400/concepts", headers=headers)
    assert res_get.status_code == status.HTTP_200_OK
    data_get = res_get.json()
    assert "use_allowed_concepts" in data_get
    assert data_get["use_allowed_concepts"] is True

    # 2. PUT concepts can disable allowed concepts
    res_put = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={
            "default_concepts": ["variables"],
            "modules": [],
            "use_allowed_concepts": False,
        },
    )
    assert res_put.status_code == status.HTTP_200_OK
    assert res_put.json()["use_allowed_concepts"] is False

    # 3. Verify in db
    course = db_session.query(Course).filter(Course.code == "cs1400").first()
    assert course is not None
    assert course.use_allowed_concepts is False

    # 4. Optional feature: updating without use_allowed_concepts leaves it intact
    res_put_partial = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={
            "default_concepts": ["variables", "loops"],
            "modules": [],
        },
    )
    assert res_put_partial.status_code == status.HTTP_200_OK
    assert res_put_partial.json()["use_allowed_concepts"] is False

    # 5. Re-enable
    res_reenable = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={
            "default_concepts": ["variables", "conditionals"],
            "modules": [],
            "use_allowed_concepts": True,
        },
    )
    assert res_reenable.status_code == status.HTTP_200_OK
    assert res_reenable.json()["use_allowed_concepts"] is True


def test_effective_allowed_concepts_and_ast_checking_behavior(db_session: Session):
    assignment = get_assignment_for_course(db_session, "cs1400", "simple-python-functions")
    assert assignment is not None

    code = "for i in range(10):\n    x = i * 2\n"

    # When use_allowed_concepts is True
    assignment.course.use_allowed_concepts = True
    db_session.commit()
    concepts = effective_allowed_concepts(assignment)
    assert concepts is not None
    assert isinstance(concepts, list)

    # When use_allowed_concepts is False
    assignment.course.use_allowed_concepts = False
    db_session.commit()
    concepts_disabled = effective_allowed_concepts(assignment)
    assert concepts_disabled is None

    # AST check with concepts_disabled (None) produces no concept warnings
    inspector = ASTCodeInspector(allowed_concepts=concepts_disabled)
    res = inspector.inspect_source(code)
    assert res.warnings == []
    assert not res.is_blocked

    # Security violations are still caught even when allowed concepts is disabled
    res_blocked = inspector.inspect_source("import os\n")
    assert res_blocked.is_blocked
    assert any("os" in b.message for b in res_blocked.blocked)

    # Reset cs1400 back to True for other tests
    assignment.course.use_allowed_concepts = True
    db_session.commit()


def test_sandbox_assignment_detail_when_concepts_disabled(client, db_session: Session):
    assignment = get_assignment_for_course(db_session, "cs1400", "simple-python-functions")
    assignment.course.use_allowed_concepts = False
    db_session.commit()
    try:
        res = client.get("/sandbox/courses/cs1400/assignments/simple-python-functions")
        assert res.status_code == status.HTTP_200_OK
    finally:
        assignment.course.use_allowed_concepts = True
        db_session.commit()

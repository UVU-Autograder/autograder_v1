from fastapi import status
from sqlalchemy.orm import Session

from app.domains.courses.models import Course


def test_course_creation_visibility(client, admin_token, db_session: Session):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Defaults to "everyone"
    res1 = client.post(
        "/staff/admin/courses",
        json={
            "code": "vis_default",
            "title": "Default Visibility Course",
            "term": "Fall 2026",
            "default_concepts": ["variables"],
        },
        headers=headers,
    )
    assert res1.status_code == status.HTTP_201_CREATED
    data1 = res1.json()
    assert data1["visibility"] == "everyone"

    c1 = db_session.get(Course, data1["id"])
    assert c1 is not None
    assert c1.visibility == "everyone"
    assert c1.is_viewable_by_everyone is True

    # 2. Explicit "teachers_admins"
    res2 = client.post(
        "/staff/admin/courses",
        json={
            "code": "vis_staff",
            "title": "Staff Only Course",
            "term": "Fall 2026",
            "visibility": "teachers_admins",
            "default_concepts": [],
        },
        headers=headers,
    )
    assert res2.status_code == status.HTTP_201_CREATED
    data2 = res2.json()
    assert data2["visibility"] == "teachers_admins"

    c2 = db_session.get(Course, data2["id"])
    assert c2 is not None
    assert c2.visibility == "teachers_admins"
    assert c2.is_viewable_by_everyone is False

    # 3. Supports viewable_by alias and normalizes staff_only
    res3 = client.post(
        "/staff/admin/courses",
        json={
            "code": "vis_alias",
            "title": "Alias Course",
            "term": "Fall 2026",
            "viewable_by": "staff_only",
            "default_concepts": [],
        },
        headers=headers,
    )
    assert res3.status_code == status.HTTP_201_CREATED
    assert res3.json()["visibility"] == "teachers_admins"


def test_course_update_visibility_in_admin(client, admin_token, db_session: Session):
    headers = {"Authorization": f"Bearer {admin_token}"}

    res_create = client.post(
        "/staff/admin/courses",
        json={
            "code": "vis_update",
            "title": "Update Visibility Course",
            "term": "Fall 2026",
            "visibility": "everyone",
            "default_concepts": [],
        },
        headers=headers,
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    course_id = res_create.json()["id"]

    # Toggle to teachers_admins
    res_update = client.put(
        f"/staff/admin/courses/{course_id}",
        json={"visibility": "teachers_admins"},
        headers=headers,
    )
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["visibility"] == "teachers_admins"

    course = db_session.get(Course, course_id)
    assert course is not None
    assert course.visibility == "teachers_admins"
    assert course.is_viewable_by_everyone is False

    # Toggle back to everyone
    res_update2 = client.put(
        f"/staff/admin/courses/{course_id}",
        json={"visibility": "everyone"},
        headers=headers,
    )
    assert res_update2.status_code == status.HTTP_200_OK
    assert res_update2.json()["visibility"] == "everyone"

    db_session.refresh(course)
    assert course.visibility == "everyone"
    assert course.is_viewable_by_everyone is True


def test_course_settings_visibility_endpoint(client, instructor_token, db_session: Session):
    headers = {"Authorization": f"Bearer {instructor_token}"}

    # GET concepts returns visibility
    res_get = client.get("/staff/courses/cs1400/concepts", headers=headers)
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["visibility"] == "everyone"

    # PUT concepts updates visibility
    res_put = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={
            "default_concepts": ["variables"],
            "modules": [],
            "visibility": "teachers_admins",
        },
    )
    assert res_put.status_code == status.HTTP_200_OK
    assert res_put.json()["visibility"] == "teachers_admins"

    course = db_session.query(Course).filter(Course.code == "cs1400").first()
    assert course is not None
    assert course.visibility == "teachers_admins"

    # Reset back to everyone so other tests aren't impacted
    res_reset = client.put(
        "/staff/courses/cs1400/concepts",
        headers=headers,
        json={
            "default_concepts": ["variables"],
            "modules": [],
            "visibility": "everyone",
        },
    )
    assert res_reset.status_code == status.HTTP_200_OK
    assert res_reset.json()["visibility"] == "everyone"


def test_sandbox_catalog_visibility_isolation(client, admin_token, db_session: Session):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # cs1400 has assignments with sandbox_enabled=True.
    # When cs1400 is "everyone", public sandbox catalog sees it.
    res_pub = client.get("/sandbox/courses")
    assert res_pub.status_code == status.HTTP_200_OK
    codes = [c["id"] for c in res_pub.json()["courses"]]
    assert "cs1400" in codes

    # Find cs1400 course id
    cs1400 = db_session.query(Course).filter(Course.code == "cs1400").first()
    assert cs1400 is not None
    cs1400_id = cs1400.id

    # Now change cs1400 visibility to "teachers_admins"
    res_put = client.put(
        f"/staff/admin/courses/{cs1400_id}",
        headers=admin_headers,
        json={"visibility": "teachers_admins"},
    )
    assert res_put.status_code == status.HTTP_200_OK

    try:
        # Unauthenticated request: cs1400 should be hidden!
        res_hidden = client.get("/sandbox/courses")
        assert res_hidden.status_code == status.HTTP_200_OK
        hidden_codes = [c["id"] for c in res_hidden.json()["courses"]]
        assert "cs1400" not in hidden_codes

        # Public request for assignments of cs1400: returns 404!
        res_assign = client.get("/sandbox/courses/cs1400/assignments")
        assert res_assign.status_code == status.HTTP_404_NOT_FOUND

        # Public request for specific assignment of cs1400: returns 404!
        res_detail = client.get("/sandbox/courses/cs1400/assignments/simple-python-functions")
        assert res_detail.status_code == status.HTTP_404_NOT_FOUND

        # Public post run for cs1400: returns 404!
        res_run = client.post(
            "/sandbox/courses/cs1400/assignments/simple-python-functions/runs",
            files={
                "bundle": (
                    "student.py.zip",
                    b"print('test')",
                    "application/zip",
                )
            },
        )
        assert res_run.status_code == status.HTTP_404_NOT_FOUND

        # Authenticated Admin request: CAN see cs1400 in sandbox!
        res_admin_courses = client.get("/sandbox/courses", headers=admin_headers)
        assert res_admin_courses.status_code == status.HTTP_200_OK
        admin_codes = [c["id"] for c in res_admin_courses.json()["courses"]]
        assert "cs1400" in admin_codes

        # Admin request for assignments: returns 200!
        res_admin_assign = client.get("/sandbox/courses/cs1400/assignments", headers=admin_headers)
        assert res_admin_assign.status_code == status.HTTP_200_OK
        assert res_admin_assign.json()["course_id"] == "cs1400"

        # Admin request for specific assignment: returns 200!
        res_admin_detail = client.get(
            "/sandbox/courses/cs1400/assignments/simple-python-functions",
            headers=admin_headers,
        )
        assert res_admin_detail.status_code == status.HTTP_200_OK

    finally:
        # Restore cs1400 to "everyone"
        client.put(
            f"/staff/admin/courses/{cs1400_id}",
            headers=admin_headers,
            json={"visibility": "everyone"},
        )

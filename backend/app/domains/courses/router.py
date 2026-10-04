from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import (
    DbSession,
    accessible_course_ids,
    accessible_section_ids_for_course,
    assert_course_access,
    require_staff,
)
from app.domains.auth.models import User
from app.domains.courses.models import Section
from app.domains.courses.schemas import (
    CourseConceptsResponse,
    CourseConceptsUpdate,
    StaffAssignmentListResponse,
    StaffCourseListResponse,
    StaffSectionListResponse,
    StaffSectionSummary,
)
from app.domains.courses.service import (
    get_course_concepts,
    list_staff_assignments,
    list_staff_courses,
    update_course_concepts,
)

router = APIRouter(
    prefix="/staff/courses",
    tags=["staff-courses"],
    dependencies=[Depends(require_staff)],
)


@router.get("", response_model=StaffCourseListResponse)
def get_staff_courses(
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> StaffCourseListResponse:
    allowed_ids = accessible_course_ids(db, current_user)
    return list_staff_courses(db, allowed_ids)


@router.get("/{course_id}/assignments", response_model=StaffAssignmentListResponse)
def get_staff_assignments(
    course_id: str,
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> StaffAssignmentListResponse:
    assert_course_access(db, current_user, course_code=course_id, allow_ia=True, write_access=False)
    assignments = list_staff_assignments(db, course_id)
    if assignments is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return assignments


@router.get("/{course_id}/sections", response_model=StaffSectionListResponse)
def get_staff_sections(
    course_id: str,
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> StaffSectionListResponse:
    course = assert_course_access(db, current_user, course_code=course_id, allow_ia=True, write_access=False)

    sections = list(
        db.scalars(
            select(Section)
            .where(Section.course_id == course.id, Section.is_active.is_(True))
            .order_by(Section.crn)
        ).all()
    )

    allowed = accessible_section_ids_for_course(db, current_user, course_id)
    if allowed is not None:
        allowed_set = set(allowed)
        sections = [s for s in sections if s.id in allowed_set]

    return StaffSectionListResponse(
        course_id=course_id,
        sections=[
            StaffSectionSummary(id=s.id, crn=s.crn, is_active=s.is_active)
            for s in sections
        ],
    )


@router.get("/{course_id}/concepts", response_model=CourseConceptsResponse)
def get_concepts(
    course_id: str,
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> CourseConceptsResponse:
    assert_course_access(db, current_user, course_code=course_id, allow_ia=True, write_access=False)
    concepts = get_course_concepts(db, course_id)
    if concepts is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return concepts


@router.put("/{course_id}/concepts", response_model=CourseConceptsResponse)
def update_concepts(
    course_id: str,
    payload: CourseConceptsUpdate,
    db: DbSession,
    current_user: User = Depends(require_staff),
) -> CourseConceptsResponse:
    assert_course_access(db, current_user, course_code=course_id, allow_ia=False, write_access=True)
    concepts = update_course_concepts(db, course_id, payload.default_concepts, payload.modules)
    if concepts is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return concepts

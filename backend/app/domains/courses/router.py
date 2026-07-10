from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.core.dependencies import (
    DbSession,
    accessible_section_ids_for_course,
    require_staff,
)
from app.domains.auth.models import User
from app.domains.courses.models import Course, Section
from app.domains.courses.schemas import (
    StaffAssignmentListResponse,
    StaffCourseListResponse,
    CourseConceptsResponse,
    CourseConceptsUpdate,
    StaffSectionListResponse,
    StaffSectionSummary,
)
from app.domains.courses.service import (
    list_staff_assignments,
    list_staff_courses,
    get_course_concepts,
    update_course_concepts,
)

router = APIRouter(
    prefix="/staff/courses",
    tags=["staff-courses"],
    dependencies=[Depends(require_staff)],
)


@router.get("", response_model=StaffCourseListResponse)
def get_staff_courses(db: DbSession) -> StaffCourseListResponse:
    return list_staff_courses(db)


@router.get("/{course_id}/assignments", response_model=StaffAssignmentListResponse)
def get_staff_assignments(course_id: str, db: DbSession) -> StaffAssignmentListResponse:
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
    course = db.scalar(
        select(Course).where(Course.code == course_id, Course.is_active.is_(True))
    )
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found.")

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
def get_concepts(course_id: str, db: DbSession) -> CourseConceptsResponse:
    concepts = get_course_concepts(db, course_id)
    if concepts is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return concepts


@router.put("/{course_id}/concepts", response_model=CourseConceptsResponse)
def update_concepts(
    course_id: str,
    payload: CourseConceptsUpdate,
    db: DbSession,
) -> CourseConceptsResponse:
    concepts = update_course_concepts(db, course_id, payload.default_concepts, payload.modules)
    if concepts is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return concepts

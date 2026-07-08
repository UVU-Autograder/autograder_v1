from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DbSession, require_staff
from app.domains.courses.schemas import (
    StaffAssignmentListResponse,
    StaffCourseListResponse,
    CourseConceptsResponse,
    CourseConceptsUpdate,
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


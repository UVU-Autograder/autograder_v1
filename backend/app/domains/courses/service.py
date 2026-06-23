from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domains.assignments.models import Assignment
from app.domains.assignments.service import validate_config_json
from app.domains.courses.models import Course
from app.domains.courses.schemas import (
    StaffAssignmentListResponse,
    StaffAssignmentSummary,
    StaffCourseListResponse,
    StaffCourseSummary,
    CourseConceptsResponse,
)



def list_staff_courses(db: Session) -> StaffCourseListResponse:
    rows = db.execute(
        select(Course, func.count(Assignment.id))
        .outerjoin(Course.assignments)
        .where(Course.is_active.is_(True))
        .group_by(Course.id)
        .order_by(Course.code)
    ).all()
    return StaffCourseListResponse(
        courses=[
            StaffCourseSummary(
                id=course.code,
                title=course.title,
                term=course.term,
                assignment_count=count,
            )
            for course, count in rows
        ]
    )


def list_staff_assignments(db: Session, course_code: str) -> StaffAssignmentListResponse | None:
    course = db.scalar(
        select(Course)
        .where(Course.code == course_code, Course.is_active.is_(True))
        .options(selectinload(Course.assignments).selectinload(Assignment.config))
    )
    if course is None:
        return None

    assignments = []
    for assignment in sorted(course.assignments, key=lambda item: item.slug):
        if not assignment.is_active or assignment.config is None:
            continue
        config = validate_config_json(assignment.config.config_json)
        assignments.append(
            StaffAssignmentSummary(
                id=assignment.slug,
                course_id=course.code,
                title=assignment.title,
                language=assignment.language,
                sandbox_enabled=assignment.sandbox_enabled,
                base_points=config.base_points,
                extra_credit_points=config.extra_credit_points,
            )
        )

    return StaffAssignmentListResponse(course_id=course.code, assignments=assignments)


def get_course_concepts(db: Session, course_code: str) -> CourseConceptsResponse | None:
    course = db.scalar(
        select(Course)
        .where(Course.code == course_code, Course.is_active.is_(True))
    )
    if course is None:
        return None
    return CourseConceptsResponse(course_id=course.code, default_concepts=course.default_concepts or [])


def update_course_concepts(db: Session, course_code: str, default_concepts: list[str]) -> CourseConceptsResponse | None:
    course = db.scalar(
        select(Course)
        .where(Course.code == course_code, Course.is_active.is_(True))
    )
    if course is None:
        return None
    course.default_concepts = default_concepts
    db.commit()
    db.refresh(course)
    return CourseConceptsResponse(course_id=course.code, default_concepts=course.default_concepts or [])


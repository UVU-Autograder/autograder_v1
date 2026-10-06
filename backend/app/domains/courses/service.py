from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domains.assignments.models import Assignment
from app.domains.assignments.service import validate_config
from app.domains.courses.models import Course, Module
from app.domains.courses.schemas import (
    CourseConceptsResponse,
    ModuleConfig,
    StaffAssignmentListResponse,
    StaffAssignmentSummary,
    StaffCourseListResponse,
    StaffCourseSummary,
)


def list_staff_courses(db: Session, allowed_course_ids: list[int] | None = None) -> StaffCourseListResponse:
    query = (
        select(Course, func.count(Assignment.id))
        .outerjoin(Course.assignments)
        .where(Course.is_active.is_(True))
    )
    if allowed_course_ids is not None:
        query = query.where(Course.id.in_(allowed_course_ids))
    rows = db.execute(
        query.group_by(Course.id).order_by(Course.code)
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
        .options(
            selectinload(Course.assignments).selectinload(Assignment.config),
            selectinload(Course.assignments).selectinload(Assignment.module),
        )
    )
    if course is None:
        return None

    assignments = []
    for assignment in sorted(course.assignments, key=lambda item: item.slug):
        if not assignment.is_active or assignment.config is None:
            continue
        config = validate_config(assignment.config.config)
        assignments.append(
            StaffAssignmentSummary(
                id=assignment.slug,
                course_id=course.code,
                title=assignment.title,
                language=assignment.language,
                sandbox_enabled=assignment.sandbox_enabled,
                base_points=config.base_points,
                extra_credit_points=config.extra_credit_points,
                module_name=assignment.module.name if assignment.module else None,
            )
        )

    return StaffAssignmentListResponse(course_id=course.code, assignments=assignments)


def _build_cumulative_module_configs(default_concepts: list[str], modules: list[Module]) -> list[ModuleConfig]:
    ordered_modules = sorted(modules, key=lambda m: m.id if m.id is not None else 0)
    seen: set[str] = set()
    for c in default_concepts or []:
        if c not in seen:
            seen.add(c)

    out: list[ModuleConfig] = []
    for m in ordered_modules:
        for c in (m.concepts or []):
            if c not in seen:
                seen.add(c)
        out.append(ModuleConfig(id=m.id, name=m.name, concepts=list(seen)))
    return out


def get_course_concepts(db: Session, course_code: str) -> CourseConceptsResponse | None:
    course = db.scalar(
        select(Course)
        .where(Course.code == course_code, Course.is_active.is_(True))
        .options(selectinload(Course.modules))
    )
    if course is None:
        return None
    return CourseConceptsResponse(
        course_id=course.code,
        default_concepts=course.default_concepts or [],
        modules=_build_cumulative_module_configs(course.default_concepts or [], course.modules),
    )


def update_course_concepts(
    db: Session,
    course_code: str,
    default_concepts: list[str],
    modules_payload: list[ModuleConfig],
) -> CourseConceptsResponse | None:
    course = db.scalar(
        select(Course)
        .where(Course.code == course_code, Course.is_active.is_(True))
        .options(selectinload(Course.modules))
    )
    if course is None:
        return None

    course.default_concepts = default_concepts

    # Sync modules
    existing_modules = {m.id: m for m in course.modules}
    updated_modules = []

    for mod_data in modules_payload:
        if mod_data.id is not None and mod_data.id in existing_modules:
            m = existing_modules[mod_data.id]
            m.name = mod_data.name
            m.concepts = mod_data.concepts
            updated_modules.append(m)
        else:
            m = Module(
                course_id=course.id,
                name=mod_data.name,
                concepts=mod_data.concepts
            )
            db.add(m)
            updated_modules.append(m)

    payload_ids = {mod_data.id for mod_data in modules_payload if mod_data.id is not None}
    for m in course.modules:
        if m.id not in payload_ids:
            db.delete(m)

    course.modules = updated_modules
    db.commit()
    db.refresh(course)

    return CourseConceptsResponse(
        course_id=course.code,
        default_concepts=course.default_concepts or [],
        modules=_build_cumulative_module_configs(course.default_concepts or [], course.modules),
    )


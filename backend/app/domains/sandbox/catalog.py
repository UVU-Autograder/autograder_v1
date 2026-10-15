from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.settings import get_settings
from app.domains.assignments.models import Assignment
from app.domains.assignments.schemas import pytest_marker_for_key
from app.domains.assignments.service import (
    _coerce_scoring_item_type,
    effective_allowed_concepts,
    validate_config,
)
from app.domains.courses.models import Course
from app.domains.sandbox.schemas import (
    SandboxAssignmentDetail,
    SandboxAssignmentListResponse,
    SandboxAssignmentSummary,
    SandboxConstraint,
    SandboxCourse,
    SandboxCourseListResponse,
    SandboxRubricGroup,
    SandboxRubricItem,
    UploadQuota,
)


def list_sandbox_courses(db: Session) -> SandboxCourseListResponse:
    rows = db.execute(
        select(Course, func.count(Assignment.id))
        .join(Course.assignments)
        .where(
            Course.is_active.is_(True),
            Assignment.is_active.is_(True),
            Assignment.sandbox_enabled.is_(True),
        )
        .group_by(Course.id)
        .order_by(Course.code)
    ).all()
    return SandboxCourseListResponse(
        courses=[
            SandboxCourse(
                id=course.code,
                title=course.title,
                term=course.term,
                sandbox_enabled_assignments=count,
            )
            for course, count in rows
        ]
    )


def list_sandbox_assignments(
    db: Session,
    course_code: str,
    quota: UploadQuota,
) -> SandboxAssignmentListResponse | None:
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

    assignments = [
        _summary_for(assignment, quota)
        for assignment in sorted(course.assignments, key=lambda item: item.slug)
        if assignment.is_active and assignment.sandbox_enabled
    ]
    return SandboxAssignmentListResponse(course_id=course.code, assignments=assignments)


def get_sandbox_assignment(
    db: Session,
    course_code: str,
    assignment_slug: str,
    quota: UploadQuota,
) -> SandboxAssignmentDetail | None:
    assignment = db.scalar(
        select(Assignment)
        .join(Assignment.course)
        .where(
            Course.code == course_code,
            Course.is_active.is_(True),
            Assignment.slug == assignment_slug,
            Assignment.is_active.is_(True),
            Assignment.sandbox_enabled.is_(True),
        )
        .options(
            selectinload(Assignment.course).selectinload(Course.modules),
            selectinload(Assignment.config),
            selectinload(Assignment.module),
        )
    )
    if assignment is None:
        return None

    settings = get_settings()
    allowed_concepts = effective_allowed_concepts(assignment)
    if assignment.config is not None:
        config = validate_config(assignment.config.config)
        req_files = config.bundle.derived_required_files()
        rubric = [
            SandboxRubricItem(
                key=item.key,
                label=item.label,
                points=item.points,
                extra_credit=item.extra_credit,
                item_type=_coerce_scoring_item_type(item.item_type, item.label),
                pytest_marker=pytest_marker_for_key(item.key) if item.item_type == "pytest" else None,
                rubric_group_key=item.rubric_group_key,
                inputs=item.inputs,
                outputs=item.outputs,
            )
            for item in config.scoring_items
        ]
        rubric_groups = [
            SandboxRubricGroup(
                key=group.key,
                label=group.label,
                item_keys=[item.key for item in config.scoring_items if item.rubric_group_key == group.key],
            )
            for group in config.rubric_groups
        ]
        completion_requirements = [item.model_dump() for item in config.completion_requirements]
        constraints = [
            SandboxConstraint(label="Entrypoint", value=config.bundle.entrypoint),
            SandboxConstraint(label="Required files", value=", ".join(req_files)),
        ]
        description = assignment.description or config.description or assignment.title
        max_score = config.base_points
    else:
        rubric = []
        rubric_groups = []
        completion_requirements = []
        constraints = [
            SandboxConstraint(label="Entrypoint", value="main.py"),
            SandboxConstraint(label="Required files", value="main.py"),
        ]
        description = assignment.description or assignment.title
        max_score = 0

    return SandboxAssignmentDetail(
        id=assignment.slug,
        course_id=assignment.course.code,
        title=assignment.title,
        sandbox_enabled=assignment.sandbox_enabled,
        language=assignment.language,
        max_score=max_score,
        upload_quota=quota,
        module_name=assignment.module.name if assignment.module else None,
        description=description,
        accepted_bundle_types=["application/zip", ".zip"],
        max_upload_bytes=settings.max_upload_bytes,
        constraints=constraints,
        allowed_concepts=allowed_concepts,
        rubric=rubric,
        rubric_groups=rubric_groups,
        completion_requirements=completion_requirements,
    )


def _summary_for(assignment: Assignment, quota: UploadQuota) -> SandboxAssignmentSummary:
    max_score = 0
    if assignment.config is not None:
        config = validate_config(assignment.config.config)
        max_score = config.base_points
    return SandboxAssignmentSummary(
        id=assignment.slug,
        course_id=assignment.course.code,
        title=assignment.title,
        sandbox_enabled=assignment.sandbox_enabled,
        language=assignment.language,
        max_score=max_score,
        upload_quota=quota,
        module_name=assignment.module.name if assignment.module else None,
    )

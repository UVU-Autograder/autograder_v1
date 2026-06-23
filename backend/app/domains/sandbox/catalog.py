from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.settings import get_settings
from app.domains.assignments.models import Assignment
from app.domains.assignments.service import validate_config_json
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
        .options(selectinload(Course.assignments).selectinload(Assignment.config))
    )
    if course is None:
        return None

    assignments = [
        _summary_for(assignment, quota)
        for assignment in sorted(course.assignments, key=lambda item: item.slug)
        if assignment.is_active and assignment.sandbox_enabled and assignment.config is not None
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
            selectinload(Assignment.course),
            selectinload(Assignment.config),
            selectinload(Assignment.scoring_items),
        )
    )
    if assignment is None or assignment.config is None:
        return None

    config = validate_config_json(assignment.config.config_json)
    settings = get_settings()
    allowed_concepts = config.concepts.additions if config.concepts else []
    return SandboxAssignmentDetail(
        **_summary_for(assignment, quota).model_dump(),
        description=assignment.title,
        accepted_bundle_types=["application/zip", ".zip"],
        max_upload_bytes=settings.max_upload_bytes,
        constraints=[
            SandboxConstraint(label="Entrypoint", value=config.bundle.entrypoint),
            SandboxConstraint(label="Required files", value=", ".join(config.bundle.required_files)),
        ],
        allowed_concepts=allowed_concepts,
        rubric=[
            SandboxRubricItem(
                key=item.config_item_key,
                label=item.label,
                points=item.points,
                extra_credit=item.extra_credit,
                item_type=item.item_type,
                pytest_marker=item.pytest_marker,
                rubric_group_key=item.rubric_group_key,
            )
            for item in sorted(assignment.scoring_items, key=lambda row: row.display_order)
        ],
        rubric_groups=[
            SandboxRubricGroup(
                key=item.key,
                label=item.label,
                item_keys=item.item_keys,
            )
            for item in config.rubric_groups
        ],
        completion_requirements=[item.model_dump() for item in config.completion_requirements],
    )


def _summary_for(assignment: Assignment, quota: UploadQuota) -> SandboxAssignmentSummary:
    config = validate_config_json(assignment.config.config_json)
    return SandboxAssignmentSummary(
        id=assignment.slug,
        course_id=assignment.course.code,
        title=assignment.title,
        sandbox_enabled=assignment.sandbox_enabled,
        language=assignment.language,
        max_score=config.base_points,
        upload_quota=quota,
    )

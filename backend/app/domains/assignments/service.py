from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.domains.artifacts.models import AssignmentArtifact
from app.domains.assignments.models import (
    Assignment,
    AssignmentConcept,
    AssignmentConfig,
    ScoringItem as ScoringItemProjection,
    TestCase,
)
from app.domains.assignments.schemas import (
    ArtifactMetadata,
    AssignmentConfigV1,
    CompletionRequirement,
    RubricGroup,
    ScoringItem,
    StaffAssignmentSetup,
    StaffAssignmentSetupUpdate,
    pytest_marker_for_key,
)
from app.domains.courses.models import Course


def validate_config_json(config_json: dict) -> AssignmentConfigV1:
    return AssignmentConfigV1.model_validate(config_json)


def regenerate_test_cases(db: Session, assignment: Assignment, config: AssignmentConfigV1) -> None:
    db.execute(delete(TestCase).where(TestCase.assignment_id == assignment.id))
    db.add_all(
        TestCase(
            assignment_id=assignment.id,
            config_test_key=item.key,
            label=item.label,
            points=item.points,
            extra_credit=item.extra_credit,
            pytest_marker=pytest_marker_for_key(item.key),
            display_order=index,
        )
        for index, item in enumerate(config.tests)
    )


def regenerate_scoring_items(db: Session, assignment: Assignment, config: AssignmentConfigV1) -> None:
    db.execute(delete(ScoringItemProjection).where(ScoringItemProjection.assignment_id == assignment.id))
    projections: list[ScoringItemProjection] = []
    for index, item in enumerate(config.tests):
        projections.append(
            ScoringItemProjection(
                assignment_id=assignment.id,
                config_item_key=item.key,
                label=item.label,
                points=item.points,
                extra_credit=item.extra_credit,
                item_type="pytest",
                pytest_marker=pytest_marker_for_key(item.key),
                rubric_group_key=item.rubric_group_key,
                display_order=index,
            )
        )
    manual_offset = len(projections)
    for index, item in enumerate(config.manual_rubric_items):
        projections.append(
            ScoringItemProjection(
                assignment_id=assignment.id,
                config_item_key=item.key,
                label=item.label,
                points=item.points,
                extra_credit=item.extra_credit,
                item_type="manual",
                pytest_marker=None,
                rubric_group_key=item.rubric_group_key,
                display_order=manual_offset + index,
            )
        )
    db.add_all(projections)


def upsert_assignment_config(
    db: Session,
    assignment: Assignment,
    config_json: dict,
) -> AssignmentConfigV1:
    config = validate_config_json(config_json)
    if assignment.config is None:
        assignment.config = AssignmentConfig(config_json=config.model_dump(mode="json"))
    else:
        assignment.config.config_json = config.model_dump(mode="json")

    if assignment.concept_additions is None:
        assignment.concept_additions = AssignmentConcept(
            added_concepts=config.concepts.additions,
        )
    else:
        assignment.concept_additions.added_concepts = config.concepts.additions

    regenerate_test_cases(db, assignment, config)
    regenerate_scoring_items(db, assignment, config)
    return config


def get_assignment_for_course(
    db: Session,
    course_code: str,
    assignment_slug: str,
) -> Assignment | None:
    return db.scalar(
        select(Assignment)
        .join(Assignment.course)
        .where(
            Course.code == course_code,
            Assignment.slug == assignment_slug,
            Assignment.is_active.is_(True),
        )
        .options(
            selectinload(Assignment.course),
            selectinload(Assignment.config),
            selectinload(Assignment.concept_additions),
            selectinload(Assignment.artifacts),
            selectinload(Assignment.test_cases),
            selectinload(Assignment.scoring_items),
        )
    )


def get_staff_setup(
    db: Session,
    course_code: str,
    assignment_slug: str,
) -> StaffAssignmentSetup | None:
    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None or assignment.config is None:
        return None
    return build_staff_setup(assignment)


def update_staff_setup(
    db: Session,
    course_code: str,
    assignment_slug: str,
    payload: StaffAssignmentSetupUpdate,
) -> StaffAssignmentSetup | None:
    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return None

    if payload.title is not None:
        assignment.title = payload.title
    if payload.due_label is not None:
        assignment.due_label = payload.due_label
    if payload.sandbox_enabled is not None:
        assignment.sandbox_enabled = payload.sandbox_enabled

    upsert_assignment_config(db, assignment, payload.config_json.model_dump(mode="json"))
    db.commit()
    db.refresh(assignment)
    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return None
    return build_staff_setup(assignment)


def build_scoring_items(scoring_items: list[ScoringItemProjection]) -> list[ScoringItem]:
    return [
        ScoringItem(
            key=item.config_item_key,
            label=item.label,
            points=item.points,
            extra_credit=item.extra_credit,
            item_type=item.item_type,
            pytest_marker=item.pytest_marker,
            rubric_group_key=item.rubric_group_key,
        )
        for item in sorted(scoring_items, key=lambda item: item.display_order)
    ]


def build_staff_setup(assignment: Assignment) -> StaffAssignmentSetup:
    config = validate_config_json(assignment.config.config_json)
    return StaffAssignmentSetup(
        course_id=assignment.course.code,
        assignment_id=assignment.slug,
        title=assignment.title,
        language=assignment.language,
        due_label=assignment.due_label,
        sandbox_enabled=assignment.sandbox_enabled,
        base_points=config.base_points,
        extra_credit_points=config.extra_credit_points,
        required_files=config.bundle.required_files,
        entrypoint_path=config.bundle.entrypoint.path,
        concept_additions=config.concepts.additions,
        scoring_items=build_scoring_items(assignment.scoring_items),
        rubric_groups=[
            RubricGroup(
                key=item.key,
                label=item.label,
                item_keys=item.item_keys,
            )
            for item in config.rubric_groups
        ],
        completion_requirements=[
            CompletionRequirement(
                key=item.key,
                label=item.label,
                test_keys=item.test_keys,
                minimum_passed=item.minimum_passed,
            )
            for item in config.completion_requirements
        ],
        artifacts=[
            ArtifactMetadata(
                artifact_key=artifact.artifact_key,
                artifact_type=artifact.artifact_type,
                display_filename=artifact.display_filename,
                size_bytes=artifact.size_bytes,
                sha256=artifact.sha256,
            )
            for artifact in sorted(assignment.artifacts, key=lambda item: item.artifact_key)
        ],
    )


def list_artifacts(
    db: Session,
    course_code: str,
    assignment_slug: str,
) -> list[ArtifactMetadata] | None:
    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return None
    return [
        ArtifactMetadata(
            artifact_key=artifact.artifact_key,
            artifact_type=artifact.artifact_type,
            display_filename=artifact.display_filename,
            size_bytes=artifact.size_bytes,
            sha256=artifact.sha256,
        )
        for artifact in sorted(assignment.artifacts, key=lambda item: item.artifact_key)
    ]

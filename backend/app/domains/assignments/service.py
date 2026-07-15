from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.domains.artifacts.models import AssignmentArtifact
from app.domains.assignments.models import (
    Assignment,
    AssignmentConfig,
    AssignmentConfigHistory,
    ScoringItem as ScoringItemProjection,
)
from app.domains.assignments.schemas import (
    ArtifactMetadata,
    AssignmentConfigV1,
    AssignmentCreate,
    CompletionRequirement,
    RubricGroup,
    ScoringItem,
    StaffAssignmentSetup,
    StaffAssignmentSetupUpdate,
    pytest_marker_for_key,
)
from app.domains.courses.models import Course
from app.domains.artifacts.models import file_storage_ref_to_path


def validate_config_json(config_json: dict) -> AssignmentConfigV1:
    return AssignmentConfigV1.model_validate(config_json)




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
        assignment.config = AssignmentConfig(
            config_json=config.model_dump(mode="json"),
            version=1,
        )
    else:
        history_entry = AssignmentConfigHistory(
            assignment_id=assignment.id,
            config_json=assignment.config.config_json,
            version=assignment.config.version,
        )
        db.add(history_entry)
        assignment.config.config_json = config.model_dump(mode="json")
        assignment.config.version += 1



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
            selectinload(Assignment.artifacts),
            selectinload(Assignment.scoring_items),
            selectinload(Assignment.module),
        )
    )


def effective_allowed_concepts(assignment: Assignment) -> list[str]:
    """Course defaults ∪ module concepts, de-duped, stable order.

    Per-assignment concept additions are ignored (unused).
    """
    seen: set[str] = set()
    out: list[str] = []
    for concept in assignment.course.default_concepts or []:
        if concept not in seen:
            seen.add(concept)
            out.append(concept)
    if assignment.module and assignment.module.concepts:
        for concept in assignment.module.concepts:
            if concept not in seen:
                seen.add(concept)
                out.append(concept)
    return out



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
    if payload.sandbox_enabled is not None:
        assignment.sandbox_enabled = payload.sandbox_enabled
    if payload.canvas_ref is not None:
        assignment.canvas_ref = payload.canvas_ref
    if payload.language is not None:
        assignment.language = payload.language
    if "module_id" in payload.model_fields_set:
        assignment.module_id = payload.module_id

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
        sandbox_enabled=assignment.sandbox_enabled,
        canvas_ref=assignment.canvas_ref,
        module_id=assignment.module_id,
        base_points=config.base_points,
        extra_credit_points=config.extra_credit_points,
        required_files=config.bundle.required_files,
        entrypoint_path=config.bundle.entrypoint,
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
        config_json=config,
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


def save_artifact(
    db: Session,
    course_code: str,
    assignment_slug: str,
    artifact_key: str,
    artifact_type: str,
    display_filename: str,
    file_content: bytes,
) -> ArtifactMetadata | None:
    import hashlib
    import uuid
    from app.core.settings import get_settings

    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return None

    settings = get_settings()
    storage_dir = settings.artifact_storage_path
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Generate opaque unique filename
    unique_filename = f"{uuid.uuid4().hex}"
    file_path = storage_dir / unique_filename

    # Calculate SHA256 and size
    sha256 = hashlib.sha256(file_content).hexdigest()
    size_bytes = len(file_content)

    # Write file content
    file_path.write_bytes(file_content)

    # Find existing or create new artifact metadata
    artifact = db.scalar(
        select(AssignmentArtifact).where(
            AssignmentArtifact.assignment_id == assignment.id,
            AssignmentArtifact.artifact_key == artifact_key,
        )
    )

    old_ref = None
    if artifact is None:
        artifact = AssignmentArtifact(
            assignment_id=assignment.id,
            artifact_key=artifact_key,
            artifact_type=artifact_type,
            storage_ref=f"file://{file_path.as_posix()}",
            display_filename=display_filename,
            content_type="text/plain",
            size_bytes=size_bytes,
            sha256=sha256,
        )
        db.add(artifact)
    else:
        # Keep old storage_ref to delete afterwards
        old_ref = artifact.storage_ref
        artifact.artifact_type = artifact_type
        artifact.storage_ref = f"file://{file_path.as_posix()}"
        artifact.display_filename = display_filename
        artifact.size_bytes = size_bytes
        artifact.sha256 = sha256

    db.commit()
    db.refresh(artifact)

    # Clean up the old physical file if it was overwritten
    if old_ref and old_ref.startswith("file://"):
        try:
            old_path = file_storage_ref_to_path(old_ref)
            if old_path is not None:
                old_path.unlink(missing_ok=True)
        except Exception:
            pass

    return ArtifactMetadata(
        artifact_key=artifact.artifact_key,
        artifact_type=artifact.artifact_type,
        display_filename=artifact.display_filename,
        size_bytes=artifact.size_bytes,
        sha256=artifact.sha256,
    )


def delete_artifact(
    db: Session,
    course_code: str,
    assignment_slug: str,
    artifact_key: str,
) -> bool:
    import logging
    logger = logging.getLogger(__name__)
    from app.integrations.artifacts.resolver import resolve_storage_ref

    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return False

    artifact = db.scalar(
        select(AssignmentArtifact).where(
            AssignmentArtifact.assignment_id == assignment.id,
            AssignmentArtifact.artifact_key == artifact_key,
        )
    )
    if artifact is None:
        return False

    if artifact.storage_ref and artifact.storage_ref.startswith("file://"):
        try:
            path = resolve_storage_ref(artifact.storage_ref)
            if path.exists():
                path.unlink()
        except Exception as exc:
            logger.warning(
                "Failed to delete physical file for artifact %s: %s",
                artifact_key,
                exc,
            )

    db.delete(artifact)
    db.commit()
    return True



def get_artifact_content(
    db: Session,
    course_code: str,
    assignment_slug: str,
    artifact_key: str,
) -> tuple[bytes, str] | None:
    from app.integrations.artifacts.resolver import resolve_storage_ref

    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return None

    artifact = db.scalar(
        select(AssignmentArtifact).where(
            AssignmentArtifact.assignment_id == assignment.id,
            AssignmentArtifact.artifact_key == artifact_key,
        )
    )
    if artifact is None or not artifact.storage_ref:
        return None

    try:
        path = resolve_storage_ref(artifact.storage_ref)
        return path.read_bytes(), artifact.display_filename or artifact_key
    except Exception:
        return None


def get_default_config_json() -> dict:
    return {
        "schema_version": 1,
        "bundle": {
            "required_files": ["main.py"],
            "entrypoint": "main.py",
            "file_requirements": [],
        },
        "concepts": {
            "additions": [],
        },
        "artifacts": {
            "tests": {
                "type": "pytest_file",
                "display_filename": "test_main.py",
            },
        },
        "tests": [
            {
                "key": "t1",
                "label": "Test 1",
                "points": 10,
                "extra_credit": False,
            },
        ],
        "completion_requirements": [],
        "execution": {
            "dependencies": [],
        },
        "rubric_groups": [],
        "manual_rubric_items": [],
        "stdin_scenarios": [],
    }


def create_assignment(
    db: Session,
    course_code: str,
    payload: AssignmentCreate,
) -> Assignment:
    course = db.scalar(
        select(Course)
        .where(Course.code == course_code, Course.is_active.is_(True))
    )
    if course is None:
        raise ValueError("Course not found.")

    # Check for existing assignment (either active or inactive)
    existing = db.scalar(
        select(Assignment)
        .where(
            Assignment.course_id == course.id,
            Assignment.slug == payload.slug,
        )
    )

    if existing is not None:
        # Reactivate and update metadata
        existing.title = payload.title
        existing.language = payload.language
        existing.canvas_ref = payload.canvas_ref
        existing.sandbox_enabled = payload.sandbox_enabled
        existing.module_id = payload.module_id
        existing.is_active = True
        if existing.config is None:
            default_config_json = get_default_config_json()
            upsert_assignment_config(db, existing, default_config_json)
        db.commit()
        db.refresh(existing)
        return existing

    # Create new assignment
    assignment = Assignment(
        course_id=course.id,
        slug=payload.slug,
        title=payload.title,
        language=payload.language,
        canvas_ref=payload.canvas_ref,
        sandbox_enabled=payload.sandbox_enabled,
        module_id=payload.module_id,
        is_active=True,
    )
    db.add(assignment)
    db.flush()

    default_config_json = get_default_config_json()
    upsert_assignment_config(db, assignment, default_config_json)

    db.commit()
    db.refresh(assignment)
    return assignment


def deactivate_assignment(
    db: Session,
    course_code: str,
    assignment_slug: str,
) -> bool:
    assignment = get_assignment_for_course(db, course_code, assignment_slug)
    if assignment is None:
        return False
    assignment.is_active = False
    db.commit()
    return True


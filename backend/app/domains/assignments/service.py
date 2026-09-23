import json
import logging
import mimetypes
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.domains.assignments.models import (
    Assignment,
    AssignmentArtifact,
    AssignmentConfig,
    AssignmentConfigHistory,
    file_storage_ref_to_path,
)
from app.domains.assignments.models import (
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


def validate_config_json(config_json: dict) -> AssignmentConfigV1:
    return AssignmentConfigV1.model_validate(config_json)




def regenerate_scoring_items(db: Session, assignment: Assignment, config: AssignmentConfigV1) -> None:
    db.execute(delete(ScoringItemProjection).where(ScoringItemProjection.assignment_id == assignment.id))
    projections: list[ScoringItemProjection] = []
    for index, item in enumerate(config.scoring_items):
        is_pytest = (item.item_type == "pytest")
        projections.append(
            ScoringItemProjection(
                assignment_id=assignment.id,
                config_item_key=item.key,
                label=item.label,
                points=item.points,
                extra_credit=item.extra_credit,
                item_type=item.item_type,
                pytest_marker=pytest_marker_for_key(item.key) if is_pytest else None,
                rubric_group_key=item.rubric_group_key,
                display_order=index,
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
    """Course defaults ∪ cumulative module concepts up to assignment.module in sequence order, de-duped."""
    seen: set[str] = set()
    out: list[str] = []
    for concept in assignment.course.default_concepts or []:
        if concept not in seen:
            seen.add(concept)
            out.append(concept)
    if assignment.module and assignment.course.modules:
        course_modules = sorted(assignment.course.modules, key=lambda m: m.id)
        for m in course_modules:
            for concept in m.concepts or []:
                if concept not in seen:
                    seen.add(concept)
                    out.append(concept)
            if m.id == assignment.module_id:
                break
    if assignment.config and assignment.config.config_json and isinstance(assignment.config.config_json, dict):
        concepts_cfg = assignment.config.config_json.get("concepts") or {}
        denylist = set(concepts_cfg.get("denylist") or concepts_cfg.get("blacklist") or [])
        if denylist:
            out = [c for c in out if c not in denylist]


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


def _coerce_scoring_item_type(item_type: str, label: str) -> Literal["manual", "pytest"]:
    if item_type not in ("manual", "pytest"):
        raise ValueError(f"Unknown item_type '{item_type}' for scoring item '{label}'")
    return "manual" if item_type == "manual" else "pytest"


def build_scoring_items(scoring_items: list[ScoringItemProjection]) -> list[ScoringItem]:
    return [
        ScoringItem(
            key=item.config_item_key,
            label=item.label,
            points=item.points,
            extra_credit=item.extra_credit,
            item_type=_coerce_scoring_item_type(item.item_type, item.label),
            pytest_marker=item.pytest_marker,
            rubric_group_key=item.rubric_group_key,
        )
        for item in sorted(scoring_items, key=lambda item: item.display_order)
    ]


def build_staff_setup(assignment: Assignment) -> StaffAssignmentSetup:
    if assignment.config is None:
        raise ValueError(f"Assignment {assignment.slug} is missing configuration")
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
        entrypoint_path=config.bundle.entrypoint,
        scoring_items=build_scoring_items(assignment.scoring_items),
        rubric_groups=[
            RubricGroup(
                key=group.key,
                label=group.label,
                item_keys=[item.config_item_key for item in assignment.scoring_items if item.rubric_group_key == group.key],
            )
            for group in config.rubric_groups
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
        effective_allowed_concepts=effective_allowed_concepts(assignment),
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
        except Exception as exc:
            logger.warning("Failed to unlink overwritten artifact file %s: %s", old_ref, exc)

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


SEEDS_DIR = Path(__file__).resolve().parents[2] / "db" / "seeds"


def resolve_seed_folder(slug: str | None = None) -> Path:
    if slug:
        for folder_name in (slug.replace("-", "_"), slug):
            candidate = SEEDS_DIR / folder_name
            if candidate.exists() and (candidate / "config_json.example.json").exists():
                return candidate
    fallback = SEEDS_DIR / "simple_python_functions"
    if fallback.exists() and (fallback / "config_json.example.json").exists():
        return fallback
    return SEEDS_DIR


def get_default_config_json(slug: str | None = None) -> dict:
    seed_folder = resolve_seed_folder(slug)
    config_path = seed_folder / "config_json.example.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))

    return {
        "bundle": {
            "entrypoint": "main.py",
            "file_requirements": [
                {
                    "label": "Main Entrypoint Script",
                    "paths": ["main.py"],
                }
            ],
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
        "scoring_items": [
            {
                "key": "t1",
                "label": "Test 1",
                "points": 10,
                "extra_credit": False,
                "item_type": "pytest",
            },
        ],
        "completion_requirements": [],
        "dependencies": [],
        "rubric_groups": [],
    }


def resolve_seed_artifact_path(
    seed_dir: Path,
    display_filename: str,
    *,
    artifact_type: str | None = None,
) -> Path | None:
    local = seed_dir / display_filename
    if local.exists():
        return local
    if artifact_type == "model_solution":
        fallback = seed_dir / "model_solution.py"
        if fallback.exists():
            return fallback
    shared = SEEDS_DIR / "shared" / display_filename
    if shared.exists():
        return shared
    return None


def seed_assignment_artifacts(
    db: Session,
    assignment: Assignment,
    slug: str,
) -> None:
    seed_dir = resolve_seed_folder(slug)
    config_path = seed_dir / "config_json.example.json"
    if not config_path.exists():
        return

    config_json = json.loads(config_path.read_text(encoding="utf-8"))
    upsert_assignment_config(db, assignment, config_json)

    db.execute(delete(AssignmentArtifact).where(AssignmentArtifact.assignment_id == assignment.id))

    for artifact_key, artifact in (config_json.get("artifacts") or {}).items():
        display_filename = artifact.get("display_filename")
        if not display_filename:
            continue

        resolved = resolve_seed_artifact_path(
            seed_dir,
            display_filename,
            artifact_type=artifact.get("type"),
        )
        if resolved is None:
            continue
        artifact_folder = "shared" if resolved.parent.name == "shared" else seed_dir.name

        db.add(
            AssignmentArtifact(
                assignment=assignment,
                artifact_key=artifact_key,
                artifact_type=artifact["type"],
                storage_ref=f"seed://{artifact_folder}/{resolved.name}",
                display_filename=display_filename,
                content_type=mimetypes.guess_type(display_filename)[0]
                or "application/octet-stream",
            )
        )


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
            seed_assignment_artifacts(db, existing, payload.slug)
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

    seed_assignment_artifacts(db, assignment, payload.slug)

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


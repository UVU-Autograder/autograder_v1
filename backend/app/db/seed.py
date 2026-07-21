import json
import mimetypes
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.base import Base, import_domain_models
from app.db.session import SessionLocal, engine
from app.domains.artifacts.models import AssignmentArtifact
from app.domains.assignments.models import Assignment
from app.domains.assignments.service import upsert_assignment_config
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Module, Section


SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
EXAMPLE_DIR = SEEDS_DIR / "simple_python_functions"
EXAMPLE_CONFIG = EXAMPLE_DIR / "config_json.example.json"
CS1410_CATALOG = SEEDS_DIR / "cs1410_catalog.json"


def load_example_config() -> dict:
    return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))


def load_cs1410_catalog() -> dict:
    return json.loads(CS1410_CATALOG.read_text(encoding="utf-8"))


def _seed_storage_ref(
    example_slug: str,
    artifact_key: str,
    display_filename: str,
) -> str:
    return f"seed://{example_slug}/{display_filename}"


def resolve_seed_artifact_path(
    seed_dir: Path,
    display_filename: str,
    *,
    artifact_type: str | None = None,
) -> Path | None:
    """Resolve a seed artifact file under the assignment folder or seeds/shared."""
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


def _seed_assignment_artifacts(
    db: Session,
    assignment: Assignment,
    slug: str,
) -> None:
    folder = slug.replace("-", "_")
    config_path = SEEDS_DIR / folder / "config_json.example.json"
    if not config_path.exists():
        return

    config_json = json.loads(config_path.read_text(encoding="utf-8"))
    upsert_assignment_config(db, assignment, config_json)

    db.query(AssignmentArtifact).filter(AssignmentArtifact.assignment_id == assignment.id).delete()

    for artifact_key, artifact in (config_json.get("artifacts") or {}).items():
        display_filename = artifact.get("display_filename")
        if not display_filename:
            continue

        resolved = resolve_seed_artifact_path(
            SEEDS_DIR / folder,
            display_filename,
            artifact_type=artifact.get("type"),
        )
        if resolved is None:
            continue
        artifact_folder = "shared" if resolved.parent.name == "shared" else folder

        db.add(
            AssignmentArtifact(
                assignment=assignment,
                artifact_key=artifact_key,
                artifact_type=artifact["type"],
                storage_ref=_seed_storage_ref(
                    artifact_folder,
                    artifact_key,
                    resolved.name,
                ),
                display_filename=display_filename,
                content_type=mimetypes.guess_type(display_filename)[0]
                or "application/octet-stream",
            )
        )


def initialize_database(seed: bool = True) -> None:
    import_domain_models()
    Base.metadata.create_all(bind=engine)
    if seed:
        with SessionLocal() as db:
            if engine.dialect.name == "sqlite":
                # Serialize check-then-insert seed logic across reload/workers.
                db.execute(text("BEGIN IMMEDIATE"))
            seed_development_data(db)


def _seed_cs1400(
    db: Session,
    *,
    staff_user: User,
    admin_role: Role,
) -> None:
    course = Course(
        code="cs1400",
        title="CS 1400: Fundamentals of Programming",
        term="Spring 2026",
        default_concepts=["variables", "conditionals"],
        instructor=staff_user,
    )
    db.add(course)
    db.flush()

    module = Module(
        course=course,
        name="Module 1: Expressions & Conditionals",
        concepts=["variables"],
    )
    section = Section(course=course, crn="12345")
    db.add_all([module, section])
    db.flush()

    db.add(
        StaffAccess(
            user=staff_user,
            role=admin_role,
            course=course,
            section=section,
        )
    )
    assignment = Assignment(
        course=course,
        slug="simple-python-functions",
        title="Simple Python Functions",
        language="python",
        canvas_ref="canvas:synthetic:simple-python-functions",
        sandbox_enabled=True,
        module=module,
        is_active=True,
    )
    db.add(assignment)
    db.flush()
    _seed_assignment_artifacts(db, assignment, assignment.slug)


def _seed_cs1410(
    db: Session,
    *,
    staff_user: User,
    admin_role: Role,
) -> None:
    catalog = load_cs1410_catalog()
    course = Course(
        code="cs1410",
        title="CS 1410: Object-Oriented Programming",
        term="Spring 2026",
        default_concepts=["variables", "conditionals", "loops", "functions"],
        instructor=staff_user,
    )
    db.add(course)
    db.flush()

    modules = {}
    accumulated_concepts: set[str] = set(course.default_concepts or [])
    for code, module_data in catalog["modules"].items():
        for c in module_data.get("concepts", []):
            accumulated_concepts.add(c)
        module = Module(
            course=course,
            name=module_data["name"],
            concepts=list(accumulated_concepts),
        )
        db.add(module)
        modules[code] = module
    db.flush()

    section = Section(course=course, crn="67890")
    db.add(section)
    db.add(
        StaffAccess(
            user=staff_user,
            role=admin_role,
            course=course,
            section=section,
        )
    )

    for assignment_data in catalog["assignments"]:
        slug = assignment_data["slug"]
        assignment = Assignment(
            course=course,
            slug=slug,
            title=assignment_data["title"],
            language="python",
            canvas_ref=f"canvas:synthetic:{slug}",
            sandbox_enabled=True,
            module=modules[assignment_data["module"]],
            is_active=True,
        )
        db.add(assignment)
        db.flush()
        _seed_assignment_artifacts(db, assignment, slug)


def seed_development_data(db: Session) -> None:
    roles = {}
    for name in ("admin", "instructor", "IA"):
        role = db.scalar(select(Role).where(Role.name == name))
        if role is None:
            role = Role(name=name)
            db.add(role)
        roles[name] = role
    db.flush()

    staff_user = db.scalar(select(User).where(User.email == "dev.staff@uvu.edu"))
    if staff_user is None:
        staff_user = User(
            email="dev.staff@uvu.edu",
            display_name="Development Staff",
        )
        db.add(staff_user)
        db.flush()

    if db.scalar(select(Course).where(Course.code == "cs1400")) is None:
        _seed_cs1400(db, staff_user=staff_user, admin_role=roles["admin"])

    if db.scalar(select(Course).where(Course.code == "cs1410")) is None:
        _seed_cs1410(db, staff_user=staff_user, admin_role=roles["admin"])

    db.commit()


if __name__ == "__main__":
    initialize_database(seed=True)

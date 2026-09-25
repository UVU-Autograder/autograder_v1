import json
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.base import Base, import_domain_models
from app.db.session import SessionLocal, engine
from app.domains.assignments.models import Assignment
from app.domains.assignments.service import (
    resolve_seed_artifact_path as resolve_seed_artifact_path,
    seed_assignment_artifacts,
)
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Module, Section

SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
EXAMPLE_DIR = SEEDS_DIR / "simple_python_functions"
EXAMPLE_CONFIG = EXAMPLE_DIR / "config_json.example.json"
CS1400_CATALOG = SEEDS_DIR / "cs1400_catalog.json"
CS1410_CATALOG = SEEDS_DIR / "cs1410_catalog.json"


def load_example_config() -> dict:
    return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))


def load_cs1400_catalog() -> dict:
    if CS1400_CATALOG.exists():
        return json.loads(CS1400_CATALOG.read_text(encoding="utf-8"))
    return {}


def load_cs1410_catalog() -> dict:
    return json.loads(CS1410_CATALOG.read_text(encoding="utf-8"))


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
    catalog = load_cs1400_catalog()
    course = Course(
        code="cs1400",
        title="Fundamentals of Programming",
        term="Spring 2026",
        default_concepts=["variables", "conditionals"],
        instructor=staff_user,
    )
    db.add(course)
    db.flush()

    modules = {}
    accumulated_concepts: set[str] = set(course.default_concepts or [])
    if catalog and "modules" in catalog:
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
    else:
        module = Module(
            course=course,
            name="Module 1: Expressions & Conditionals",
            concepts=["variables"],
        )
        db.add(module)
        modules["m1"] = module
    db.flush()

    section = Section(course=course, crn="12345")
    db.add(section)
    db.add(
        StaffAccess(
            user=staff_user,
            role=admin_role,
            course=course,
            section=section,
        )
    )

    if catalog and "assignments" in catalog:
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
            seed_assignment_artifacts(db, assignment, slug)
    else:
        assignment = Assignment(
            course=course,
            slug="simple-python-functions",
            title="Simple Python Functions",
            language="python",
            canvas_ref="canvas:synthetic:simple-python-functions",
            sandbox_enabled=True,
            module=modules["m1"],
            is_active=True,
        )
        db.add(assignment)
        db.flush()
        seed_assignment_artifacts(db, assignment, assignment.slug)


def _seed_cs1410(
    db: Session,
    *,
    staff_user: User,
    admin_role: Role,
) -> None:
    catalog = load_cs1410_catalog()
    course = Course(
        code="cs1410",
        title="Object-Oriented Programming",
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
        seed_assignment_artifacts(db, assignment, slug)


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

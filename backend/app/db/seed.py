import json
import logging
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

logger = logging.getLogger(__name__)

SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
EXAMPLE_DIR = SEEDS_DIR / "simple-python-functions"
EXAMPLE_CONFIG = EXAMPLE_DIR / "config.json"
CS1400_CATALOG = SEEDS_DIR / "cs1400_catalog.json"
CS1410_CATALOG = SEEDS_DIR / "cs1410_catalog.json"


def load_example_config() -> dict:
    return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))


def load_cs1400_catalog() -> dict:
    return json.loads(CS1400_CATALOG.read_text(encoding="utf-8"))


def load_cs1410_catalog() -> dict:
    return json.loads(CS1410_CATALOG.read_text(encoding="utf-8"))


def seed_judge0_language(db_url: str | None = None) -> bool:
    """Idempotently seed custom language 711 into Judge0 PostgreSQL database."""
    from app.core.settings import get_settings

    url = db_url or get_settings().database_url
    if not url or ("postgresql" not in url and "postgres" not in url):
        return False
    try:
        from sqlalchemy import create_engine

        judge0_url = url.rsplit("/", 1)[0] + "/judge0"
        judge0_engine = create_engine(judge0_url, pool_pre_ping=True)
        seed_sql = (
            "INSERT INTO languages (id, name, compile_cmd, run_cmd, source_file, is_archived) "
            "VALUES (711, 'Python (3.11.9)', NULL, '/usr/local/python-3.11.9/bin/python3.11 script.py', 'script.py', false) "
            "ON CONFLICT (id) DO UPDATE SET "
            "name = EXCLUDED.name, "
            "compile_cmd = EXCLUDED.compile_cmd, "
            "run_cmd = EXCLUDED.run_cmd, "
            "source_file = EXCLUDED.source_file, "
            "is_archived = EXCLUDED.is_archived;"
        )
        with judge0_engine.connect() as conn:
            conn.execute(text(seed_sql))
            conn.commit()
        return True
    except Exception as exc:
        logger.debug("Judge0 language seed attempt skipped or failed: %s", exc)
        return False


def initialize_database(seed: bool = True) -> None:
    import_domain_models()
    Base.metadata.create_all(bind=engine)
    if seed:
        with SessionLocal() as db:
            if engine.dialect.name == "sqlite":
                # Serialize check-then-insert seed logic across reload/workers.
                db.execute(text("BEGIN IMMEDIATE"))
            seed_development_data(db)
        seed_judge0_language()


def _seed_cs1400(
    db: Session,
    *,
    staff_user: User,
    admin_role: Role,
) -> None:
    catalog = load_cs1400_catalog()
    course = db.scalar(select(Course).where(Course.code == "cs1400"))
    if course is None:
        course = Course(
            code="cs1400",
            title="Fundamentals of Programming",
            term="Fall 2026",
            default_concepts=["variables", "conditionals"],
            instructor=staff_user,
        )
        db.add(course)
        db.flush()

    existing_modules = {m.name: m for m in course.modules}
    modules = {}
    accumulated_concepts: set[str] = set(course.default_concepts or [])
    for code, module_data in catalog["modules"].items():
        for c in module_data.get("concepts", []):
            accumulated_concepts.add(c)
        if module_data["name"] in existing_modules:
            module = existing_modules[module_data["name"]]
            module.concepts = list(accumulated_concepts)
        else:
            module = Module(
                course=course,
                name=module_data["name"],
                concepts=list(accumulated_concepts),
            )
            db.add(module)
        modules[code] = module
    db.flush()

    section = db.scalar(select(Section).where(Section.course_id == course.id, Section.crn == "12345"))
    if section is None:
        section = Section(course=course, crn="12345")
        db.add(section)
        db.flush()

    existing_staff_access = db.scalar(
        select(StaffAccess).where(
            StaffAccess.user_id == staff_user.id,
            StaffAccess.course_id == course.id,
            StaffAccess.section_id == section.id,
        )
    )
    if existing_staff_access is None:
        db.add(
            StaffAccess(
                user=staff_user,
                role=admin_role,
                course=course,
                section=section,
            )
        )

    from app.core.settings import get_settings

    settings = get_settings()

    legacy_module = db.scalar(
        select(Module).where(
            Module.course_id == course.id,
            Module.name == "Module 1: Expressions & Conditionals",
        )
    )
    if legacy_module is not None:
        db.delete(legacy_module)
        db.flush()

    if settings.is_sqlite:
        fixture_assignment = db.scalar(
            select(Assignment).where(Assignment.course_id == course.id, Assignment.slug == "simple-python-functions")
        )
        if fixture_assignment is None:
            fixture_assignment = Assignment(
                course=course,
                slug="simple-python-functions",
                title="Simple Python Functions",
                language="python",
                canvas_ref="canvas:synthetic:simple-python-functions",
                sandbox_enabled=True,
                module=modules["m1"],
                is_active=True,
            )
            db.add(fixture_assignment)
            db.flush()
            seed_assignment_artifacts(db, fixture_assignment, fixture_assignment.slug)
            db.flush()
            from app.domains.assignments.inventory import execution_fingerprint
            from app.domains.grading.report_contract import ValidatedManifest

            cases = [
                {"nodeid": "assignment_tests.py::test_add_numbers_positive_values", "markers": ["ag_add_numbers"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_add_numbers_negative_values", "markers": ["ag_add_numbers"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_reverse_words_basic_sentence", "markers": ["ag_reverse_words"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_reverse_words_preserves_spacing_between_words", "markers": ["ag_reverse_words"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_count_vowels_lowercase", "markers": ["ag_count_vowels"], "xfail": False},
                {"nodeid": "assignment_tests.py::test_count_vowels_case_insensitive", "markers": ["ag_count_vowels"], "xfail": False},
            ]
            fixture_assignment.config.validated_test_manifest = ValidatedManifest(
                fingerprint=execution_fingerprint(db, fixture_assignment),
                cases=cases,
            ).model_dump(mode="json")
    else:
        legacy_assignment = db.scalar(
            select(Assignment).where(
                Assignment.course_id == course.id,
                Assignment.slug == "simple-python-functions",
            )
        )
        if legacy_assignment is not None:
            db.delete(legacy_assignment)
            db.flush()

    existing_assignments = {a.slug: a for a in course.assignments}
    cs1400_root = Path(__file__).resolve().parents[3] / "cs1400"
    for item in catalog["assignments"]:
        slug = item["slug"]
        desc = item.get("description")
        folder = item.get("folder")
        if not desc and folder:
            desc_path = cs1400_root / folder / "desc.md"
            if desc_path.exists():
                desc = desc_path.read_text(encoding="utf-8")
        if slug in existing_assignments:
            assignment = existing_assignments[slug]
            assignment.title = item["title"]
            assignment.module = modules[item["module"]]
            assignment.sandbox_enabled = True
            if desc:
                assignment.description = desc
        else:
            assignment = Assignment(
                course=course,
                slug=slug,
                title=item["title"],
                language="python",
                canvas_ref=f"canvas:synthetic:{slug}",
                sandbox_enabled=True,
                module=modules[item["module"]],
                description=desc,
                is_active=True,
            )
            db.add(assignment)

    db.commit()


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
        term="Fall 2026",
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

    _seed_cs1400(db, staff_user=staff_user, admin_role=roles["admin"])

    if db.scalar(select(Course).where(Course.code == "cs1410")) is None:
        _seed_cs1410(db, staff_user=staff_user, admin_role=roles["admin"])

    db.commit()


if __name__ == "__main__":
    initialize_database(seed=True)

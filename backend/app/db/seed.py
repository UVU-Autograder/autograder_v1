from pathlib import Path
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base, import_domain_models
from app.db.session import engine, SessionLocal
from app.domains.artifacts.models import AssignmentArtifact
from app.domains.assignments.models import Assignment
from app.domains.assignments.service import upsert_assignment_config
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Section


REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = REPO_ROOT / "docs" / "backend_implementation" / "examples" / "simple_python_functions"
EXAMPLE_CONFIG = EXAMPLE_DIR / "config_json.example.json"


def load_example_config() -> dict:
    return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))


def initialize_database(seed: bool = True) -> None:
    import_domain_models()
    Base.metadata.create_all(bind=engine)
    if seed:
        with SessionLocal() as db:
            seed_development_data(db)


def seed_development_data(db: Session) -> None:
    if db.scalar(select(Course).where(Course.code == "cs1400")) is not None:
        return

    roles = {name: Role(name=name) for name in ("admin", "instructor", "IA")}
    db.add_all(roles.values())

    staff_user = User(email="dev.staff@uvu.edu", display_name="Development Staff")
    course = Course(
        code="cs1400",
        title="CS 1400: Programming Foundations",
        term="Spring 2026",
        default_concepts=["variables", "conditionals"],
    )
    section = Section(course=course, crn="12345", name="Section 001")
    assignment = Assignment(
        course=course,
        slug="simple-python-functions",
        title="Simple Python Functions",
        language="python",
        canvas_ref="canvas:synthetic:simple-python-functions",
        due_label="Practice",
        sandbox_enabled=True,
        is_active=True,
    )
    db.add_all([staff_user, course, section, assignment])
    db.flush()

    db.add(
        StaffAccess(
            user=staff_user,
            role=roles["admin"],
            course=course,
            section=None,
        )
    )

    config_json = load_example_config()
    upsert_assignment_config(db, assignment, config_json)

    artifacts = config_json["artifacts"]
    db.add_all(
        AssignmentArtifact(
            assignment=assignment,
            artifact_key=artifact_key,
            artifact_type=artifact["type"],
            storage_ref=f"seed://simple_python_functions/{artifact['display_filename']}",
            display_filename=artifact.get("display_filename"),
            content_type="text/plain",
        )
        for artifact_key, artifact in artifacts.items()
    )
    db.commit()


if __name__ == "__main__":
    initialize_database(seed=True)

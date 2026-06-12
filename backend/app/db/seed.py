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
        staff_user = User(email="dev.staff@uvu.edu", display_name="Development Staff")
        db.add(staff_user)
        db.flush()

    course_cs1400 = db.scalar(select(Course).where(Course.code == "cs1400"))
    if course_cs1400 is None:
        course_cs1400 = Course(
            code="cs1400",
            title="CS 1400: Programming Foundations",
            term="Spring 2026",
            default_concepts=["variables", "conditionals"],
        )
        db.add(course_cs1400)
        db.flush()

        section = Section(course=course_cs1400, crn="12345", name="Section 001")
        db.add(section)

        db.add(
            StaffAccess(
                user=staff_user,
                role=roles["admin"],
                course=course_cs1400,
                section=None,
            )
        )

        assignment = Assignment(
            course=course_cs1400,
            slug="simple-python-functions",
            title="Simple Python Functions",
            language="python",
            canvas_ref="canvas:synthetic:simple-python-functions",
            due_label="Practice",
            sandbox_enabled=True,
            is_active=True,
        )
        db.add(assignment)
        db.flush()

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

    course_cs1410 = db.scalar(select(Course).where(Course.code == "cs1410"))
    if course_cs1410 is None:
        course_cs1410 = Course(
            code="cs1410",
            title="CS 1410: Object-Oriented Programming",
            term="Spring 2026",
            default_concepts=["image-processing", "file-io", "loops"],
        )
        db.add(course_cs1410)
        db.flush()

        section = Section(course=course_cs1410, crn="67890", name="Section 001")
        db.add(section)

        db.add(
            StaffAccess(
                user=staff_user,
                role=roles["admin"],
                course=course_cs1410,
                section=None,
            )
        )

        assignment_cs1410 = Assignment(
            course=course_cs1410,
            slug="lab-1-image-processing",
            title="Lab 1: Image Processing",
            language="python",
            canvas_ref="canvas:synthetic:lab-1-image-processing",
            due_label="Required",
            sandbox_enabled=True,
            is_active=True,
        )
        db.add(assignment_cs1410)
        db.flush()

        cs1410_config_path = EXAMPLE_DIR.parent / "lab_1_image_processing" / "config_json.example.json"
        config_json_cs1410 = json.loads(cs1410_config_path.read_text(encoding="utf-8"))
        upsert_assignment_config(db, assignment_cs1410, config_json_cs1410)

        artifacts = config_json_cs1410["artifacts"]
        db.add_all(
            AssignmentArtifact(
                assignment=assignment_cs1410,
                artifact_key=artifact_key,
                artifact_type=artifact["type"],
                storage_ref=f"seed://lab_1_image_processing/{artifact['display_filename']}",
                display_filename=artifact.get("display_filename"),
                content_type="text/plain",
            )
            for artifact_key, artifact in artifacts.items()
        )
    db.commit()


if __name__ == "__main__":
    initialize_database(seed=True)

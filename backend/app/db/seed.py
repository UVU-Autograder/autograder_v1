from pathlib import Path
import json
import mimetypes
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base, import_domain_models
from app.db.session import engine, SessionLocal
from app.domains.artifacts.models import AssignmentArtifact
from app.domains.assignments.models import Assignment
from app.domains.assignments.service import upsert_assignment_config
from app.domains.auth.models import Role, StaffAccess, User
from app.domains.courses.models import Course, Section, Module


SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
EXAMPLE_DIR = SEEDS_DIR / "simple_python_functions"
EXAMPLE_CONFIG = EXAMPLE_DIR / "config_json.example.json"


def load_example_config() -> dict:
    return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))


def _seed_storage_ref(example_slug: str, artifact_key: str, display_filename: str) -> str:
    return f"seed://{example_slug}/{display_filename}"


def _seed_assignment_artifacts(db: Session, assignment: Assignment, slug: str) -> None:
    folder = slug.replace("-", "_")
    config_path = SEEDS_DIR / folder / "config_json.example.json"
    if not config_path.exists():
        return

    config_json = json.loads(config_path.read_text(encoding="utf-8"))
    upsert_assignment_config(db, assignment, config_json)

    artifacts = config_json.get("artifacts") or {}
    for artifact_key, artifact in artifacts.items():
        display_fn = artifact.get("display_filename")
        if not display_fn:
            continue

        if (SEEDS_DIR / folder / display_fn).exists():
            artifact_folder = folder
        else:
            artifact_folder = "shared"

        db.add(
            AssignmentArtifact(
                assignment=assignment,
                artifact_key=artifact_key,
                artifact_type=artifact["type"],
                storage_ref=_seed_storage_ref(
                    artifact_folder,
                    artifact_key,
                    display_fn,
                ),
                display_filename=display_fn,
                content_type=mimetypes.guess_type(display_fn or "")[0] or "application/octet-stream",
            )
        )


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
            title="CS 1400: Fundamentals of Programming",
            term="Spring 2026",
            default_concepts=["variables", "conditionals"],
            instructor=staff_user,
        )
        db.add(course_cs1400)
        db.flush()

        mod_cs1400 = Module(
            course=course_cs1400,
            name="Module 1: Expressions & Conditionals",
            concepts=["variables"]
        )
        db.add(mod_cs1400)
        db.flush()

        section = Section(course=course_cs1400, crn="12345")
        db.add(section)

        db.add(
            StaffAccess(
                user=staff_user,
                role=roles["admin"],
                course=course_cs1400,
                section=section,
            )
        )

        assignment = Assignment(
            course=course_cs1400,
            slug="simple-python-functions",
            title="Simple Python Functions",
            language="python",
            canvas_ref="canvas:synthetic:simple-python-functions",
            sandbox_enabled=True,
            module=mod_cs1400,
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
                storage_ref=_seed_storage_ref(
                    "simple_python_functions",
                    artifact_key,
                    artifact["display_filename"],
                ),
                display_filename=artifact.get("display_filename"),
                content_type=mimetypes.guess_type(artifact.get("display_filename") or "")[0] or "application/octet-stream",
            )
            for artifact_key, artifact in artifacts.items()
        )

    course_cs1410 = db.scalar(select(Course).where(Course.code == "cs1410"))
    if course_cs1410 is None:
        course_cs1410 = Course(
            code="cs1410",
            title="CS 1410: Object-Oriented Programming",
            term="Spring 2026",
            default_concepts=["variables", "conditionals", "loops", "functions"],
            instructor=staff_user,
        )
        db.add(course_cs1410)
        db.flush()

        # Define the 12 modules for CS 1410 with cumulative concepts
        modules_data = {
            "m1": {"name": "Module 1: Warmup", "concepts": ["image-processing"]},
            "m2": {"name": "Module 2: Object-Oriented Intro", "concepts": ["classes", "type-hints"]},
            "m3": {"name": "Module 3: Inheritance, Polymorphism, and Properties", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading"]},
            "m4": {"name": "Module 4: Generators and Iterators", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators"]},
            "m5": {"name": "Module 5: Unit Tests with pytest", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing"]},
            "m6": {"name": "Module 6: Abstract Classes", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes"]},
            "m7": {"name": "Module 7: Exceptions and Protocols", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes", "exceptions", "protocols"]},
            "m8": {"name": "Module 8: Introduction to Pygame", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes", "exceptions", "protocols", "pygame"]},
            "m9": {"name": "Module 9: Object-Oriented Pygame", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes", "exceptions", "protocols", "pygame"]},
            "m10": {"name": "Module 10: Pygame GUI Widgets", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes", "exceptions", "protocols", "pygame"]},
            "m11": {"name": "Module 11: Named tuples, Dataclasses, and Sorting lists", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes", "exceptions", "protocols", "pygame", "dataclasses", "file-io"]},
            "m12": {"name": "Module 12: CS Degrees at UVU", "concepts": ["classes", "type-hints", "inheritance", "properties", "operator-overloading", "generators", "testing", "abstract-classes", "exceptions", "protocols", "pygame", "dataclasses", "file-io"]},
        }

        mods = {}
        for code, mdata in modules_data.items():
            mod = Module(
                course=course_cs1410,
                name=mdata["name"],
                concepts=mdata["concepts"],
            )
            db.add(mod)
            db.flush()
            mods[code] = mod

        section = Section(course=course_cs1410, crn="67890")
        db.add(section)

        db.add(
            StaffAccess(
                user=staff_user,
                role=roles["admin"],
                course=course_cs1410,
                section=section,
            )
        )

        # Seeding the 17 assignments
        assignments_data = [
            # Module 1
            {
                "module": "m1",
                "slug": "lab-1-image-processing",  # Keep existing slug
                "title": "Lab 1: Image Processing",
                "canvas_ref": "canvas:synthetic:lab-1-image-processing",
            },
            # Module 2
            {
                "module": "m2",
                "slug": "lab2",
                "title": "Lab 2: Bank Account Class",
                "canvas_ref": "canvas:synthetic:lab2",
            },
            {
                "module": "m2",
                "slug": "lab3",
                "title": "Lab 3: Type Hinting and Encapsulation",
                "canvas_ref": "canvas:synthetic:lab3",
            },
            # Module 3
            {
                "module": "m3",
                "slug": "ds1",
                "title": "Dessert Shop 1: Inheritance Superclass",
                "canvas_ref": "canvas:synthetic:ds1",
            },
            {
                "module": "m3",
                "slug": "lab4",
                "title": "Lab 4: Properties and Validation",
                "canvas_ref": "canvas:synthetic:lab4",
            },
            {
                "module": "m3",
                "slug": "lab5",
                "title": "Lab 5: Operator Overloading",
                "canvas_ref": "canvas:synthetic:lab5",
            },
            # Module 4
            {
                "module": "m4",
                "slug": "ds2",
                "title": "Dessert Shop 2: Using Classes in main",
                "canvas_ref": "canvas:synthetic:ds2",
            },
            # Module 5
            {
                "module": "m5",
                "slug": "ds3",
                "title": "Dessert Shop 3: Test Cases with pytest",
                "canvas_ref": "canvas:synthetic:ds3",
            },
            # Module 6
            {
                "module": "m6",
                "slug": "ds4",
                "title": "Dessert Shop 4: Abstraction",
                "canvas_ref": "canvas:synthetic:ds4",
            },
            # Module 7
            {
                "module": "m7",
                "slug": "ds5",
                "title": "Dessert Shop 5: Console Application",
                "canvas_ref": "canvas:synthetic:ds5",
            },
            # Module 8
            {
                "module": "m8",
                "slug": "ds6",
                "title": "Dessert Shop 6: Overriding Methods",
                "canvas_ref": "canvas:synthetic:ds6",
            },
            {
                "module": "m8",
                "slug": "lab6",
                "title": "Lab 6: Moving an Animal Image Left and Right",
                "canvas_ref": "canvas:synthetic:lab6",
            },
            # Module 9
            {
                "module": "m9",
                "slug": "ds7",
                "title": "Dessert Shop 7: Mixin Interface",
                "canvas_ref": "canvas:synthetic:ds7",
            },
            # Module 10
            {
                "module": "m10",
                "slug": "ds8",
                "title": "Dessert Shop 8: Payment Method",
                "canvas_ref": "canvas:synthetic:ds8",
            },
            # Module 11
            {
                "module": "m11",
                "slug": "ds9",
                "title": "Dessert Shop 9: Sort Receipt Items",
                "canvas_ref": "canvas:synthetic:ds9",
            },
            {
                "module": "m11",
                "slug": "lab7",
                "title": "Lab 7: Modeling College Students with Data Classes",
                "canvas_ref": "canvas:synthetic:lab7",
            },
            # Module 12
            {
                "module": "m12",
                "slug": "ds10",
                "title": "Dessert Shop 10: Combine Like Items",
                "canvas_ref": "canvas:synthetic:ds10",
            },
        ]

        for adata in assignments_data:
            assignment = Assignment(
                course=course_cs1410,
                slug=adata["slug"],
                title=adata["title"],
                language="python",
                canvas_ref=adata["canvas_ref"],
                sandbox_enabled=True,
                module=mods[adata["module"]],
                is_active=True,
            )
            db.add(assignment)
            db.flush()

            # Seed detailed config and artifacts if they exist
            _seed_assignment_artifacts(db, assignment, adata["slug"])
    db.commit()


if __name__ == "__main__":
    initialize_database(seed=True)

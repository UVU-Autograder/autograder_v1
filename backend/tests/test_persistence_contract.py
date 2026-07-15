import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_domain_models  # noqa: E402
from app.db.seed import initialize_database, load_example_config  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
import app.domains.assignments.models as assignment_models  # noqa: E402
from app.domains.assignments.schemas import (  # noqa: E402
    AssignmentConfigV1,
    StaffAssignmentSetupUpdate,
    pytest_marker_for_key,
)
from app.domains.assignments.service import update_staff_setup  # noqa: E402


@pytest.fixture(autouse=True)
def initialized_database():
    import_domain_models()
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)
    yield
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)


def test_assignment_config_accepts_simple_python_example():
    config = AssignmentConfigV1.model_validate(load_example_config())

    assert config.schema_version == 1
    assert config.base_points == 25
    assert config.extra_credit_points == 0
    assert pytest_marker_for_key(config.tests[0].key) == "ag_add_numbers"


def test_assignment_config_rejects_missing_schema_version():
    raw = load_example_config()
    raw.pop("schema_version")

    with pytest.raises(ValidationError):
        AssignmentConfigV1.model_validate(raw)


def test_assignment_config_rejects_duplicate_test_keys():
    raw = load_example_config()
    raw["tests"][1]["key"] = raw["tests"][0]["key"]

    with pytest.raises(ValidationError, match="duplicate test keys"):
        AssignmentConfigV1.model_validate(raw)


def test_assignment_config_rejects_missing_extra_credit():
    raw = load_example_config()
    raw["tests"][0].pop("extra_credit")

    with pytest.raises(ValidationError):
        AssignmentConfigV1.model_validate(raw)


def test_assignment_config_rejects_invalid_completion_reference():
    raw = load_example_config()
    raw["completion_requirements"] = [
        {
            "key": "complete_two",
            "label": "Complete two",
            "test_keys": ["add_numbers", "missing_key"],
            "minimum_passed": 2,
        }
    ]

    with pytest.raises(ValidationError, match="unknown tests"):
        AssignmentConfigV1.model_validate(raw)


def test_initial_metadata_tables_exist():
    table_names = set(inspect(engine).get_table_names())

    assert {
        "users",
        "roles",
        "courses",
        "sections",
        "staff_access",
        "assignments",
        "assignment_configs",
        "assignment_artifacts",
        "scoring_items",
        "run_summaries",
    }.issubset(table_names)


def test_seed_creates_assignment_artifacts_and_derived_test_cases():
    with SessionLocal() as db:
        # Check cs1400
        assignment = db.scalar(
            select(assignment_models.Assignment).where(
                assignment_models.Assignment.slug == "simple-python-functions"
            )
        )
        assert assignment is not None
        assert assignment.config is not None
        assert {artifact.artifact_type for artifact in assignment.artifacts} == {
            "pytest_file",
            "model_solution",
            "support_file",
        }
        # Check cs1410
        assignment_cs1410 = db.scalar(
            select(assignment_models.Assignment).where(
                assignment_models.Assignment.slug == "lab-1-image-processing"
            )
        )
        assert assignment_cs1410 is not None
        assert assignment_cs1410.config is not None
        assert {artifact.artifact_type for artifact in assignment_cs1410.artifacts} == {
            "pytest_file",
            "model_solution",
            "support_file",
        }
        
        scoring_items = db.scalars(
            select(assignment_models.ScoringItem)
            .where(assignment_models.ScoringItem.assignment_id == assignment_cs1410.id)
            .order_by(assignment_models.ScoringItem.display_order)
        ).all()
        assert len(scoring_items) == 6
        assert [item.config_item_key for item in scoring_items] == [
            "part1_files",
            "part1_output",
            "part2_files",
            "part2_output",
            "part1_visual",
            "part2_visual",
        ]
        assert [item.item_type for item in scoring_items] == [
            "pytest",
            "pytest",
            "pytest",
            "pytest",
            "manual",
            "manual",
        ]
        assert [item.pytest_marker for item in scoring_items] == [
            "ag_part1_files",
            "ag_part1_output",
            "ag_part2_files",
            "ag_part2_output",
            None,
            None,
        ]

        # Check ds1
        assignment_ds1 = db.scalar(
            select(assignment_models.Assignment).where(
                assignment_models.Assignment.slug == "ds1"
            )
        )
        assert assignment_ds1 is not None
        assert assignment_ds1.config is not None
        assert {artifact.artifact_type for artifact in assignment_ds1.artifacts} == {
            "pytest_file",
            "model_solution",
        }

        scoring_items_ds1 = db.scalars(
            select(assignment_models.ScoringItem)
            .where(assignment_models.ScoringItem.assignment_id == assignment_ds1.id)
            .order_by(assignment_models.ScoringItem.display_order)
        ).all()
        assert len(scoring_items_ds1) == 5
        assert [item.config_item_key for item in scoring_items_ds1] == [
            "dessert_item",
            "candy",
            "cookie",
            "icecream",
            "sundae",
        ]
        assert [item.item_type for item in scoring_items_ds1] == [
            "pytest",
            "pytest",
            "pytest",
            "pytest",
            "pytest",
        ]
        assert [item.pytest_marker for item in scoring_items_ds1] == [
            "ag_dessert_item",
            "ag_candy",
            "ag_cookie",
            "ag_icecream",
            "ag_sundae",
        ]


def test_seed_is_idempotent():
    from sqlalchemy import func
    from app.domains.courses.models import Course

    with SessionLocal() as db:
        num_courses_before = db.scalar(select(func.count(Course.id)))
        num_assignments_before = db.scalar(select(func.count(assignment_models.Assignment.id)))

    # Re-run initialization/seeding
    initialize_database(seed=True)

    with SessionLocal() as db:
        num_courses_after = db.scalar(select(func.count(Course.id)))
        num_assignments_after = db.scalar(select(func.count(assignment_models.Assignment.id)))
        assert num_courses_before == num_courses_after
        assert num_assignments_before == num_assignments_after




def test_manual_rubric_items_derive_non_pytest_scoring_projections():
    raw = load_example_config()
    raw["manual_rubric_items"] = [
        {
            "key": "reflection_quality",
            "label": "Quality of the reflection report",
            "points": 10,
            "extra_credit": False,
        }
    ]

    with SessionLocal() as db:
        setup = update_staff_setup(
            db,
            "cs1400",
            "simple-python-functions",
            StaffAssignmentSetupUpdate(
                config_json=AssignmentConfigV1.model_validate(raw),
                title="Simple Python Functions",
                sandbox_enabled=True,
            ),
        )
        assert setup is not None

        items = db.scalars(
            select(assignment_models.ScoringItem)
            .join(assignment_models.ScoringItem.assignment)
            .where(assignment_models.Assignment.slug == "simple-python-functions")
            .order_by(assignment_models.ScoringItem.display_order)
        ).all()
        
        # Should have the 3 pytest tests plus the 1 manual rubric item
        assert len(items) == 4
        manual_item = items[-1]
        assert manual_item.config_item_key == "reflection_quality"
        assert manual_item.item_type == "manual"
        assert manual_item.pytest_marker is None
        assert manual_item.points == 10

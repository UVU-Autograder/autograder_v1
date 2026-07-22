import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import func, inspect, select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import app.domains.assignments.models as assignment_models  # noqa: E402
from app.db.seed import (  # noqa: E402
    SEEDS_DIR,
    initialize_database,
    load_example_config,
)
from app.db.session import SessionLocal, engine  # noqa: E402
from app.domains.assignments.schemas import (  # noqa: E402
    AssignmentConfigV1,
    StaffAssignmentSetupUpdate,
    pytest_marker_for_key,
)
from app.domains.assignments.service import update_staff_setup  # noqa: E402
from app.domains.courses.models import Course  # noqa: E402


@pytest.fixture(autouse=True)
def initialized_database(reset_database):
    yield


def test_assignment_config_accepts_simple_python_example():
    config = AssignmentConfigV1.model_validate(load_example_config())

    assert config.base_points == 25
    assert config.extra_credit_points == 0
    assert pytest_marker_for_key(config.scoring_items[0].key) == "ag_add_numbers"


def test_assignment_config_rejects_duplicate_test_keys():
    raw = load_example_config()
    raw["scoring_items"][1]["key"] = raw["scoring_items"][0]["key"]

    with pytest.raises(ValidationError, match="duplicate scoring item keys"):
        AssignmentConfigV1.model_validate(raw)


def test_assignment_config_rejects_missing_extra_credit():
    raw = load_example_config()
    raw["scoring_items"][0].pop("extra_credit")

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


@pytest.mark.parametrize(
    "seed_dir",
    [
        path
        for path in SEEDS_DIR.iterdir()
        if path.is_dir()
        and path.name != "shared"
        and (path / "config_json.example.json").exists()
    ],
    ids=lambda path: path.name,
)
def test_seed_creates_artifacts_and_scoring_items_from_config(seed_dir: Path):
    raw = json.loads(
        (seed_dir / "config_json.example.json").read_text(encoding="utf-8")
    )
    config = AssignmentConfigV1.model_validate(raw)
    slug = seed_dir.name.replace("_", "-")

    with SessionLocal() as db:
        assignment = db.scalar(
            select(assignment_models.Assignment).where(
                assignment_models.Assignment.slug == slug
            )
        )
        assert assignment is not None
        assert assignment.config is not None
        assert {artifact.artifact_type for artifact in assignment.artifacts} == {
            artifact.type for artifact in config.artifacts.values()
        }

        scoring_items = db.scalars(
            select(assignment_models.ScoringItem)
            .where(assignment_models.ScoringItem.assignment_id == assignment.id)
            .order_by(assignment_models.ScoringItem.display_order)
        ).all()

        expected_keys = [item.key for item in config.scoring_items]
        assert [item.config_item_key for item in scoring_items] == expected_keys
        assert [item.item_type for item in scoring_items] == [
            item.item_type for item in config.scoring_items
        ]
        assert [item.pytest_marker for item in scoring_items] == [
            pytest_marker_for_key(item.key) if item.item_type == "pytest" else None
            for item in config.scoring_items
        ]


def test_seed_is_idempotent():
    with SessionLocal() as db:
        num_courses_before = db.scalar(select(func.count(Course.id)))
        num_assignments_before = db.scalar(
            select(func.count(assignment_models.Assignment.id))
        )

    initialize_database(seed=True)

    with SessionLocal() as db:
        num_courses_after = db.scalar(select(func.count(Course.id)))
        num_assignments_after = db.scalar(
            select(func.count(assignment_models.Assignment.id))
        )
        assert num_courses_before == num_courses_after
        assert num_assignments_before == num_assignments_after


def test_manual_rubric_items_derive_non_pytest_scoring_projections():
    raw = load_example_config()
    raw["scoring_items"].append({
        "key": "reflection_quality",
        "label": "Quality of the reflection report",
        "points": 10,
        "extra_credit": False,
        "item_type": "manual",
    })

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
            .where(
                assignment_models.Assignment.slug == "simple-python-functions"
            )
            .order_by(assignment_models.ScoringItem.display_order)
        ).all()

        assert len(items) == 4
        manual_item = items[-1]
        assert manual_item.config_item_key == "reflection_quality"
        assert manual_item.item_type == "manual"
        assert manual_item.pytest_marker is None
        assert manual_item.points == 10

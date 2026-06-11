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
        "assignment_concepts",
        "assignment_artifacts",
        "test_cases",
        "run_summaries",
    }.issubset(table_names)


def test_seed_creates_assignment_artifacts_and_derived_test_cases():
    with SessionLocal() as db:
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
        assert [case.pytest_marker for case in assignment.test_cases] == [
            "ag_add_numbers",
            "ag_reverse_words",
            "ag_count_vowels",
        ]


def test_setup_update_regenerates_derived_test_cases():
    raw = load_example_config()
    raw["tests"] = raw["tests"][:2]
    raw["tests"][1]["points"] = 12

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

        cases = db.scalars(
            select(assignment_models.TestCase)
            .join(assignment_models.TestCase.assignment)
            .where(assignment_models.Assignment.slug == "simple-python-functions")
            .order_by(assignment_models.TestCase.display_order)
        ).all()
        assert [case.config_test_key for case in cases] == ["add_numbers", "reverse_words"]
        assert cases[1].points == 12

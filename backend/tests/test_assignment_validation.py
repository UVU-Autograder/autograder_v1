import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.domains.assignments.service import (
    get_assignment_for_course,
    save_artifact,
)
from app.domains.assignments.validation import (
    extract_ag_markers,
    run_preflight_validation,
)


@pytest.fixture(autouse=True)
def _isolate_storage(temp_artifact_storage):
    yield


def test_extract_ag_markers():
    code = """
import pytest
from pytest import mark
from pytest.mark import ag_count_vowels

@pytest.mark.ag_add_numbers
def test_add():
    pass

@mark.ag_reverse_words()
async def test_reverse():
    pass

@ag_count_vowels(123)
def test_vowels():
    pass

@pytest.mark.other_decorator
def test_other():
    pass

@pytest.mark.ag_another
class TestClass:
    # decorators on classes should be ignored
    pass
"""
    markers = extract_ag_markers(code)
    assert markers == {"ag_add_numbers", "ag_reverse_words", "ag_count_vowels"}


def test_extract_ag_markers_syntax_error():
    code = """
import pytest

@pytest.mark.ag_add_numbers
def test_add(
    # syntax error
"""
    markers = extract_ag_markers(code)
    assert markers == set()


def test_run_preflight_validation_missing_pytest_artifact(db_session):
    # Retrieve seed assignment
    assignment = get_assignment_for_course(db_session, "cs1400", "simple-python-functions")
    assert assignment is not None

    # Delete existing artifacts to simulate missing pytest artifact
    for artifact in list(assignment.artifacts):
        db_session.delete(artifact)
    db_session.commit()

    errors = run_preflight_validation(db_session, "cs1400", "simple-python-functions")
    assert any("At least one 'pytest_file' artifact is required" in err for err in errors)


def test_run_preflight_validation_missing_markers(db_session):
    # Seed assignment exists. Let's upload a pytest file that is missing 'ag_count_vowels' marker
    test_code = """
import pytest

@pytest.mark.ag_add_numbers
def test_add():
    pass

@pytest.mark.ag_reverse_words
def test_rev():
    pass
"""
    # config requires: add_numbers, reverse_words, count_vowels
    # We save this pytest file
    save_artifact(
        db=db_session,
        course_code="cs1400",
        assignment_slug="simple-python-functions",
        artifact_key="assignment_tests",
        artifact_type="pytest_file",
        display_filename="assignment_tests.py",
        file_content=test_code.encode("utf-8"),
    )

    errors = run_preflight_validation(db_session, "cs1400", "simple-python-functions")
    assert len(errors) == 1
    assert "ag_count_vowels" in errors[0]


def test_run_preflight_validation_success(db_session):
    test_code = """
import pytest

@pytest.mark.ag_add_numbers
def test_add():
    pass

@pytest.mark.ag_reverse_words
def test_rev():
    pass

@pytest.mark.ag_count_vowels
def test_vowels():
    pass
"""
    save_artifact(
        db=db_session,
        course_code="cs1400",
        assignment_slug="simple-python-functions",
        artifact_key="assignment_tests",
        artifact_type="pytest_file",
        display_filename="assignment_tests.py",
        file_content=test_code.encode("utf-8"),
    )

    errors = run_preflight_validation(db_session, "cs1400", "simple-python-functions")
    assert errors == []


def test_run_preflight_validation_ds1_passes(db_session: Session) -> None:
    errors = run_preflight_validation(db_session, "cs1410", "ds1")
    assert errors == []


def test_assignment_config_comparison_mode_defaults_and_overrides():
    from app.domains.assignments.schemas import AssignmentConfigV1
    from pydantic import ValidationError

    raw_config = {
        "bundle": {"entrypoint": "main.py"},
        "artifacts": {"tests": {"type": "pytest_file"}},
        "comparison_mode": "exact",
        "tolerance": 0.005,
        "scoring_items": [
            {
                "key": "test_inherited",
                "label": "Inherited Exact",
                "points": 10,
                "extra_credit": False,
            },
            {
                "key": "test_override",
                "label": "Overridden Regex",
                "points": 10,
                "extra_credit": False,
                "comparison_mode": "regex",
            },
            {
                "key": "test_custom_tol",
                "label": "Custom Tolerance",
                "points": 10,
                "extra_credit": False,
                "comparison_mode": "numeric_tolerance",
                "tolerance": 1e-6,
            },
        ],
    }

    config = AssignmentConfigV1.model_validate(raw_config)
    assert config.comparison_mode == "exact"
    assert config.tolerance == 0.005

    # Inherited item gets assignment defaults
    assert config.scoring_items[0].comparison_mode == "exact"
    assert config.scoring_items[0].tolerance == 0.005

    # Overridden item preserves explicit comparison_mode
    assert config.scoring_items[1].comparison_mode == "regex"
    assert config.scoring_items[1].tolerance == 0.005

    # Custom tolerance item preserves explicit tolerance
    assert config.scoring_items[2].comparison_mode == "numeric_tolerance"
    assert config.scoring_items[2].tolerance == 1e-6

    # Invalid mode raises ValidationError
    with pytest.raises(ValidationError):
        AssignmentConfigV1.model_validate({**raw_config, "comparison_mode": "invalid_mode"})

    # Negative tolerance raises ValidationError
    with pytest.raises(ValidationError):
        AssignmentConfigV1.model_validate({**raw_config, "tolerance": -0.5})



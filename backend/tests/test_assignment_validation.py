import sys
from pathlib import Path
import pytest
from sqlalchemy.orm import Session

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base, import_domain_models  # noqa: E402
from app.db.seed import initialize_database  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.domains.assignments.models import Assignment, AssignmentConfig  # noqa: E402
from app.domains.assignments.validation import extract_ag_markers, run_preflight_validation  # noqa: E402
from app.domains.assignments.service import save_artifact, get_assignment_for_course  # noqa: E402


@pytest.fixture(autouse=True)
def db_session():
    import_domain_models()
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)
    with SessionLocal() as session:
        yield session
    Base.metadata.drop_all(bind=engine)
    initialize_database(seed=True)


@pytest.fixture(autouse=True)
def temp_artifact_storage(tmp_path, monkeypatch):
    from app.core.settings import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "artifact_storage_dir", str(tmp_path))
    yield tmp_path


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
    # config_json requires: add_numbers, reverse_words, count_vowels
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


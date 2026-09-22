from sqlalchemy.orm import Session

from app.domains.assignments.engine import AssignmentSpecificationEngine

_engine = AssignmentSpecificationEngine()


def extract_ag_markers(source_code: str) -> set[str]:
    """Parse python source code to find all pytest decorators starting with 'ag_'."""
    return _engine.extract_ag_markers(source_code)


def run_preflight_validation(db: Session, course_code: str, assignment_slug: str) -> list[str]:
    """Execute preflight checks on config_json and uploaded artifacts.

    Returns a list of validation error strings. If empty, validation passed.
    """
    return _engine.validate_specification(db, course_code, assignment_slug)

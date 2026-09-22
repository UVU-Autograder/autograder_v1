from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_domain_models() -> None:
    """Register all domain models with SQLAlchemy metadata."""

    import app.domains.assignments.models
    import app.domains.auth.models
    import app.domains.courses.models
    import app.domains.runs.models  # noqa: F401


from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.settings import get_settings


def _engine_kwargs(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        kwargs: dict = {
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,
            },
        }
        if ":memory:" in database_url:
            kwargs["poolclass"] = StaticPool
        return kwargs
    # Each API request holds a pooled connection for its whole life, and scheduling
    # needs one more while it holds the scheduler lock. SQLAlchemy's default (5 + 10
    # overflow, 30 s wait) ran out under a burst of uploads. Fail fast rather than
    # hold the scheduler lock for 30 s waiting for a connection.
    return {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 10, "pool_timeout": 10}


settings = get_settings()
engine = create_engine(settings.database_url, future=True, **_engine_kwargs(settings.database_url))

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

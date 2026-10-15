"""Cross-test isolation checks for the SQLite backup/restore reset_database fixture."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.domains.auth.models import User
from app.domains.courses.models import Course


def test_pollute_database_with_rows_ddl_and_hanging_session(db_session: Session) -> None:
    """Leave committed rows, injected DDL, and an unclosed session for the next test."""
    for i in range(50):
        db_session.add(User(email=f"adversarial_{i}@uvu.edu", display_name=f"Adv {i}"))
    course = db_session.scalar(select(Course).where(Course.code == "cs1400"))
    assert course is not None
    course.title = "HACKED_TITLE"
    db_session.commit()

    raw_conn = engine.raw_connection().dbapi_connection
    cur = raw_conn.cursor()
    cur.execute("CREATE TABLE injected_adversary_table (id INT, val TEXT)")
    cur.execute("INSERT INTO injected_adversary_table VALUES (999, 'injected')")
    raw_conn.commit()

    dirty_session = SessionLocal()
    dirty_session.add(User(email="hanging_user@uvu.edu", display_name="Hanging"))
    dirty_session.flush()
    cur = engine.raw_connection().dbapi_connection.cursor()
    cur.execute("SAVEPOINT sp_leak")
    cur.execute(
        "INSERT INTO users (email, display_name, is_active) VALUES ('sp_leak@uvu.edu', 'SP', 1)"
    )


def test_reset_clears_pollution_after_prior_test(db_session: Session) -> None:
    """Verify rows, DDL, and hanging-session writes from the prior test are gone."""
    assert (
        db_session.scalar(select(func.count(User.id)).where(User.email.like("adversarial_%")))
        == 0
    )
    assert db_session.scalar(select(func.count(User.id))) == 1
    course = db_session.scalar(select(Course).where(Course.code == "cs1400"))
    assert course is not None
    assert course.title == "Fundamentals of Programming"

    raw_conn = engine.raw_connection().dbapi_connection
    cur = raw_conn.cursor()
    cur.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='injected_adversary_table'"
    )
    assert cur.fetchone()[0] == 0
    assert db_session.scalar(select(User).where(User.email == "hanging_user@uvu.edu")) is None
    assert db_session.scalar(select(User).where(User.email == "sp_leak@uvu.edu")) is None


def test_drive_rowid_past_baseline(db_session: Session) -> None:
    for i in range(50):
        db_session.add(User(email=f"rowid_test_{i}@uvu.edu", display_name=f"Rowid {i}"))
    db_session.commit()
    max_id = db_session.scalar(select(func.max(User.id)))
    assert max_id is not None and max_id >= 51


def test_rowid_resets_after_prior_inserts(db_session: Session) -> None:
    fresh = User(email="fresh_after_rowid@uvu.edu", display_name="Fresh")
    db_session.add(fresh)
    db_session.commit()
    db_session.refresh(fresh)
    assert fresh.id == 2, f"RowID was not reset! Expected 2, got {fresh.id}"

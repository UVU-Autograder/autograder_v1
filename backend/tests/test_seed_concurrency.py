import time
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db import seed as seed_module
from app.db.base import Base
from app.domains.auth.models import User


def test_initialize_database_serializes_sqlite_seed(
    tmp_path,
    monkeypatch,
):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'seed.db'}",
        connect_args={"check_same_thread": False, "timeout": 2},
    )
    sessions = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    def slow_seed(db):
        user = db.scalar(
            select(User).where(User.email == "dev.staff@uvu.edu")
        )
        if user is None:
            time.sleep(0.1)
            db.add(User(email="dev.staff@uvu.edu"))
        db.commit()

    monkeypatch.setattr(seed_module, "engine", engine)
    monkeypatch.setattr(seed_module, "SessionLocal", sessions)
    monkeypatch.setattr(seed_module, "seed_development_data", slow_seed)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(seed_module.initialize_database, seed=True)
            for _ in range(2)
        ]
        for future in futures:
            future.result()

    with sessions() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1

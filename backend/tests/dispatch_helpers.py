from app.db.session import SessionLocal
from app.domains.runs import retention
from app.domains.runs.dispatcher import sweep
from app.domains.runs.models import OfficialDispatch, RunSummary
from app.domains.runs.tasks import grade_official_run


def register(run_id):
    with SessionLocal() as db:
        if not db.get(OfficialDispatch, run_id):
            db.add(OfficialDispatch(run_id=run_id, ready=True, attempts=0,
                next_attempt_at=retention.utc_now()))
            db.commit()


def drain(run_id):
    register(run_id)
    for _ in range(202):
        outgoing = []
        sweep(lambda *args: outgoing.append(args))
        for args in outgoing:
            result = grade_official_run(*args)
            if result["state"] in ("complete", "failure"):
                return result
        with SessionLocal() as db:
            run = db.get(RunSummary, run_id)
            if run.status in ("complete", "failure"):
                return {"run_id": run_id, "state": run.status}
    raise AssertionError("Dispatch failed to reach a terminal state")

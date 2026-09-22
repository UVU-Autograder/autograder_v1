"""Run with python -m app.domains.runs.cleanup_worker; no Celery/Redis dependency."""
from __future__ import annotations

import argparse
import signal
import threading

from app.core.audit_log import audit_event, configure_audit_logging
from app.db.base import import_domain_models
from app.db.session import SessionLocal
from app.domains.runs.retention import health, reconcile, write_heartbeat


def sweep() -> bool:
    counts: dict[str, int] = {}
    healthy = False
    try:
        with SessionLocal() as db:
            counts = reconcile(db)
        healthy = counts["error_count"] == 0
    except Exception:
        # Never print raw exceptions: filesystem errors can contain student paths.
        audit_event("official.cleanup_service_failed", failure_category="cleanup_service_unavailable")
    try:
        write_heartbeat(healthy=healthy, counts=counts)
    except OSError:
        healthy = False
        audit_event("official.cleanup_heartbeat_failed", failure_category="heartbeat_unavailable")
    return healthy


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--health", action="store_true")
    args = parser.parse_args()
    import_domain_models()
    configure_audit_logging()
    if args.health:
        try:
            with SessionLocal() as db:
                healthy = health(db)["cleanup_service_healthy"]
        except Exception:
            healthy = False
        raise SystemExit(0 if healthy else 1)
    if args.once:
        raise SystemExit(0 if sweep() else 1)
    stopped = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stopped.set())
    while not stopped.is_set():
        sweep()
        stopped.wait(60)


if __name__ == "__main__":
    main()

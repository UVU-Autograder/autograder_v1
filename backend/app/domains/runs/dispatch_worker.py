"""Dedicated bounded-dispatch service; cleanup remains independent of it."""
import json
import logging
import sys
import time

from app.core.audit_log import configure_audit_logging
from app.db.base import import_domain_models
from app.domains.runs import retention

import_domain_models()
configure_audit_logging()


def heartbeat(healthy: bool, counts: dict) -> None:
    path = retention.control_root() / "dispatcher.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"at": retention.utc_now().isoformat(),
        "healthy": healthy, **counts}), encoding="utf-8")
    temporary.replace(path)


def healthy() -> bool:
    from datetime import datetime
    try:
        payload = json.loads((retention.control_root() / "dispatcher.json").read_text(encoding="utf-8"))
        return payload["healthy"] and (retention.utc_now() - datetime.fromisoformat(payload["at"])).total_seconds() < 30
    except (OSError, ValueError, KeyError):
        return False


def main():
    from app.domains.runs.dispatcher import sweep
    if "--health" in sys.argv:
        raise SystemExit(0 if healthy() else 1)
    while True:
        try:
            counts = sweep()
            heartbeat(counts["publish_failures"] == 0, counts)
        except Exception:
            logging.error("Dispatch reconciliation unavailable")
            try:
                heartbeat(False, {})
            except OSError:
                pass
        time.sleep(5)


if __name__ == "__main__":
    main()

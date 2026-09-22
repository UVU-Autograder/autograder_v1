"""Quiesced rollout helper. Dry run by default; never deletes broker/status keys."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import redis
from app.core.settings import get_settings


def purge(client, *, apply: bool = False) -> int:
    count = 0
    for key in client.scan_iter(match="celery-task-meta-*", count=100):
        # SCAN may repeat a key; count only actual deletions on apply.
        count += int(client.delete(key)) if apply else 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-quiesced-exclusive-app-db", action="store_true")
    args = parser.parse_args()
    if args.apply and not args.confirm_quiesced_exclusive_app_db:
        parser.error("Stop intake/workers and confirm this Redis database belongs exclusively to this application.")
    client = redis.Redis.from_url(get_settings().redis_url)
    try:
        count = purge(client, apply=args.apply)
    except Exception:
        raise SystemExit("Result cleanup failed; inspect Redis health. No keys or payloads are printed.") from None
    print(f"Application task result records {'deleted' if args.apply else 'found'}: {count}")


if __name__ == "__main__":
    main()

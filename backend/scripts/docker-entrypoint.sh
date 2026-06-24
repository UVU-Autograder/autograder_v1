#!/bin/sh
set -eu

: "${DATABASE_URL:=}"

if [ -n "$DATABASE_URL" ]; then
  python - <<'PY'
import os
import time
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
deadline = time.time() + int(os.environ.get("DB_WAIT_TIMEOUT_SECONDS", "60"))
last_error = None
while time.time() < deadline:
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("select 1"))
        break
    except Exception as exc:  # pragma: no cover - startup path
        last_error = exc
        time.sleep(2)
else:
    raise SystemExit(f"database did not become ready: {last_error}")
PY

  if [ "${RUN_ALEMBIC_MIGRATIONS:-true}" = "true" ]; then
    alembic upgrade head
  fi

  if [ "${SEED_DATABASE:-false}" = "true" ]; then
    python -m app.db.seed
  fi
fi

exec "$@"

#!/usr/bin/env bash
# ==============================================================================
# UVU Autograder — Official Grading-Package Rollout & Worker Coordination (#23)
#
# Coordinates API (`backend`), `celery-worker`, `dispatch-worker`, and
# `cleanup-worker` updates from a single revision without version drift or
# dropped batches:
#   1. Drains queued/running official batches and active sandbox tickets
#      (never purges queues).
#   2. Captures a FERPA-compliant metadata backup prior to container rebuild.
#   3. Rebuilds and restarts `backend`, `celery-worker`, `dispatch-worker`, and
#      `cleanup-worker` simultaneously.
#   4. Executes `scripts/validate_grading_package_host.py` inside the deployed
#      `backend` container to verify synthetic package capture, isolated Judge0
#      execution, and immediate submission deletion.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COURSE="cs1410"
ASSIGNMENT="lab1"
DRAIN_TIMEOUT_SECONDS=600
POLL_INTERVAL_SECONDS=5
SKIP_BACKUP=0
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  --course <SLUG>         Synthetic course slug for post-rollout smoke check (default: cs1400)
  --assignment <SLUG>     Synthetic assignment slug for post-rollout smoke check (default: simple-python-functions)
  --timeout <SECONDS>     Maximum time to wait for queue drainage (default: 600)
  --skip-backup           Skip pre-rollout metadata backup
  --dry-run               Verify queue drainage and print planned commands without restarting containers
  -h, --help              Show this help message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --course)
      COURSE="${2:-}"
      shift 2
      ;;
    --assignment)
      ASSIGNMENT="${2:-}"
      shift 2
      ;;
    --timeout)
      DRAIN_TIMEOUT_SECONDS="${2:-600}"
      shift 2
      ;;
    --skip-backup)
      SKIP_BACKUP=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

COMPOSE_ENV_FILE="${REPO_ROOT}/.env.local"
if [[ ! -f "${COMPOSE_ENV_FILE}" ]]; then
  COMPOSE_ENV_FILE="${REPO_ROOT}/.env"
fi

DC=(docker compose)
if [[ -f "${COMPOSE_ENV_FILE}" ]]; then
  DC+=(--env-file "${COMPOSE_ENV_FILE}")
fi
DC+=(-f "${REPO_ROOT}/docker-compose.yml")
if [[ -f "${REPO_ROOT}/docker-compose.kata.yml" ]]; then
  DC+=(-f "${REPO_ROOT}/docker-compose.kata.yml")
fi

COMMIT_REV="$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
echo "=== UVU Autograder: Coordinated Grading-Package Rollout ==="
echo "Revision:   ${COMMIT_REV}"
echo "Target:     ${COURSE}/${ASSIGNMENT}"
echo "Drain cap:  ${DRAIN_TIMEOUT_SECONDS}s"

check_unfinished_workload() {
  "${DC[@]}" exec -T backend python -c '
import json
from sqlalchemy import func, select
from app.db.base import import_domain_models
from app.db.session import SessionLocal
from app.domains.runs import retention
from app.domains.runs.models import ExecutionTicket, RunSummary

import_domain_models()
with SessionLocal() as db:
    unfinished = db.scalar(
        select(func.count()).select_from(RunSummary).where(
            RunSummary.workflow_type == "official",
            RunSummary.status.in_(("queue", "run")),
        )
    ) or 0
    tickets = db.scalar(
        select(func.count()).select_from(ExecutionTicket).where(
            ExecutionTicket.state.in_(("waiting", "active")),
            ExecutionTicket.expires_at > retention.utc_now(),
        )
    ) or 0
print(f"{unfinished}:{tickets}")
'
}

echo "--> [1/4] Waiting for active official batches and execution tickets to drain..."
ELAPSED=0
while true; do
  COUNTS="$(check_unfinished_workload)"
  UNFINISHED="${COUNTS%%:*}"
  TICKETS="${COUNTS##*:}"
  if [[ "${UNFINISHED}" -eq 0 && "${TICKETS}" -eq 0 ]]; then
    echo "  Queues drained (unfinished_official=0, active_tickets=0)."
    break
  fi
  if [[ "${ELAPSED}" -ge "${DRAIN_TIMEOUT_SECONDS}" ]]; then
    echo "Error: Workload did not drain within ${DRAIN_TIMEOUT_SECONDS}s (unfinished_official=${UNFINISHED}, active_tickets=${TICKETS}). Aborting rollout without purging queues." >&2
    exit 1
  fi
  echo "  Draining: unfinished_official=${UNFINISHED}, active_tickets=${TICKETS} (${ELAPSED}s/${DRAIN_TIMEOUT_SECONDS}s)..."
  sleep "${POLL_INTERVAL_SECONDS}"
  ELAPSED=$((ELAPSED + POLL_INTERVAL_SECONDS))
done

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "--> [Dry Run] Queue drain verified. Planned rollout commands:"
  echo "  bash scripts/backup_metadata.sh --backup"
  echo "  ${DC[*]} up -d --build backend celery-worker dispatch-worker cleanup-worker"
  echo "  ${DC[*]} exec -T backend python scripts/validate_grading_package_host.py --course ${COURSE} --assignment ${ASSIGNMENT}"
  exit 0
fi

if [[ "${SKIP_BACKUP}" -eq 0 ]]; then
  echo "--> [2/4] Capturing pre-rollout persistent metadata backup..."
  bash "${SCRIPT_DIR}/backup_metadata.sh" --backup
else
  echo "--> [2/4] Skipping metadata backup (--skip-backup)."
fi

echo "--> [3/4] Rebuilding and restarting coordinated API and worker services..."
"${DC[@]}" up -d --build backend celery-worker dispatch-worker cleanup-worker

echo "  Waiting for API and worker health checks..."
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    break
  fi
  if [[ "${attempt}" -eq 30 ]]; then
    echo "Error: Backend API did not become healthy at http://127.0.0.1:8000/api/health" >&2
    exit 1
  fi
  sleep 2
done

"${DC[@]}" exec -T backend celery -A app.integrations.celery.app inspect ping >/dev/null
"${DC[@]}" exec -T dispatch-worker python -m app.domains.runs.dispatch_worker --health
"${DC[@]}" exec -T cleanup-worker python -m app.domains.runs.cleanup_worker --health
echo "  API, Celery worker, dispatch-worker, and cleanup-worker healthy on revision ${COMMIT_REV}."

echo "--> [4/4] Running synthetic grading-package host validation (${COURSE}/${ASSIGNMENT})..."
"${DC[@]}" exec -T backend python scripts/validate_grading_package_host.py \
  --course "${COURSE}" \
  --assignment "${ASSIGNMENT}"

echo "=== Coordinated Grading-Package Rollout Completed Successfully (${COMMIT_REV}) ==="

#!/usr/bin/env bash
# ==============================================================================
# UVU Autograder — Metadata & Course Configuration Backup Utility
# Scope: Persistent system and course configurations only.
# FERPA Compliance: STRICTLY EXCLUDES runs, student submissions, and workspaces.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${REPO_ROOT}/backups/metadata_${TIMESTAMP}"
COMPOSE_ENV_FILE="${REPO_ROOT}/.env.local"

if [ ! -f "${COMPOSE_ENV_FILE}" ]; then
  COMPOSE_ENV_FILE="${REPO_ROOT}/.env"
fi

DC=(docker compose)
if [ -f "${COMPOSE_ENV_FILE}" ]; then
  DC+=(--env-file "${COMPOSE_ENV_FILE}")
fi

usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --backup              Perform a metadata backup (default action)"
  echo "  --restore <DIR>       Restore metadata from specified backup directory"
  echo "  --output-dir <DIR>    Custom directory to store backup (default: backups/metadata_<timestamp>)"
  echo "  -h, --help            Show this help message"
  exit 1
}

# Explicitly allowed persistent metadata tables (FERPA boundary)
METADATA_TABLES=(
  "roles"
  "users"
  "staff_access"
  "courses"
  "sections"
  "modules"
  "assignments"
  "assignment_configs"
  "assignment_artifacts"
  "alembic_version"
)

do_backup() {
  echo "=== UVU Autograder: Initiating Persistent Metadata Backup ==="
  echo "Timestamp: ${TIMESTAMP}"
  echo "Target directory: ${BACKUP_DIR}"
  mkdir -p "${BACKUP_DIR}"

  # 1. PostgreSQL Schema & Metadata Dump
  echo "--> Dumping persistent database tables (excluding student submission data)..."
  PG_TABLE_ARGS=()
  for tbl in "${METADATA_TABLES[@]}"; do
    PG_TABLE_ARGS+=("-t" "${tbl}")
  done

  # Execute pg_dump inside the postgres container
  "${DC[@]}" exec -T postgres pg_dump -U autograder -d autograder \
    --data-only \
    --inserts \
    "${PG_TABLE_ARGS[@]}" > "${BACKUP_DIR}/metadata_data.sql"

  # Dump schema structure for metadata tables
  "${DC[@]}" exec -T postgres pg_dump -U autograder -d autograder \
    --schema-only \
    "${PG_TABLE_ARGS[@]}" > "${BACKUP_DIR}/metadata_schema.sql"

  echo "  Database dump complete: metadata_data.sql"

  # 2. Archive Assignment Test Artifacts (Instructor-owned only)
  echo "--> Archiving instructor assignment artifacts..."
  ARTIFACT_SRC="${REPO_ROOT}/data/artifacts"
  if [ -d "${ARTIFACT_SRC}" ]; then
    tar -czf "${BACKUP_DIR}/artifacts.tar.gz" -C "${REPO_ROOT}/data" artifacts
    echo "  Artifact archive complete: artifacts.tar.gz"
  else
    echo "  Notice: ${ARTIFACT_SRC} not found. Skipping artifact archive."
  fi

  # 3. Create Manifest
  COMMIT_HASH="$(git rev-parse HEAD 2>/dev/null || echo "unknown")"
  cat > "${BACKUP_DIR}/manifest.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "git_commit": "${COMMIT_HASH}",
  "backup_scope": "metadata_only",
  "ferpa_compliant": true,
  "tables": [$(printf '"%s",' "${METADATA_TABLES[@]}" | sed 's/,$//')],
  "excluded_entities": ["runs", "student_submissions", "execution_logs", "workspaces", "broker_payloads"]
}
EOF

  echo "=== Backup Completed Successfully ==="
  echo "Location: ${BACKUP_DIR}"
}

do_restore() {
  local RESTORE_DIR="$1"
  if [ ! -d "${RESTORE_DIR}" ]; then
    echo "Error: Restore directory '${RESTORE_DIR}' does not exist." >&2
    exit 1
  fi

  if [ ! -f "${RESTORE_DIR}/manifest.json" ] || [ ! -f "${RESTORE_DIR}/metadata_data.sql" ]; then
    echo "Error: Directory '${RESTORE_DIR}' is not a valid autograder metadata backup." >&2
    exit 1
  fi

  echo "=== UVU Autograder: Restoring Metadata from '${RESTORE_DIR}' ==="
  read -p "Warning: This will insert backed up metadata into the current database. Proceed? (y/N): " -r CONFIRM
  if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
    echo "Restore aborted by operator."
    exit 0
  fi

  echo "--> Restoring database metadata..."
  "${DC[@]}" exec -T postgres psql -U autograder -d autograder < "${RESTORE_DIR}/metadata_data.sql"

  if [ -f "${RESTORE_DIR}/artifacts.tar.gz" ]; then
    echo "--> Restoring assignment artifacts..."
    mkdir -p "${REPO_ROOT}/data"
    tar -xzf "${RESTORE_DIR}/artifacts.tar.gz" -C "${REPO_ROOT}/data"
  fi

  echo "=== Metadata Restore Complete ==="
}

ACTION="backup"
RESTORE_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backup)
      ACTION="backup"
      shift
      ;;
    --restore)
      ACTION="restore"
      RESTORE_PATH="${2:-}"
      if [ -z "${RESTORE_PATH}" ]; then usage; fi
      shift 2
      ;;
    --output-dir)
      BACKUP_DIR="${2:-}"
      if [ -z "${BACKUP_DIR}" ]; then usage; fi
      shift 2
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

if [ "${ACTION}" = "backup" ]; then
  do_backup
elif [ "${ACTION}" = "restore" ]; then
  do_restore "${RESTORE_PATH}"
fi

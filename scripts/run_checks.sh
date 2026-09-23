#!/usr/bin/env bash
# UVU Autograder - Unified Quality & Verification Checks (Bash / CI)
# Usage: ./scripts/run_checks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Running UVU Autograder Quality Checks ==="
echo "Repository root: ${REPO_ROOT}"
echo ""

# 1. Determine Python executable
if [ -f "${REPO_ROOT}/backend/venv/bin/python" ]; then
    PYTHON="${REPO_ROOT}/backend/venv/bin/python"
elif [ -f "${REPO_ROOT}/backend/venv/Scripts/python.exe" ]; then
    PYTHON="${REPO_ROOT}/backend/venv/Scripts/python.exe"
else
    PYTHON="python3"
fi

# 2. Backend Linting (Ruff)
echo "--> [1/6] Backend Linting (ruff)..."
(
    cd "${REPO_ROOT}/backend"
    "${PYTHON}" -m ruff check app tests
)
echo "  Ruff check passed."
echo ""

# 3. Backend Unit Tests
echo "--> [2/6] Backend Unit Tests (pytest)..."
(
    cd "${REPO_ROOT}/backend"
    "${PYTHON}" -m pytest tests/unit -q
)
echo "  Backend unit tests passed."
echo ""

# 4. Database Schema Drift Check
echo "--> [3/6] Database Schema Drift Check (alembic check)..."
(
    cd "${REPO_ROOT}/backend"
    TEMP_DB="${REPO_ROOT}/backend/check_drift_tmp.db"
    rm -f "${TEMP_DB}"
    trap 'rm -f "${TEMP_DB}"' EXIT
    DATABASE_URL="sqlite+pysqlite:///${TEMP_DB}" "${PYTHON}" -m alembic upgrade head >/dev/null
    DATABASE_URL="sqlite+pysqlite:///${TEMP_DB}" "${PYTHON}" -m alembic check
)
echo "  Schema drift check passed (0 drift)."
echo ""

# 5. Frontend Type Check
echo "--> [4/6] Frontend Type Check (tsc)..."
(
    cd "${REPO_ROOT}/frontend"
    npm run type-check
)
echo "  TypeScript check passed."
echo ""

# 6. Frontend Linting (ESLint)
echo "--> [5/6] Frontend Linting (eslint)..."
(
    cd "${REPO_ROOT}/frontend"
    npm run lint
)
echo "  ESLint check passed."
echo ""

# 7. Frontend Tests (Vitest)
echo "--> [6/6] Frontend Unit Tests (vitest)..."
(
    cd "${REPO_ROOT}/frontend"
    npm run test
)
echo "  Frontend tests passed."
echo ""

echo "=== All Quality Checks Passed Successfully! ==="

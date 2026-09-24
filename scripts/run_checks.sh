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
echo "--> [1/7] Backend Linting (ruff)..."
(
    cd "${REPO_ROOT}/backend"
    "${PYTHON}" -m ruff check app tests
)
echo "  Ruff check passed."
echo ""

# 3. Backend Type Check (mypy)
echo "--> [2/7] Backend Type Checking (mypy)..."
(
    cd "${REPO_ROOT}"
    "${PYTHON}" -m mypy backend/app
)
echo "  Mypy check passed."
echo ""

# 4. Backend Tests
echo "--> [3/7] Backend Tests (pytest)..."
(
    cd "${REPO_ROOT}/backend"
    "${PYTHON}" -m pytest tests -q
)
echo "  Backend tests passed."
echo ""

# 5. Database Schema Drift Check
echo "--> [4/7] Database Schema Drift Check (alembic check)..."
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

# 6. Frontend Type Check
echo "--> [5/7] Frontend Type Check (tsc)..."
(
    cd "${REPO_ROOT}/frontend"
    npm run type-check
)
echo "  TypeScript check passed."
echo ""

# 7. Frontend Linting (ESLint)
echo "--> [6/7] Frontend Linting (eslint)..."
(
    cd "${REPO_ROOT}/frontend"
    npm run lint
)
echo "  ESLint check passed."
echo ""

# 8. Frontend Tests (Vitest)
echo "--> [7/7] Frontend Unit Tests (vitest)..."
(
    cd "${REPO_ROOT}/frontend"
    npm run test
)
echo "  Frontend tests passed."
echo ""

echo "=== All Quality Checks Passed Successfully! ==="

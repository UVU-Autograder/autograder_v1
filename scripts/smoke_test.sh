#!/usr/bin/env bash
# smoke_test.sh — quick deployment health check for the UVU Autograder workstation
# Usage: ./scripts/smoke_test.sh [host]
# Default host: 127.0.0.1 (run on the workstation itself)
set -euo pipefail

HOST="${1:-127.0.0.1}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

check() {
  local label="$1" url="$2" expect="$3"
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || true)
  status="${status:-000}"
  status="${status:0:3}"
  if [ "$status" = "$expect" ]; then
    echo "  ✓ ${label}: HTTP ${status}"
    PASS=$((PASS + 1))
  else
    echo "  ✗ ${label}: HTTP ${status} (expected ${expect})"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== UVU Autograder Smoke Test ==="
echo "Host: ${HOST}"
echo ""

# --- Backend API & Reverse Proxy ---
echo "[Backend API & Reverse Proxy]"
if [ "$HOST" = "127.0.0.1" ] || [ "$HOST" = "localhost" ]; then
  check "Health endpoint (Direct :8000)" "http://${HOST}:8000/health" "200"
else
  check "Direct :8000 loopback isolation (refused)" "http://${HOST}:8000/health" "000"
fi
check "Health probe (via Nginx)" "http://${HOST}/health" "200"
check "API prefix rewrite (/api/health)" "http://${HOST}/api/health" "200"

# --- Frontend ---
echo "[Frontend]"
check "Sandbox page" "http://${HOST}/sandbox" "200"
check "Login redirect" "http://${HOST}/staff/login" "200"

# --- Execution Engine (Judge0) ---
echo "[Execution Engine (Judge0)]"
if [ "$HOST" = "127.0.0.1" ] || [ "$HOST" = "localhost" ]; then
  check "Judge0 language runtime (:2358)" "http://${HOST}:2358/languages" "200"
else
  check "Direct :2358 loopback isolation (refused)" "http://${HOST}:2358/languages" "000"
fi

# --- Local AI Feedback Service (vLLM) ---
echo "[Local AI Feedback Service (vLLM)]"
if [ "$HOST" = "127.0.0.1" ] || [ "$HOST" = "localhost" ]; then
  check "vLLM model server (:8001)" "http://${HOST}:8001/v1/models" "200"
else
  check "Direct :8001 loopback isolation (refused)" "http://${HOST}:8001/v1/models" "000"
fi

# --- Docker services ---
if [ "$HOST" = "127.0.0.1" ] || [ "$HOST" = "localhost" ]; then
  echo "[Docker Services]"
  if command -v docker &>/dev/null; then
    unhealthy=$(docker compose -f "${REPO_ROOT}/docker-compose.yml" ps 2>/dev/null | grep -cE "Restarting|unhealthy|Exited \([1-9]" || true)
    unhealthy=$(echo "$unhealthy" | tr -d '[:space:]')
    total=$(docker compose -f "${REPO_ROOT}/docker-compose.yml" ps -q 2>/dev/null | wc -l || echo 0)
    total=$(echo "$total" | tr -d '[:space:]')
    if [ "${total:-0}" -eq 0 ]; then
      echo "  ✗ Docker services are stopped (0 containers running)"
      FAIL=$((FAIL + 1))
    elif [ "${unhealthy:-0}" -eq 0 ]; then
      echo "  ✓ All ${total} containers healthy"
      PASS=$((PASS + 1))
    else
      echo "  ✗ ${unhealthy} container(s) unhealthy or restarting"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "  - Docker not available (skipped)"
  fi
fi

# --- Summary ---
echo ""
TOTAL=$((PASS + FAIL))
echo "Result: ${PASS}/${TOTAL} checks passed"
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi

#!/usr/bin/env bash
# ==============================================================================
# UVU Autograder — Docker Compose CLI Wrapper
# Location: scripts/dc.sh
# Purpose: Enforces Kata Containers microVM runtime overlay on every invocation.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${SCRIPT_DIR}"

ENV_FILE=".env"
if [[ -f ".env.local" ]]; then
  ENV_FILE=".env.local"
fi

exec docker compose --env-file "${ENV_FILE}" -f docker-compose.yml -f docker-compose.kata.yml "$@"

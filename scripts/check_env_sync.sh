#!/usr/bin/env bash
# check_env_sync.sh — verify .env has every variable from .env.example
# Usage: ./scripts/check_env_sync.sh [path/to/.env]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="${REPO_ROOT}/.env.example"
ACTIVE="${1:-${REPO_ROOT}/.env}"

if [ ! -f "$EXAMPLE" ]; then
  echo "ERROR: .env.example not found at ${EXAMPLE}" >&2
  exit 1
fi
if [ ! -f "$ACTIVE" ]; then
  echo "ERROR: .env file not found at ${ACTIVE}" >&2
  echo "  Copy .env.example to .env and fill in secrets before deploying." >&2
  exit 1
fi

errors=0

# Extract variable names (skip comments and blank lines)
example_vars=$( (grep -E '^[A-Z_][A-Z0-9_]*=' "$EXAMPLE" || true) | cut -d= -f1 | sort -u)
active_vars=$( (grep -E '^[A-Z_][A-Z0-9_]*=' "$ACTIVE" || true) | cut -d= -f1 | sort -u)

# Check for missing variables
missing=$(comm -23 <(echo "$example_vars") <(echo "$active_vars"))
if [ -n "$missing" ]; then
  echo "MISSING from ${ACTIVE} (present in .env.example):"
  echo "$missing" | sed 's/^/  - /'
  errors=$((errors + $(echo "$missing" | wc -l)))
fi

# Check for placeholder values that should be changed
while IFS='=' read -r key value; do
  clean_val=$(echo "$value" | sed -e 's/^[[:space:]"'\''"]*//' -e 's/[[:space:]"'\''"]*$//')
  if [[ "$clean_val" == *"change-me"* ]] || [[ "$clean_val" == *"replace-with"* ]]; then
    echo "PLACEHOLDER: ${key}=${value} (needs a real value)"
    errors=$((errors + 1))
  fi
done < <(grep -E '^[A-Z_][A-Z0-9_]*=' "$ACTIVE" || true)

if [ "$errors" -eq 0 ]; then
  echo "OK: .env is in sync with .env.example ($(echo "$active_vars" | wc -l) variables checked)"
else
  echo ""
  echo "FAILED: ${errors} issue(s) found"
  exit 1
fi

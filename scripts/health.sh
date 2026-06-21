#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env.server}"

need curl

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
FRONTEND_PUBLIC_URL="${FRONTEND_PUBLIC_URL:-http://localhost:${FRONTEND_PORT}}"
API_BASE="${API_BASE:-${VITE_API_BASE:-http://127.0.0.1:${BACKEND_PORT}}}"
API_BASE="${API_BASE%/}"
FRONTEND_PUBLIC_URL="${FRONTEND_PUBLIC_URL%/}"
TIMEOUT="${HEALTH_TIMEOUT:-8}"

failures=0

check_url() {
  local name="$1"
  local url="$2"
  local code
  code="$(curl -L -sS -o /dev/null -w '%{http_code}' --max-time "$TIMEOUT" "$url" || true)"
  if [[ "$code" =~ ^2|3 ]]; then
    printf 'OK   %-28s %s (%s)\n' "$name" "$url" "$code"
  else
    printf 'FAIL %-28s %s (%s)\n' "$name" "$url" "${code:-curl-error}"
    failures=$((failures + 1))
  fi
}

check_cors() {
  local name="$1"
  local url="$2"
  local origin="$3"
  local headers
  headers="$(curl -sS -D - -o /dev/null --max-time "$TIMEOUT" -H "Origin: ${origin}" "$url" || true)"
  if echo "$headers" | grep -qi "access-control-allow-origin"; then
    printf 'OK   %-28s %s (origin %s)\n' "$name" "$url" "$origin"
  else
    printf 'FAIL %-28s %s (missing access-control-allow-origin for %s)\n' "$name" "$url" "$origin"
    failures=$((failures + 1))
  fi
}

echo "Personal Invest health check"
echo "frontend: ${FRONTEND_PUBLIC_URL}"
echo "api:      ${API_BASE}"
echo

check_url "frontend page" "$FRONTEND_PUBLIC_URL"
check_url "frontend config" "$FRONTEND_PUBLIC_URL/config.js"
check_url "backend health" "$API_BASE/health"
check_url "backend cors health" "$API_BASE/health/cors"
check_url "dashboard api" "$API_BASE/api/dashboard"
check_url "data credibility api" "$API_BASE/api/data/credibility"
check_cors "cors header" "$API_BASE/health/cors" "$FRONTEND_PUBLIC_URL"

echo
if [ "$failures" -eq 0 ]; then
  echo "health: OK"
else
  echo "health: ${failures} failure(s)"
  exit 1
fi

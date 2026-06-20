#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
FRONTEND_PUBLIC_URL="${FRONTEND_PUBLIC_URL:-http://localhost:${FRONTEND_PORT}}"
VITE_API_BASE="${VITE_API_BASE:-}"
FRONTEND_ALLOWED_HOSTS="${FRONTEND_ALLOWED_HOSTS:-localhost,127.0.0.1}"
BACKEND_CORS_ORIGINS="${BACKEND_CORS_ORIGINS:-http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}}"
VITE_PROXY_TARGET="${VITE_PROXY_TARGET:-http://127.0.0.1:${BACKEND_PORT}}"

host_from_url() {
  python3 - "$1" <<'PY'
from urllib.parse import urlparse
import sys
url = sys.argv[1]
print(urlparse(url).hostname or "")
PY
}

contains_csv() {
  local csv="$1"
  local target="$2"
  IFS=',' read -ra items <<< "$csv"
  for item in "${items[@]}"; do
    item="$(echo "$item" | xargs)"
    if [ "$item" = "$target" ]; then
      return 0
    fi
  done
  return 1
}

print_cmd() {
  local name="$1"
  local cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  $name: $($cmd --version 2>/dev/null | head -n 1)"
  else
    echo "  $name: missing"
  fi
}

frontend_host="$(host_from_url "$FRONTEND_PUBLIC_URL")"
issues=0

echo "Personal Invest doctor"
echo "env file: ${ENV_FILE:-.env}"
echo

echo "runtime:"
print_cmd "uv" "uv"
print_cmd "node" "node"
print_cmd "pnpm" "pnpm"
echo

echo "backend:"
echo "  listen: ${BACKEND_HOST}:${BACKEND_PORT}"
echo "  cors:   ${BACKEND_CORS_ORIGINS}"
echo

echo "frontend:"
echo "  listen:        ${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "  public url:    ${FRONTEND_PUBLIC_URL}"
echo "  allowed hosts: ${FRONTEND_ALLOWED_HOSTS}"
echo

echo "api mode:"
if [ -n "$VITE_API_BASE" ]; then
  echo "  direct api: ${VITE_API_BASE}"
else
  echo "  same-origin proxy: /api -> ${VITE_PROXY_TARGET}"
fi
echo

if [ -n "$frontend_host" ]; then
  if ! contains_csv "$FRONTEND_ALLOWED_HOSTS" "$frontend_host" && [ "$FRONTEND_ALLOWED_HOSTS" != "*" ]; then
    echo "WARN: FRONTEND_ALLOWED_HOSTS does not include ${frontend_host}"
    issues=$((issues + 1))
  fi
fi

if [ -n "$VITE_API_BASE" ]; then
  if ! contains_csv "$BACKEND_CORS_ORIGINS" "$FRONTEND_PUBLIC_URL"; then
    echo "WARN: BACKEND_CORS_ORIGINS does not include ${FRONTEND_PUBLIC_URL}"
    issues=$((issues + 1))
  fi
fi

if [ "$issues" -eq 0 ]; then
  echo "doctor: OK"
else
  echo "doctor: ${issues} warning(s)"
fi

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

source "$ROOT_DIR/scripts/lib.sh"
load_env_file "${ENV_FILE:-.env}"

ensure_python_runtime

export PYTHONPATH="$ROOT_DIR/backend${PYTHONPATH:+:$PYTHONPATH}"
export BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
export BACKEND_PORT="${BACKEND_PORT:-8000}"
export UVICORN_WORKERS="${UVICORN_WORKERS:-1}"

if [ "${1:-}" = "--check" ]; then
  python_bin="$(python_runtime_bin)"
  echo "python: $python_bin"
  "$python_bin" - <<'PYCODE'
import importlib.util
import sys
for module in ("fastapi", "uvicorn"):
    if importlib.util.find_spec(module) is None:
        raise SystemExit(f"missing python module: {module}")
print("backend runtime ok")
print(sys.version.split()[0])
PYCODE
  exit 0
fi

run_python -m uvicorn app.main:app \
  --app-dir backend \
  --host "$BACKEND_HOST" \
  --port "$BACKEND_PORT" \
  --workers "$UVICORN_WORKERS"

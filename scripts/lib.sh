#!/usr/bin/env bash

# systemd services do not read interactive shell profiles, so tools installed by
# uv's installer or Node/Corepack may otherwise be invisible at runtime.
export PATH="${PATH:-/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin}"
USER_HOME="${HOME:-}"
for candidate in \
  "${USER_HOME:+$USER_HOME/.local/bin}" \
  "${USER_HOME:+$USER_HOME/.cargo/bin}" \
  "/root/.local/bin" \
  "/root/.cargo/bin" \
  "/usr/local/bin"; do
  if [ -z "$candidate" ]; then
    continue
  fi
  if [ -d "$candidate" ]; then
    case ":$PATH:" in
      *":$candidate:"*) ;;
      *) PATH="$candidate:$PATH" ;;
    esac
  fi
done
export PATH

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "缺少命令：$1"
    echo "请先安装 $1 后重试。"
    exit 1
  fi
}

ensure_uv() {
  need uv
}

python_runtime_bin() {
  local candidate="${PYTHON_RUNTIME_BIN:-}"
  if [ -n "$candidate" ]; then
    if [ -x "$candidate" ]; then
      printf '%s
' "$candidate"
      return 0
    fi
    echo "PYTHON_RUNTIME_BIN 不可执行：$candidate" >&2
    return 1
  fi

  candidate="${VENV_DIR:-.venv}/bin/python"
  if [ -x "$candidate" ]; then
    printf '%s
' "$candidate"
    return 0
  fi

  if [ -x ".venv/bin/python" ]; then
    printf '%s
' ".venv/bin/python"
    return 0
  fi

  return 1
}

ensure_python_runtime() {
  if ! python_runtime_bin >/dev/null; then
    echo "缺少生产 Python 运行时：.venv/bin/python"
    echo "请先在项目根目录执行：uv sync"
    echo "或设置 PYTHON_RUNTIME_BIN 指向可执行 Python。"
    exit 1
  fi
}

run_python() {
  local python_bin
  python_bin="$(python_runtime_bin)" || {
    echo "缺少生产 Python 运行时：.venv/bin/python"
    echo "请先在项目根目录执行：uv sync"
    exit 1
  }
  "$python_bin" "$@"
}

ensure_pnpm_latest() {
  export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
  local version="${PNPM_VERSION:-latest}"

  if command -v corepack >/dev/null 2>&1; then
    corepack enable >/dev/null 2>&1 || true
    corepack prepare "pnpm@${version}" --activate >/dev/null
  fi

  if ! command -v pnpm >/dev/null 2>&1; then
    echo "缺少命令：pnpm"
    echo "推荐安装 Node.js 20+ 后执行：corepack enable && corepack prepare pnpm@latest --activate"
    exit 1
  fi

  echo "pnpm: $(pnpm --version)"
}

load_env_file() {
  local file="${1:-.env}"
  if [ -f "$file" ]; then
    echo "loading env: $file"
    set -a
    # shellcheck disable=SC1090
    source "$file"
    set +a
  fi
}

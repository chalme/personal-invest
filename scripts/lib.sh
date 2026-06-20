#!/usr/bin/env bash

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

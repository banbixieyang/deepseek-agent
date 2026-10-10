#!/usr/bin/env bash
# ds-agent 一键启动（Linux / macOS）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
else
  PY="${PYTHON:-python3}"
fi

export PYTHONPATH="$ROOT/src:${PYTHONPATH:-}"

exec "$PY" -m ds_agent.launcher "$@"

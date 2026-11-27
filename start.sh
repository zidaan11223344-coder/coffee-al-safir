#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD="$PYTHON_BIN"
elif command -v python3.13 >/dev/null 2>&1; then
  PYTHON_CMD="python3.13"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "[START][FATAL] Python 3.13/3 not found in PATH." >&2
  exit 2
fi

echo "[START] Python: $("$PYTHON_CMD" --version 2>&1)"
NODE_PATH=""
if NODE_OUTPUT="$("$PYTHON_CMD" node_runtime_bootstrap.py)"; then
  printf '%s\n' "$NODE_OUTPUT" | sed '$d'
  NODE_PATH="$(printf '%s\n' "$NODE_OUTPUT" | tail -n 1)"
else
  echo "[START][WARN] Node.js 22 bootstrap failed; continuing with the existing Python music fallbacks." >&2
fi

if [[ -n "$NODE_PATH" && -x "$NODE_PATH" ]]; then
  export NODE_BINARY="$NODE_PATH"
  export PATH="$(dirname "$NODE_PATH"):$PATH"
  echo "[START] Node: $("$NODE_BINARY" --version)"
else
  unset NODE_BINARY || true
  echo "[START][WARN] No Node.js 22 runtime; YouTube EJS may be unavailable, but the TalkinChat bot will still start." >&2
fi

echo "[START] Starting TalkinChat with PY_FILE=${PY_FILE:-bot.py}"
exec "$PYTHON_CMD" "${PY_FILE:-bot.py}"

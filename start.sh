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

  # YouTube may require per-video Proof-of-Origin tokens. Start the official
  # bgutil provider locally; its yt-dlp plugin discovers 127.0.0.1:4416.
  if [[ "${YOUTUBE_POT_PROVIDER:-1}" == "1" ]]; then
    POT_DIR="${YOUTUBE_POT_PROVIDER_DIR:-${HOME:-/tmp}/.cache/bgutil-ytdlp-pot-provider-2.0.2}"
    POT_PID=""
    if [[ ! -f "$POT_DIR/server/build/main.js" ]]; then
      mkdir -p "$(dirname "$POT_DIR")"
      if [[ ! -d "$POT_DIR/.git" ]]; then
        rm -rf "$POT_DIR"
        git clone --depth 1 --branch 2.0.2 \
          https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git "$POT_DIR" || true
      fi
      if [[ -d "$POT_DIR/server" ]]; then
        (cd "$POT_DIR/server" && npm ci --no-audit --no-fund && npx tsc) || true
      fi
    fi
    if [[ -f "$POT_DIR/server/build/main.js" ]]; then
      "$NODE_BINARY" "$POT_DIR/server/build/main.js" --host 127.0.0.1 --port 4416 \
        >"${POT_DIR}/provider.log" 2>&1 &
      POT_PID=$!
      export YOUTUBE_POT_BASE_URL="${YOUTUBE_POT_BASE_URL:-http://127.0.0.1:4416}"
      echo "[START] YouTube PO Token provider: $YOUTUBE_POT_BASE_URL (pid=$POT_PID)"
    else
      echo "[START][WARN] Could not build bgutil PO Token provider; protected YouTube formats may fail." >&2
    fi
    cleanup_pot() { [[ -n "${POT_PID:-}" ]] && kill "$POT_PID" 2>/dev/null || true; }
    trap cleanup_pot EXIT
  fi
else
  unset NODE_BINARY || true
  echo "[START][WARN] No Node.js 22 runtime; YouTube EJS may be unavailable, but the TalkinChat bot will still start." >&2
fi

echo "[START] Starting TalkinChat with PY_FILE=${PY_FILE:-bot.py}"
exec "$PYTHON_CMD" "${PY_FILE:-bot.py}"

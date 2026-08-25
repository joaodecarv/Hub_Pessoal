#!/usr/bin/env bash
#
# start.sh — launch the whole Personal AI + Finance Hub with one command.
#
# Starts both modules and streams their logs into this one terminal:
#   • Backend  — FastAPI/Uvicorn on http://localhost:8000  (docs at /docs)
#   • Frontend — React/Vite     on http://localhost:5173
#
# Press Ctrl+C once to stop both cleanly.
#
# Usage:
#   ./start.sh            # start backend + frontend
#   ./start.sh backend    # start only the backend
#   ./start.sh frontend   # start only the frontend
#

set -euo pipefail

# Project root = the folder this script lives in (works from anywhere).
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

# Small helpers so the two log streams are easy to tell apart.
log()  { printf '\033[1;36m[hub]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[hub] error:\033[0m %s\n' "$*" >&2; exit 1; }

# --- sanity checks ----------------------------------------------------------
[ -x "$BACKEND/.venv/bin/uvicorn" ] || fail "backend venv not found — run: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
[ -d "$FRONTEND/node_modules" ]     || fail "frontend deps not installed — run: cd frontend && npm install"

# Track child PIDs so we can shut everything down together.
PIDS=()

_cleaned=0
cleanup() {
  [ "$_cleaned" = 1 ] && return   # trap can fire on both TERM and EXIT
  _cleaned=1
  log "shutting down..."
  for pid in "${PIDS[@]:-}"; do
    # Kill the whole process group (Uvicorn --reload / Vite spawn children).
    kill -- -"$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  log "stopped."
}
trap cleanup INT TERM EXIT

start_backend() {
  log "starting backend  → http://localhost:8000  (docs: /docs)"
  ( cd "$BACKEND" && exec .venv/bin/uvicorn app.main:app --reload --port 8000 ) &
  PIDS+=("$!")
}

start_frontend() {
  log "starting frontend → http://localhost:5173"
  # Frontend uses Node via nvm (no venv); load nvm so `npm`/`node` resolve.
  (
    cd "$FRONTEND"
    export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
    if [ -s "$NVM_DIR/nvm.sh" ]; then
      # nvm scripts trip `set -u`/`set -e`; relax inside this subshell only.
      set +eu
      \. "$NVM_DIR/nvm.sh"
      nvm use default >/dev/null 2>&1 || true
    fi
    exec npm run dev
  ) &
  PIDS+=("$!")
}

# Run children in their own process groups so cleanup can take their kids too.
set -m

case "${1:-all}" in
  backend)  start_backend ;;
  frontend) start_frontend ;;
  all)      start_backend; start_frontend ;;
  *)        fail "unknown argument '$1' — use: backend | frontend | (nothing for both)" ;;
esac

log "running — press Ctrl+C to stop both."
# Wait for any child to exit; cleanup trap handles the rest.
wait

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8000}"

cd "$ROOT_DIR/frontend"

echo "[run_local_frontend] Proxying /api to http://localhost:$API_PORT"

VITE_PROXY_TARGET="http://localhost:$API_PORT" npm run dev -- --host 0.0.0.0 --port 5173

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${AI_HUB_DB_PATH:-$ROOT_DIR/backend/.local/daily_digest.db}"
APP_PORT="${APP_PORT:-8000}"

cd "$ROOT_DIR"

export DATABASE_URL="sqlite:////$DB_PATH"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000}"
export ENVIRONMENT="${ENVIRONMENT:-development}"
export SECRET_KEY="${SECRET_KEY:-local-dev-secret}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"

echo "[run_local_backend] Using database: $DATABASE_URL"
echo "[run_local_backend] Starting API on port $APP_PORT"

exec ./.venv/bin/python -m uvicorn backend.app.main:app --host 0.0.0.0 --port "$APP_PORT"

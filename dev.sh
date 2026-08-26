#!/usr/bin/env bash
# One-command local dev startup: backend stack (Docker Compose) + frontend
# dev server. Run this, wait for the URL, open it in a browser — Ctrl+C
# stops the frontend; the backend containers keep running in the background
# (they're slow to cold-start, especially stt/tts) so the next run is fast.
#
# Usage: ./dev.sh [--build]
#   --build   rebuild the API image first (after changing Dockerfile,
#             pyproject.toml, or uv.lock)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

if [ ! -f .env ]; then
  echo "No .env found — copying .env.example to .env."
  cp .env.example .env
  echo "Edit .env (at least JWT_SECRET_KEY and POSTGRES_PASSWORD) and run this again."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker isn't running (or isn't reachable) — start Docker Desktop and try again."
  exit 1
fi

if [ "${1:-}" = "--build" ]; then
  echo "Building the API image..."
  docker compose build api
fi

echo "Starting backend (db, redis, stt, tts, api)..."
docker compose up -d

echo -n "Waiting for the API to be ready"
for _ in $(seq 1 60); do
  if curl -s -o /dev/null -w "" http://localhost:"${API_PORT:-8000}"/health 2>/dev/null; then
    echo " ready."
    break
  fi
  echo -n "."
  sleep 1
done

if ! curl -s -o /dev/null http://localhost:"${API_PORT:-8000}"/health 2>/dev/null; then
  echo
  echo "API didn't come up in time — check the logs: docker compose logs api"
  exit 1
fi

if [ ! -d frontend/node_modules ]; then
  echo "Installing frontend dependencies (first run only)..."
  (cd frontend && npm install)
fi

echo
echo "Backend:  http://localhost:${API_PORT:-8000} (docs at /docs)"
echo "Frontend: http://localhost:5173 (starting now — open it once Vite says 'ready')"
echo "Ctrl+C stops the frontend; the backend keeps running for next time."
echo "  (docker compose down   — to stop everything)"
echo

cd frontend
# No --host flag: Vite then prints and binds "localhost", matching the
# API's CORS_ORIGINS exactly. Passing --host 127.0.0.1 instead makes Vite
# print that literal address, which the API's CORS then rejects as a
# different origin — a 400 on every request that looks like "the backend
# isn't working" but is really a CORS mismatch (see docs/decisions.md).
exec npm run dev -- --port 5173

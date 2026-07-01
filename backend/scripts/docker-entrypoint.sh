#!/bin/sh
set -e
cd /app
export PYTHONPATH=/app/src

echo "Running Alembic migrations..."
alembic -c alembic.ini upgrade head

PORT="${PORT:-8000}"
echo "Starting API server on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"

#!/bin/sh
set -e
cd /app
export PYTHONPATH=/app/src

echo "Running Alembic migrations..."
alembic -c alembic.ini upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

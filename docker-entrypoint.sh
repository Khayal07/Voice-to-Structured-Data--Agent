#!/usr/bin/env bash
set -euo pipefail

# Apply database migrations, then start the API.
echo "Running database migrations..."
alembic upgrade head

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

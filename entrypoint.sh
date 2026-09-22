#!/bin/bash
set -e

# Wait for PostgreSQL to become available (dynamically parses DATABASE_URL)
echo "Waiting for PostgreSQL to be ready..."
python - <<'PY'
import os
import socket
import sys
import time
from urllib.parse import urlparse

db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app_user:app_password@postgres:5432/todo_db",
)

# Replace driver prefix if present so urlparse works reliably
if "://" in db_url:
    scheme, remainder = db_url.split("://", 1)
    db_url = f"http://{remainder}"

parsed = urlparse(db_url)
host = parsed.hostname or "postgres"
port = parsed.port or 5432
timeout = 30

start = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"PostgreSQL at {host}:{port} is ready.")
            break
    except (ConnectionRefusedError, socket.timeout, OSError):
        if time.time() - start > timeout:
            print(f"Timeout waiting for PostgreSQL at {host}:{port}", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)
PY

# Apply pending Alembic migrations
echo "Running Alembic migrations..."
python -m alembic upgrade head

# Start the Uvicorn server (uses $PORT if supplied by host/cloud platform)
echo "Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
"""Application configuration loaded from environment variables.

All values have sensible fallbacks so the application can boot in a
development environment without a ``.env`` file.  In production, set
the environment variables explicitly (or via a secrets manager).
"""

import os

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
# The async database URL is used by the application at runtime via
# ``create_async_engine``.  The driver is ``asyncpg``.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://app_user:app_password@localhost:5433/todo_db",
)

# A *synchronous* URL (psycopg2 driver) — used by Alembic for migrations.
# psycopg2 is the standard sync driver that Alembic's offline/online helpers
# use with ``create_engine`` rather than ``create_async_engine``.
SYNC_DATABASE_URL = os.environ.get(
    "SYNC_DATABASE_URL",
    "postgresql://app_user:app_password@localhost:5433/todo_db",
)

# ---------------------------------------------------------------------------
# JWT / security configuration
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

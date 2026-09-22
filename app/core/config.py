"""Application configuration loaded from environment variables.

All values have sensible fallbacks so the application can boot in a
development environment without a ``.env`` file. In production, set
the environment variables explicitly (or via a secrets manager).
"""

import os


def _get_async_database_url() -> str:
    """Retrieve and normalize the runtime database URL for asyncpg."""
    raw_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://app_user:app_password@localhost:5433/todo_db",
    )

    # Normalize Render / Heroku legacy scheme prefixes to asyncpg
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if raw_url.startswith("postgresql://") and not raw_url.startswith(
        "postgresql+asyncpg://"
    ):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return raw_url


# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
# The async database URL is used by the application at runtime via
# ``create_async_engine``. The driver is ``asyncpg``.
DATABASE_URL = _get_async_database_url()

# A *synchronous* URL (psycopg2 driver) — used by Alembic for migrations.
# Automatically derived from DATABASE_URL unless explicitly overridden.
SYNC_DATABASE_URL = os.environ.get(
    "SYNC_DATABASE_URL",
    DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"),
)

# ---------------------------------------------------------------------------
# JWT / security configuration
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key_change_in_prod")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

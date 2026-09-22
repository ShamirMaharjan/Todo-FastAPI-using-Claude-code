"""Alembic environment configuration for async PostgreSQL.

Uses SQLAlchemy 2.0 async engines (``asyncpg``) and configures Alembic
to run migrations via a synchronous ``create_engine`` bridge. This is
the standard pattern: Alembic's own API is synchronous, so we connect
to the database with a sync engine (psycopg2) while the application
uses asyncpg for its async sessions.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Dynamically override sqlalchemy.url from the environment variable if available
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Convert async driver (postgresql+asyncpg://) to sync driver (postgresql://) for Alembic
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    elif "+asyncpg" in database_url:
        database_url = database_url.replace("+asyncpg", "")
    config.set_main_option("sqlalchemy.url", database_url)

# add your model's MetaData object here
# for 'autogenerate' support — import from the application's Base.
from app.database import Base  # noqa: E402
from app.models import Task, User  # noqa: E402  (ensures models are registered)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to
    the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure and run migrations against a single connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with a sync engine.

    Uses a synchronous ``create_engine`` (psycopg2 driver) — this is
    the standard Alembic pattern. The application itself uses asyncpg
    via ``create_async_engine``; Alembic's API is synchronous and
    connects via psycopg2.
    """
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
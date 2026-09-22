"""Async PostgreSQL database connection and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from .core.config import DATABASE_URL

# Create async engine for PostgreSQL using the asyncpg driver.
# NullPool is used to avoid "database is locked" errors and to ensure
# clean connection handling with asyncpg.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)

# Async session factory bound to the engine
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base for all models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Used as a dependency in route handlers via ``Depends(get_db)``.
    The session is automatically closed after the request completes.
    """
    async with AsyncSessionLocal() as session:
        yield session

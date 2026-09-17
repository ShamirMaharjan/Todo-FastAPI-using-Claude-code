"""Pytest configuration and shared fixtures for integration tests."""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create all tables in the in-memory test database once for the session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    # Drop all tables after the session completes
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session(db_engine) -> AsyncSession:
    """Provide a clean async database session for each test.

    Rolls back any uncommitted changes after the test so each test
    starts with a pristine database.
    """
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(db_engine):
    """Truncate all tables before each test for full isolation.

    Works alongside ``db_session``: because the in-memory SQLite database
    uses a shared ``StaticPool``, committed rows from one test would
    otherwise be visible to subsequent tests. This fixture clears every
    table before each test runs.
    """
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncClient:
    """Provide an async test client with the DB dependency overridden.

    The ``get_db`` dependency is replaced with one that yields the
    per-test ``db_session`` fixture, ensuring tests use the isolated
    in-memory database.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

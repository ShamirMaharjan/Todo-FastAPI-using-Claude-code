"""Pytest configuration and shared fixtures for integration tests.

Uses PostgreSQL (asyncpg) as the test database, matching the production
configuration.  Tables are created and dropped at session scope; each test
starts with a clean database via the clean_tables fixture.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import DATABASE_URL
from app.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create the async test engine with NullPool to avoid cross-event-loop
    connection issues. NullPool creates connections on-demand, so they are
    always bound to the current event loop rather than a stale one.
    """
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_engine(test_engine):
    """Create all tables in the test database once for the session."""
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
    session_maker = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(db_engine):
    """Truncate all tables before each test for full isolation."""
    async with db_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


@pytest_asyncio.fixture()
async def client(db_session) -> AsyncClient:
    """Provide an async test client with the DB dependency overridden."""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
async def auth_token(client: AsyncClient) -> str:
    """Register and log in a test user, returning the JWT access token."""
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    response = await client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest_asyncio.fixture()
async def auth_headers(client: AsyncClient, auth_token: str) -> dict[str, str]:
    """Return Authorization header dict for the authenticated test user."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture()
async def auth_client(client: AsyncClient, auth_token: str) -> AsyncClient:
    """Provide the test client with the bearer token pre-set in default headers."""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    yield client
    client.headers.pop("Authorization", None)

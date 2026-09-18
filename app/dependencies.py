"""FastAPI dependency providers for wiring services and repositories."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .core.security import decode_access_token
from .database import get_db
from .models import User
from .repositories.task_repository import TaskRepository
from .repositories.user_repository import UserRepository
from .services.auth_service import AuthService
from .services.task_service import TaskService

# OAuth2 scheme for token-based authentication.
# The tokenUrl tells FastAPI where clients obtain the token (the login endpoint).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[AuthService, None]:
    """FastAPI dependency that yields an ``AuthService`` backed by the request session.

    Keeps the auth router free of ``AsyncSession`` and SQLAlchemy imports,
    preserving strict layered separation (Router -> Service -> Repository).
    """
    repo = UserRepository(db)
    yield AuthService(repo)


async def get_task_service(
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[TaskService, None]:
    """FastAPI dependency that yields a ``TaskService`` backed by the request session.

    This factory lives outside the router so that ``app/routers/task.py``
    never imports ``AsyncSession`` or SQLAlchemy query primitives directly,
    preserving strict layered separation (Router -> Service -> Repository).
    """
    repo = TaskRepository(db)
    yield TaskService(repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """Resolve and validate the authenticated user from a bearer token.

    Args:
        token: The JWT bearer token extracted from the Authorization header.
        session: The async database session for user lookups.

    Returns:
        The authenticated ``User`` instance.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid, expired,
            missing a ``sub`` claim, or the referenced user is not found
            or inactive. The response includes the ``WWW-Authenticate: Bearer``
            header.
    """
    payload = decode_access_token(token)
    if payload is None:
        raise _credentials_exception()

    email: str | None = payload.get("sub")
    if not email:
        raise _credentials_exception()

    repo = UserRepository(session)
    user = await repo.get_by_email(email)
    if user is None or not user.is_active:
        raise _credentials_exception()

    return user


def _credentials_exception() -> HTTPException:
    """Build a fresh 401 HTTPException with the Bearer challenge header."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

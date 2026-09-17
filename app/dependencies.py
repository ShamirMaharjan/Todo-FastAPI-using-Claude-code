"""FastAPI dependency providers for wiring services and repositories."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .repositories.task_repository import TaskRepository
from .services.task_service import TaskService


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

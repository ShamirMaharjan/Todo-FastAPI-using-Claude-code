"""Task repository encapsulating all database access for Task objects."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Task
from ..schemas import TaskCreate, TaskUpdate


class TaskRepository:
    """Repository class for Task database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, task_id: int, user_id: int) -> Optional[Task]:
        """Retrieve a single task by its ID, scoped to the owning user.

        Args:
            task_id: The unique identifier of the task.
            user_id: The ID of the user who owns the task.

        Returns:
            The matching ``Task`` if found and owned by *user_id*, else ``None``.
        """
        result = await self.session.execute(
            select(Task)
            .where(Task.id == task_id)
            .where(Task.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        user_id: int,
        completed: Optional[bool] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """Retrieve tasks owned by *user_id* with optional completed filter, offset, and limit.

        Args:
            user_id: The ID of the user whose tasks to retrieve.
            completed: Optional filter for completed tasks.
            offset: Pagination offset.
            limit: Maximum number of tasks to return.

        Returns:
            A list of tasks owned by *user_id*.
        """
        query = select(Task).where(Task.user_id == user_id)
        if completed is not None:
            query = query.where(Task.completed == completed)
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, schema: TaskCreate, user_id: int) -> Task:
        """Create a new task owned by *user_id* from the schema and return the created task.

        Args:
            schema: The task creation data.
            user_id: The ID of the user who owns the task.

        Returns:
            The newly created ``Task`` instance.
        """
        task = Task(**schema.model_dump(), user_id=user_id)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(self, db_obj: Task, schema: TaskUpdate, user_id: int) -> Task:
        """Update only the provided fields and return the updated task.

        Args:
            db_obj: The existing ``Task`` to update (already scoped to *user_id*).
            schema: The partial task data to update.
            user_id: The ID of the owning user (for consistency / audit).

        Returns:
            The updated task.
        """
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Task, user_id: int) -> None:
        """Delete the given task from the database.

        Args:
            db_obj: The existing ``Task`` to delete (already scoped to *user_id*).
            user_id: The ID of the owning user (for consistency / audit).
        """
        await self.session.delete(db_obj)
        await self.session.commit()

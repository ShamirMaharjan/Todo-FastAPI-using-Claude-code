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

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Retrieve a single task by its ID. Returns None if not found."""
        result = await self.session.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        completed: Optional[bool] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """Retrieve tasks with optional completed filter, offset, and limit."""
        query = select(Task)
        if completed is not None:
            query = query.where(Task.completed == completed)
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, schema: TaskCreate) -> Task:
        """Create a new task from the schema and return the created task."""
        task = Task(**schema.model_dump())
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update(self, db_obj: Task, schema: TaskUpdate) -> Task:
        """Update only the provided fields and return the updated task."""
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def delete(self, db_obj: Task) -> None:
        """Delete the given task from the database."""
        await self.session.delete(db_obj)
        await self.session.commit()

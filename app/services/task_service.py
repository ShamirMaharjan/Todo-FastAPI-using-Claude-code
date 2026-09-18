"""Service layer for task business logic."""

from typing import List, Optional

from ..repositories.task_repository import TaskRepository
from ..models import Task
from ..schemas import TaskCreate, TaskUpdate


class TaskNotFoundException(Exception):
    """Raised when a task with the specified ID does not exist."""

    def __init__(self, task_id: int) -> None:
        self.task_id = task_id
        super().__init__(f"Task with id {task_id} not found")


class TaskService:
    """Business logic layer for task operations.

    Args:
        repo: The task repository used for data access.
    """

    def __init__(self, repo: TaskRepository) -> None:
        self.repo = repo

    async def get_by_id(self, task_id: int, user_id: int) -> Task:
        """Retrieve a single task by its ID, scoped to the owning user.

        Args:
            task_id: The unique identifier of the task.
            user_id: The ID of the user who owns the task.

        Returns:
            The task if found and owned by *user_id*.

        Raises:
            TaskNotFoundException: If the task does not exist or does not
                belong to *user_id*.
        """
        task = await self.repo.get_by_id(task_id, user_id)
        if task is None:
            raise TaskNotFoundException(task_id)
        return task

    async def list_all(
        self,
        user_id: int,
        completed: Optional[bool] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[Task]:
        """Retrieve all tasks for a user, optionally filtered by completion status.

        Args:
            user_id: The ID of the user whose tasks to retrieve.
            completed: Optional filter for completed tasks.
            offset: Pagination offset.
            limit: Maximum number of tasks to return.

        Returns:
            A list of tasks owned by *user_id*.
        """
        return await self.repo.list(user_id, completed=completed, offset=offset, limit=limit)

    async def create_task(self, schema: TaskCreate, user_id: int) -> Task:
        """Create a new task.

        Args:
            schema: The task creation data.
            user_id: The ID of the user who owns the task.

        Returns:
            The created task.
        """
        return await self.repo.create(schema, user_id)

    async def update_task(self, task_id: int, schema: TaskUpdate, user_id: int) -> Task:
        """Partially update an existing task.

        Args:
            task_id: The unique identifier of the task.
            schema: The partial task data to update.
            user_id: The ID of the user who owns the task (for tenant scoping).

        Returns:
            The updated task.

        Raises:
            TaskNotFoundException: If the task does not exist.
        """
        task = await self.get_by_id(task_id, user_id)
        return await self.repo.update(task, schema, user_id)

    async def delete_task(self, task_id: int, user_id: int) -> None:
        """Delete a task by its ID.

        Args:
            task_id: The unique identifier of the task.
            user_id: The ID of the user who owns the task (for tenant scoping).

        Raises:
            TaskNotFoundException: If the task does not exist.
        """
        task = await self.get_by_id(task_id, user_id)
        await self.repo.delete(task, user_id)

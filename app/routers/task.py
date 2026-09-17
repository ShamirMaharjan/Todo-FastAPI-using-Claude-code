"""Task router with CRUD endpoints.

This router is the HTTP layer only: it receives requests, delegates all
business logic to ``TaskService``, and translates domain exceptions into
HTTP responses.  It never imports ``AsyncSession`` or SQLAlchemy query
primitives, enforcing strict layered separation.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from ..dependencies import get_task_service
from ..schemas import TaskCreate, TaskResponse, TaskUpdate
from ..services.task_service import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task item.

    Args:
        task: The task data to create.
        service: The injected task service.

    Returns:
        The created task item.
    """
    return await service.create_task(task)


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    completed: Optional[bool] = None,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
) -> List[TaskResponse]:
    """Retrieve a list of task items.

    Args:
        completed: Optional filter to return only completed (``True``)
            or only pending (``False``) tasks. When ``None``, all tasks
            are returned.
        limit: Maximum number of tasks to return. Defaults to 100.
        offset: Number of tasks to skip. Defaults to 0.
        service: The injected task service.

    Returns:
        A list of task items matching the filter criteria.
    """
    tasks = await service.list_all(completed=completed, offset=offset, limit=limit)
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Retrieve a single task item by its ID.

    Args:
        task_id: The unique identifier of the task item.
        service: The injected task service.

    Returns:
        The task item with the specified ID.

    Raises:
        TaskNotFoundException: 404 if the task item does not exist.
    """
    return await service.get_by_id(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Partially update a task item by its ID.

    Only the fields provided in the request body are updated.

    Args:
        task_id: The unique identifier of the task item.
        task: The partial task data to update.
        service: The injected task service.

    Returns:
        The updated task item.

    Raises:
        TaskNotFoundException: 404 if the task item does not exist.
    """
    return await service.update_task(task_id, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task item by its ID.

    Args:
        task_id: The unique identifier of the task item.
        service: The injected task service.

    Raises:
        TaskNotFoundException: 404 if the task item does not exist.
    """
    await service.delete_task(task_id)

"""Task router with CRUD endpoints.

This router is the HTTP layer only: it receives requests, delegates all
business logic to ``TaskService``, and translates domain exceptions into
HTTP responses.  It never imports ``AsyncSession`` or SQLAlchemy query
primitives, enforcing strict layered separation.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status

from ..dependencies import get_current_user
from ..dependencies import get_task_service
from ..models import User
from ..schemas import TaskCreate
from ..schemas import TaskResponse
from ..schemas import TaskUpdate
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
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Create a new task item.

    Args:
        task: The task data to create.
        current_user: The authenticated user (used for tenant isolation).
        service: The injected task service.

    Returns:
        The created task item.
    """
    return await service.create_task(task, current_user.id)


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    completed: bool | None = None,
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    """Retrieve a list of task items.

    Args:
        completed: Optional filter to return only completed (``True``)
            or only pending (``False``) tasks. When ``None``, all tasks
            are returned.
        limit: Maximum number of tasks to return. Defaults to 100.
        offset: Number of tasks to skip. Defaults to 0.
        current_user: The authenticated user (used for tenant isolation).
        service: The injected task service.

    Returns:
        A list of task items matching the filter criteria.
    """
    tasks = await service.list_all(
        current_user.id, completed=completed, offset=offset, limit=limit
    )
    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Retrieve a single task item by its ID.

    Args:
        task_id: The unique identifier of the task item.
        current_user: The authenticated user (used for tenant isolation).
        service: The injected task service.

    Returns:
        The task item with the specified ID.

    Raises:
        TaskNotFoundError: 404 if the task item does not exist.
    """
    return await service.get_by_id(task_id, current_user.id)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task: TaskUpdate,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """Partially update a task item by its ID.

    Only the fields provided in the request body are updated.

    Args:
        task_id: The unique identifier of the task item.
        task: The partial task data to update.
        current_user: The authenticated user (used for tenant isolation).
        service: The injected task service.

    Returns:
        The updated task item.

    Raises:
        TaskNotFoundError: 404 if the task item does not exist.
    """
    return await service.update_task(task_id, task, current_user.id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> None:
    """Delete a task item by its ID.

    Args:
        task_id: The unique identifier of the task item.
        current_user: The authenticated user (used for tenant isolation).
        service: The injected task service.

    Raises:
        TaskNotFoundError: 404 if the task item does not exist.
    """
    await service.delete_task(task_id, current_user.id)

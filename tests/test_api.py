"""Integration tests for the FastAPI Task Management API.

Tests cover the full 3-tier architecture (Router -> Service -> Repository)
including CRUD operations, pagination, filtering, validation, and error
handling (404 / 422).  All task-related tests use the ``auth_client``
fixture which pre-sets a bearer token so that tenant-isolated endpoints
are accessible.
"""

import pytest
from httpx import AsyncClient


class TestHealthCheck:
    """Tests for the health-check and info endpoints (no auth required)."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """GET / should return a status:ok response."""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_info(self, client: AsyncClient) -> None:
        """GET /info should return app name and version."""
        response = await client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "FastAPI Todo"
        assert "version" in data


class TestTaskCRUD:
    """Integration tests for the /tasks CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_task(self, auth_client: AsyncClient) -> None:
        """POST /tasks should create a new task and return it."""
        payload = {"title": "Write tests"}
        response = await auth_client.post("/tasks/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Write tests"
        assert data["completed"] is False
        assert data["description"] is None
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_task_with_all_fields(self, auth_client: AsyncClient) -> None:
        """POST /tasks should accept title, description, and completed fields."""
        payload = {
            "title": "Deploy app",
            "description": "Push to production",
            "completed": True,
        }
        response = await auth_client.post("/tasks/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Deploy app"
        assert data["description"] == "Push to production"
        assert data["completed"] is True

    @pytest.mark.asyncio
    async def test_create_task_with_priority(self, auth_client: AsyncClient) -> None:
        """POST /tasks with a custom priority should store and return it."""
        payload = {"title": "High priority task", "priority": "HIGH"}
        response = await auth_client.post("/tasks/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "HIGH"

    @pytest.mark.asyncio
    async def test_create_task_default_priority(self, auth_client: AsyncClient) -> None:
        """POST /tasks without a priority should default to 'MEDIUM'."""
        payload = {"title": "Default priority task"}
        response = await auth_client.post("/tasks/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "MEDIUM"

    @pytest.mark.asyncio
    async def test_create_task_invalid_data(self, auth_client: AsyncClient) -> None:
        """POST /tasks with missing title should return 422."""
        response = await auth_client.post("/tasks/", json={"description": "no title"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, auth_client: AsyncClient) -> None:
        """GET /tasks on an empty database should return an empty list."""
        response = await auth_client.get("/tasks/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_tasks(self, auth_client: AsyncClient) -> None:
        """GET /tasks should return all created tasks."""
        await auth_client.post("/tasks/", json={"title": "Task A"})
        await auth_client.post("/tasks/", json={"title": "Task B"})

        response = await auth_client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = {item["title"] for item in data}
        assert {"Task A", "Task B"} == titles

    @pytest.mark.asyncio
    async def test_get_task_by_id(self, auth_client: AsyncClient) -> None:
        """GET /tasks/{id} should return the task with the given ID."""
        create_response = await auth_client.post("/tasks/", json={"title": "Fix bug"})
        task_id = create_response.json()["id"]

        response = await auth_client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Fix bug"
        assert data["id"] == task_id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, auth_client: AsyncClient) -> None:
        """GET /tasks/{id} with unknown id should return 404."""
        response = await auth_client.get("/tasks/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task with id 9999 not found"

    @pytest.mark.asyncio
    async def test_update_task(self, auth_client: AsyncClient) -> None:
        """PATCH /tasks/{id} should update the provided fields."""
        create_response = await auth_client.post("/tasks/", json={"title": "Old task"})
        task_id = create_response.json()["id"]

        response = await auth_client.patch(
            f"/tasks/{task_id}",
            json={"title": "New task", "completed": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New task"
        assert data["completed"] is True

    @pytest.mark.asyncio
    async def test_update_task_priority(self, auth_client: AsyncClient) -> None:
        """PATCH /tasks/{id} should update the priority field."""
        create_response = await auth_client.post("/tasks/", json={"title": "Task"})
        task_id = create_response.json()["id"]

        response = await auth_client.patch(
            f"/tasks/{task_id}",
            json={"priority": "LOW"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "LOW"

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, auth_client: AsyncClient) -> None:
        """PATCH /tasks/{id} with unknown id should return 404."""
        response = await auth_client.patch("/tasks/9999", json={"title": "X"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Task with id 9999 not found"

    @pytest.mark.asyncio
    async def test_delete_task(self, auth_client: AsyncClient) -> None:
        """DELETE /tasks/{id} should remove the task and return 204."""
        create_response = await auth_client.post("/tasks/", json={"title": "Delete me"})
        task_id = create_response.json()["id"]

        response = await auth_client.delete(f"/tasks/{task_id}")
        assert response.status_code == 204

        get_response = await auth_client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, auth_client: AsyncClient) -> None:
        """DELETE /tasks/{id} with unknown id should return 404."""
        response = await auth_client.delete("/tasks/9999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task with id 9999 not found"


class TestTaskPagination:
    """Tests for pagination on GET /tasks/."""

    @pytest.mark.asyncio
    async def test_list_tasks_pagination_limit(self, auth_client: AsyncClient) -> None:
        """GET /tasks/?limit=N should return at most N tasks."""
        for i in range(5):
            await auth_client.post("/tasks/", json={"title": f"Task {i}"})

        response = await auth_client.get("/tasks/?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_tasks_pagination_offset(self, auth_client: AsyncClient) -> None:
        """GET /tasks/?offset=M should skip the first M tasks."""
        for i in range(5):
            await auth_client.post("/tasks/", json={"title": f"Task {i}"})

        response = await auth_client.get("/tasks/?offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        titles = {item["title"] for item in data}
        assert titles == {"Task 2", "Task 3", "Task 4"}

    @pytest.mark.asyncio
    async def test_list_tasks_pagination_combined(self, auth_client: AsyncClient) -> None:
        """GET /tasks/?limit=N&offset=M should return N tasks starting after M."""
        for i in range(5):
            await auth_client.post("/tasks/", json={"title": f"Task {i}"})

        response = await auth_client.get("/tasks/?limit=2&offset=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        titles = {item["title"] for item in data}
        assert titles == {"Task 1", "Task 2"}

    @pytest.mark.asyncio
    async def test_list_tasks_pagination_default(self, auth_client: AsyncClient) -> None:
        """GET /tasks/ with no params should return all tasks (3)."""
        for i in range(3):
            await auth_client.post("/tasks/", json={"title": f"Task {i}"})

        response = await auth_client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_tasks_pagination_limit_exceeds_max(
        self, auth_client: AsyncClient
    ) -> None:
        """GET /tasks/?limit=200 should return 422 (violates le=100)."""
        response = await auth_client.get("/tasks/?limit=200")
        assert response.status_code == 422


class TestTaskFiltering:
    """Tests for the completed-status filter on GET /tasks/."""

    @pytest.mark.asyncio
    async def test_list_tasks_filter_completed_true(
        self, auth_client: AsyncClient
    ) -> None:
        """GET /tasks/?completed=true should return only completed tasks."""
        await auth_client.post("/tasks/", json={"title": "Done task", "completed": True})
        await auth_client.post("/tasks/", json={"title": "Pending task", "completed": False})

        response = await auth_client.get("/tasks/?completed=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["completed"] is True
        assert data[0]["title"] == "Done task"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_completed_false(
        self, auth_client: AsyncClient
    ) -> None:
        """GET /tasks/?completed=false should return only pending tasks."""
        await auth_client.post("/tasks/", json={"title": "Done task", "completed": True})
        await auth_client.post("/tasks/", json={"title": "Pending task", "completed": False})

        response = await auth_client.get("/tasks/?completed=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["completed"] is False
        assert data[0]["title"] == "Pending task"

    @pytest.mark.asyncio
    async def test_list_tasks_filter_no_filter_returns_all(
        self, auth_client: AsyncClient
    ) -> None:
        """GET /tasks/ with no filter should return all tasks."""
        await auth_client.post("/tasks/", json={"title": "Done task", "completed": True})
        await auth_client.post("/tasks/", json={"title": "Pending task", "completed": False})

        response = await auth_client.get("/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestTaskValidation:
    """Tests for Pydantic v2 schema validation (extra='forbid', field constraints)."""

    @pytest.mark.asyncio
    async def test_create_task_rejects_unknown_field(
        self, auth_client: AsyncClient
    ) -> None:
        """POST /tasks with an unknown field should return 422 (extra='forbid')."""
        payload = {"title": "Valid task", "unknown_field": "value"}
        response = await auth_client.post("/tasks/", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_rejects_empty_title(
        self, auth_client: AsyncClient
    ) -> None:
        """POST /tasks with an empty title should return 422 (min_length=1)."""
        response = await auth_client.post("/tasks/", json={"title": ""})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_rejects_title_too_long(
        self, auth_client: AsyncClient
    ) -> None:
        """POST /tasks with a title exceeding 255 chars should return 422."""
        response = await auth_client.post("/tasks/", json={"title": "x" * 256})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_rejects_description_too_long(
        self, auth_client: AsyncClient
    ) -> None:
        """POST /tasks with a description exceeding 2000 chars should return 422."""
        response = await auth_client.post(
            "/tasks/", json={"title": "Valid", "description": "x" * 2001}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_rejects_priority_too_long(
        self, auth_client: AsyncClient
    ) -> None:
        """POST /tasks with a priority exceeding 50 chars should return 422."""
        response = await auth_client.post(
            "/tasks/", json={"title": "Valid", "priority": "x" * 51}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_rejects_invalid_priority(
        self, auth_client: AsyncClient
    ) -> None:
        """POST /tasks with an invalid priority value should return 422."""
        response = await auth_client.post(
            "/tasks/", json={"title": "Valid", "priority": "EXTREME"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_task_rejects_unknown_field(
        self, auth_client: AsyncClient
    ) -> None:
        """PATCH /tasks/{id} with an unknown field should return 422 (extra='forbid')."""
        create_response = await auth_client.post("/tasks/", json={"title": "Test task"})
        task_id = create_response.json()["id"]

        response = await auth_client.patch(
            f"/tasks/{task_id}", json={"unknown_field": "value"}
        )
        assert response.status_code == 422

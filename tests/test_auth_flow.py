"""Integration tests for the full authentication flow and tenant isolation.

Covers:
  * Registration and login (token issuance).
  * Unauthenticated access to protected endpoints (401).
  * Tenant isolation: User A cannot view, list, update, or delete
    User B's tasks.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

# Helper credentials -----------------------------------------------------------
USER_A_EMAIL = "usera@example.com"
USER_A_PASS = "passwordA123"
USER_B_EMAIL = "userb@example.com"
USER_B_PASS = "passwordB123"


async def _register_and_login(client: AsyncClient, email: str, password: str) -> str:
    """Register a user then log in, returning the bearer access token."""
    await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    response = await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


# ---------------------------------------------------------------------------
# Full registration / login flow
# ---------------------------------------------------------------------------


class TestAuthFlow:
    """End-to-end tests for register -> login -> token validation."""

    @pytest.mark.asyncio
    async def test_register_returns_user_response(self, client: AsyncClient) -> None:
        """POST /auth/register should return the created user with 201."""
        response = await client.post(
            "/auth/register",
            json={"email": USER_A_EMAIL, "password": USER_A_PASS},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == USER_A_EMAIL
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        """POST /auth/register with an existing email should return 400."""
        await client.post(
            "/auth/register",
            json={"email": USER_A_EMAIL, "password": USER_A_PASS},
        )
        response = await client.post(
            "/auth/register",
            json={"email": USER_A_EMAIL, "password": "otherpass123"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

    @pytest.mark.asyncio
    async def test_login_returns_bearer_token(self, client: AsyncClient) -> None:
        """POST /auth/login should return a JWT bearer token."""
        await client.post(
            "/auth/register",
            json={"email": USER_A_EMAIL, "password": USER_A_PASS},
        )
        response = await client.post(
            "/auth/login",
            data={"username": USER_A_EMAIL, "password": USER_A_PASS},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        """POST /auth/login with wrong password should return 401."""
        await client.post(
            "/auth/register",
            json={"email": USER_A_EMAIL, "password": USER_A_PASS},
        )
        response = await client.post(
            "/auth/login",
            data={"username": USER_A_EMAIL, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client: AsyncClient) -> None:
        """Accessing /tasks without a token should return 401."""
        response = await client.get("/tasks/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_with_invalid_token(
        self, client: AsyncClient
    ) -> None:
        """Accessing /tasks with an invalid token should return 401."""
        response = await client.get(
            "/tasks/",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    """Verify that one user cannot access another user's tasks."""

    @pytest_asyncio.fixture()
    async def tokens(self, client: AsyncClient) -> dict[str, str]:
        """Register two users and return their bearer tokens."""
        token_a = await _register_and_login(client, USER_A_EMAIL, USER_A_PASS)
        token_b = await _register_and_login(client, USER_B_EMAIL, USER_B_PASS)
        return {"a": token_a, "b": token_b}

    @pytest.mark.asyncio
    async def test_user_b_cannot_list_user_a_tasks(
        self, client: AsyncClient, tokens: dict[str, str]
    ) -> None:
        """User B's task list should not contain User A's tasks."""
        # User A creates a task
        await client.post(
            "/tasks/",
            json={"title": "User A secret task"},
            headers={"Authorization": f"Bearer {tokens['a']}"},
        )

        # User B lists tasks -- should be empty
        response = await client.get(
            "/tasks/",
            headers={"Authorization": f"Bearer {tokens['b']}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_user_b_cannot_view_user_a_task(
        self, client: AsyncClient, tokens: dict[str, str]
    ) -> None:
        """User B should get 404 when trying to read User A's task."""
        # User A creates a task
        create_resp = await client.post(
            "/tasks/",
            json={"title": "User A secret task"},
            headers={"Authorization": f"Bearer {tokens['a']}"},
        )
        task_id = create_resp.json()["id"]

        # User B tries to GET it
        response = await client.get(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {tokens['b']}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == f"Task with id {task_id} not found"

    @pytest.mark.asyncio
    async def test_user_b_cannot_update_user_a_task(
        self, client: AsyncClient, tokens: dict[str, str]
    ) -> None:
        """User B should get 404 when trying to update User A's task."""
        # User A creates a task
        create_resp = await client.post(
            "/tasks/",
            json={"title": "User A secret task"},
            headers={"Authorization": f"Bearer {tokens['a']}"},
        )
        task_id = create_resp.json()["id"]

        # User B tries to PATCH it
        response = await client.patch(
            f"/tasks/{task_id}",
            json={"title": "Hacked by User B"},
            headers={"Authorization": f"Bearer {tokens['b']}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == f"Task with id {task_id} not found"

    @pytest.mark.asyncio
    async def test_user_b_cannot_delete_user_a_task(
        self, client: AsyncClient, tokens: dict[str, str]
    ) -> None:
        """User B should get 404 when trying to delete User A's task."""
        # User A creates a task
        create_resp = await client.post(
            "/tasks/",
            json={"title": "User A secret task"},
            headers={"Authorization": f"Bearer {tokens['a']}"},
        )
        task_id = create_resp.json()["id"]

        # User B tries to DELETE it
        response = await client.delete(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {tokens['b']}"},
        )
        assert response.status_code == 404

        # Confirm the task still exists for User A
        verify = await client.get(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {tokens['a']}"},
        )
        assert verify.status_code == 200
        assert verify.json()["title"] == "User A secret task"

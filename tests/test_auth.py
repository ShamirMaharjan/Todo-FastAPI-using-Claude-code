"""Unit tests for authentication: password hashing, JWT tokens, and user registration.

Covers:
  * ``app.core.security`` — bcrypt hashing and PyJWT encode/decode.
  * ``app.services.auth_service`` — registration (email uniqueness) and
    authentication (credential verification).
"""

from datetime import timedelta

import pytest
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas import UserCreate
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_service(db_session: AsyncSession) -> AuthService:
    """Provide an ``AuthService`` backed by the test database session."""
    repo = UserRepository(db_session)
    return AuthService(repo)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    """Tests for bcrypt password hashing and verification."""

    def test_hash_password_returns_hash(self) -> None:
        """``hash_password`` should return a bcrypt hash, not the plaintext."""
        hashed = hash_password("testpassword123")
        assert hashed != "testpassword123"
        assert hashed.startswith("$2")

    def test_hash_password_uses_salt(self) -> None:
        """``hash_password`` should produce different hashes for the same input."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2

    def test_verify_password_correct(self) -> None:
        """``verify_password`` should return ``True`` for a correct password."""
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self) -> None:
        """``verify_password`` should return ``False`` for an incorrect password."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------


class TestJWTTokens:
    """Tests for JWT access-token creation and decoding."""

    def test_create_access_token(self) -> None:
        """``create_access_token`` should return a non-empty JWT string."""
        token = create_access_token({"sub": "user@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_roundtrip(self) -> None:
        """``decode_access_token`` should return the original payload."""
        payload = {"sub": "user@example.com", "custom": "data"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user@example.com"
        assert decoded["custom"] == "data"

    def test_decode_access_token_invalid(self) -> None:
        """``decode_access_token`` should return ``None`` for an invalid token."""
        decoded = decode_access_token("invalid.token.here")
        assert decoded is None

    def test_decode_access_token_tampered(self) -> None:
        """``decode_access_token`` should return ``None`` for a tampered token."""
        token = create_access_token({"sub": "user@example.com"})
        tampered = token[:-5] + "XXXXX"
        decoded = decode_access_token(tampered)
        assert decoded is None

    def test_create_access_token_sets_expiry(self) -> None:
        """The encoded token should include an ``exp`` claim."""
        token = create_access_token(
            {"sub": "user@example.com"},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        decoded = decode_access_token(token)
        assert decoded is not None
        assert "exp" in decoded
        assert "sub" in decoded

    def test_decode_access_token_expired(self) -> None:
        """``decode_access_token`` should return ``None`` for an expired token."""
        token = create_access_token(
            {"sub": "user@example.com"},
            expires_delta=timedelta(seconds=0),
        )
        decoded = decode_access_token(token)
        assert decoded is None


# ---------------------------------------------------------------------------
# Auth service — registration
# ---------------------------------------------------------------------------


class TestAuthServiceRegister:
    """Tests for ``AuthService.register_user``."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service: AuthService) -> None:
        """``register_user`` should create a user and return a ``UserResponse``."""
        user_in = UserCreate(email="test@example.com", password="securepass123")
        response = await auth_service.register_user(user_in)

        assert response.email == "test@example.com"
        assert response.is_active is True
        assert response.id is not None

    @pytest.mark.asyncio
    async def test_register_user_password_is_hashed(
        self, auth_service: AuthService, db_session: AsyncSession
    ) -> None:
        """The stored password should be hashed, not plaintext."""
        user_in = UserCreate(email="hashing@example.com", password="mysecret123")
        await auth_service.register_user(user_in)

        repo = UserRepository(db_session)
        user = await repo.get_by_email("hashing@example.com")
        assert user is not None
        assert user.hashed_password != "mysecret123"
        assert user.hashed_password.startswith("$2")

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(
        self, auth_service: AuthService
    ) -> None:
        """``register_user`` should raise HTTP 400 for a duplicate email."""
        user_in = UserCreate(email="dup@example.com", password="password123")
        await auth_service.register_user(user_in)

        duplicate = UserCreate(email="dup@example.com", password="differentpass")
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(duplicate)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Auth service — authentication
# ---------------------------------------------------------------------------


class TestAuthServiceAuthenticate:
    """Tests for ``AuthService.authenticate_user``."""

    @pytest.fixture()
    async def registered_user(
        self, auth_service: AuthService
    ) -> None:
        """Register a known user before each authentication test."""
        user_in = UserCreate(email="auth@example.com", password="correctpass123")
        await auth_service.register_user(user_in)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self, auth_service: AuthService, registered_user: None
    ) -> None:
        """``authenticate_user`` should return the ``User`` on valid credentials."""
        user = await auth_service.authenticate_user("auth@example.com", "correctpass123")
        assert isinstance(user, User)
        assert user.email == "auth@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(
        self, auth_service: AuthService, registered_user: None
    ) -> None:
        """``authenticate_user`` should raise HTTP 401 for an incorrect password."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user("auth@example.com", "wrongpassword")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(
        self, auth_service: AuthService
    ) -> None:
        """``authenticate_user`` should raise HTTP 401 for a non-existent email."""
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user("nobody@example.com", "anypassword")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

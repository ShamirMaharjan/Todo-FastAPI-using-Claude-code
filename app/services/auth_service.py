"""Service layer for authentication and user registration.

Encapsulates the business logic for registering new users and
authenticating existing ones, delegating persistence to
``UserRepository`` and password/JWT operations to ``app.core.security``.
"""

from fastapi import HTTPException
from fastapi import status

from ..core.security import hash_password
from ..core.security import verify_password
from ..models import User
from ..repositories.user_repository import UserRepository
from ..schemas import UserCreate
from ..schemas import UserResponse


class AuthService:
    """Business logic layer for authentication operations.

    Args:
        repo: The user repository used for data access.
    """

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def register_user(self, user_in: UserCreate) -> UserResponse:
        """Register a new user.

        Args:
            user_in: The user creation data containing email and password.

        Returns:
            The created user serialized as a ``UserResponse``.

        Raises:
            HTTPException: 400 if a user with the given email already exists.
        """
        existing = await self.repo.get_by_email(user_in.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed = hash_password(user_in.password)
        user = await self.repo.create(email=user_in.email, hashed_password=hashed)
        return UserResponse.model_validate(user)

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate a user by email and password.

        Args:
            email: The user's email address.
            password: The user's plaintext password.

        Returns:
            The authenticated ``User`` instance.

        Raises:
            HTTPException: 401 if the email does not exist or the password
                does not match.
        """
        user = await self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        return user

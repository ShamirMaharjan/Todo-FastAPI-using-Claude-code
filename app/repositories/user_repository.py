"""Repository for user database operations.

Follows the same async repository pattern as ``TaskRepository``,
encapsulating all SQLAlchemy access for the ``User`` model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User


class UserRepository:
    """Repository class for User database operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a single user by their email address.

        Args:
            email: The email address to look up.

        Returns:
            The matching ``User`` if found, ``None`` otherwise.
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        """Retrieve a single user by their primary key.

        Args:
            user_id: The user's ID.

        Returns:
            The matching ``User`` if found, ``None`` otherwise.
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str) -> User:
        """Create a new user with the given credentials.

        Args:
            email: The user's email address.
            hashed_password: The bcrypt-hashed password.

        Returns:
            The newly created ``User`` instance.
        """
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

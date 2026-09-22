"""Pydantic v2 request and response schemas."""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field

from .models import TaskPriority


class UserBase(BaseModel):
    """Shared fields for user schemas."""

    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user (request body)."""

    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., min_length=8, description="The user's password")


class UserResponse(UserBase):
    """Schema for serializing a user in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """Schema for the JWT access-token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for the decoded token payload."""

    email: str | None = None


class TaskBase(BaseModel):
    """Shared fields for task create and update operations."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="The title of the task",
    )
    description: str | None = Field(
        None,
        max_length=2000,
        description="Optional detailed description",
    )
    priority: TaskPriority | None = TaskPriority.MEDIUM
    completed: bool | None = Field(
        False,
        description="Whether the task is completed",
    )


class TaskCreate(TaskBase):
    """Schema for creating a new task item (request body)."""

    model_config = ConfigDict(extra="forbid")


class TaskUpdate(BaseModel):
    """Schema for partially updating a task item (request body).

    All fields are optional — only provided fields are updated.
    """

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    priority: TaskPriority | None = None
    completed: bool | None = None


class TaskResponse(TaskBase):
    """Schema for serializing a task item in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    user_id: int | None = None

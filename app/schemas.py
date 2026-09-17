"""Pydantic v2 request and response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    """Shared fields for task create and update operations."""

    title: str = Field(..., min_length=1, max_length=255, description="The title of the task")
    description: Optional[str] = Field(None, max_length=2000, description="Optional detailed description")
    priority: Optional[str] = Field("MEDIUM", max_length=50, description="Task priority level")
    completed: Optional[bool] = Field(False, description="Whether the task is completed")


class TaskCreate(TaskBase):
    """Schema for creating a new task item (request body)."""

    model_config = ConfigDict(extra="forbid")


class TaskUpdate(BaseModel):
    """Schema for partially updating a task item (request body).

    All fields are optional — only provided fields are updated.
    """

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, max_length=50)
    completed: Optional[bool] = None


class TaskResponse(TaskBase):
    """Schema for serializing a task item in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Boolean, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Task(Base):
    """A single task item."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="MEDIUM"
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title!r}, completed={self.completed})>"

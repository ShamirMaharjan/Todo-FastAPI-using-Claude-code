# Technical Architecture Document (TAD)

## 1. Architectural Overview
The system follows a strict **3-Tier Clean Architecture** model to isolate HTTP handling, business logic, and database persistence.

```
┌────────────────────────────────────────────────────────┐
│                   Router Layer                         │  <- Parses HTTP Requests, Input Validation (DTOs),
│              (app/routers/task.py)                     │     Invokes Service, Returns Pydantic Responses
└───────────────────────────┬────────────────────────────┘
                            │ Calls Service
┌───────────────────────────▼────────────────────────────┐
│                   Service Layer                        │  <- Enforces Domain Rules, Handles Transactions,
│              (app/services/task_service.py)            │     Orchestrates Data Operations
└───────────────────────────┬────────────────────────────┘
                            │ Calls Repository
┌───────────────────────────▼────────────────────────────┐
│                  Repository Layer                      │  <- Raw SQLAlchemy 2.0 Async Queries,
│           (app/repositories/task_repository.py)        │     Encapsulates Database Access
└───────────────────────────┬────────────────────────────┘
                            │ Executes SQL
┌───────────────────────────▼────────────────────────────┐
│                 Database (SQLite)                      │  <- Persistent Data Store via aiosqlite
└────────────────────────────────────────────────────────┘
```

---

## 2. Directory Hierarchy

```text
fastapi-todo/
├── CLAUDE.md
├── .claude/
│   ├── settings.json
│   └── skills/
│       └── add-api-endpoint/
│           └── SKILL.md
├── docs/
│   ├── PRD.md
│   ├── TAD.md
│   ├── SAD.md
│   └── TICKETS.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── task_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py
│   └── routers/
│       ├── __init__.py
│       └── task.py
├── tests/
│   ├── conftest.py
│   └── test_api.py
└── requirements.txt
```

---

## 3. Data Models & Schemas

### 3.1 SQLAlchemy 2.0 Model (`app/models.py`)
```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Task(Base):
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
        server_default=func.now(),
        nullable=False
    )
```

### 3.2 Pydantic v2 DTO Schemas (`app/schemas.py`)
- `TaskBase`: Core shared fields (`title`, `description`, `priority`, `completed`).
- `TaskCreate`: Inherits `TaskBase`; sets `ConfigDict(extra="forbid")`.
- `TaskUpdate`: All fields optional for partial updates (`PATCH`); fields include `title`, `description`, `priority`, `completed`.
- `TaskResponse`: Includes `id`, `created_at`; sets `ConfigDict(from_attributes=True)`.

---

## 4. Layer Responsibilities & Dependencies

| Layer | File Path | Responsibilities | Injected Dependencies |
|---|---|---|---|
| **Repository** | `app/repositories/task_repository.py` | Executes SQL queries (`select`, `insert`, `update`, `delete`). | `AsyncSession` |
| **Service** | `app/services/task_service.py` | Encapsulates business logic, domain validation, error handling. | `TaskRepository` |
| **Router** | `app/routers/task.py` | Receives HTTP requests, delegates to `TaskService`, manages status codes. | `TaskService` (via `Depends()`) |
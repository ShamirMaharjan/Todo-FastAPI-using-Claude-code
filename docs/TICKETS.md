# Feature Ticket List (TICKETS.md)

## Epic: Enterprise Architecture Refactoring & Consolidation

---

### Ticket TCK-001: Domain Model Consolidation
- **Summary:** Unify domain models by deleting duplicate `Todo` entities and keeping a single `Task` domain.
- **Layer:** `app/models.py`, `app/schemas.py`
- **Priority:** High
- **Acceptance Criteria:**
  1. Remove `Todo`, `TodoCreate`, `TodoUpdate`, `TodoResponse` classes.
  2. Maintain `Task` model with SQLAlchemy 2.0 type mapping (`Mapped[...]`).
  3. Ensure `TaskCreate`, `TaskUpdate`, `TaskResponse` enforce `extra="forbid"`.

---

### Ticket TCK-002: Repository Layer Implementation
- **Summary:** Build `TaskRepository` to encapsulate all database interaction.
- **Layer:** `app/repositories/task_repository.py`
- **Priority:** High
- **Acceptance Criteria:**
  1. Create `TaskRepository` class taking `AsyncSession` in `__init__`.
  2. Implement methods: `get_by_id(id)`, `list(completed, offset, limit)`, `create(schema)`, `update(db_obj, schema)`, `delete(db_obj)`.
  3. All database operations must use async SQLAlchemy select/commit/refresh.

---

### Ticket TCK-003: Service Layer Implementation
- **Summary:** Implement `TaskService` to host domain rules and orchestrate data access.
- **Layer:** `app/services/task_service.py`
- **Priority:** High
- **Acceptance Criteria:**
  1. Create `TaskService` class accepting `TaskRepository` via dependency injection.
  2. Raise domain-specific exceptions (e.g., `TaskNotFoundException`) when items do not exist.
  3. Ensure service methods return Pydantic models or domain objects cleanly.

---

### Ticket TCK-004: Stateless Router Layer Refactoring
- **Summary:** Refactor `app/routers/task.py` to use `TaskService` exclusively.
- **Layer:** `app/routers/task.py`
- **Priority:** High
- **Acceptance Criteria:**
  1. Router functions MUST NOT import `AsyncSession` or SQLAlchemy `select`.
  2. Router injects `TaskService` using FastAPI `Depends()`.
  3. Endpoints return valid HTTP status codes (`201`, `200`, `204`, `404`).

---

### Ticket TCK-005: Clean Architecture Test Suite Alignment
- **Summary:** Update integration and unit tests to validate the 3-tier structure.
- **Layer:** `tests/test_api.py`, `tests/conftest.py`
- **Priority:** High
- **Acceptance Criteria:**
  1. Verify all 5 CRUD routes (`POST`, `GET list`, `GET id`, `PATCH`, `DELETE`).
  2. Test pagination and status filtering logic.
  3. Verify 404 behavior for invalid task IDs.
  4. Ensure 100% test pass rate with automated pytest hooks.
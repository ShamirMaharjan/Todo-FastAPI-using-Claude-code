# Product Requirements Document (PRD)

## 1. Product Overview
The **FastAPI Task Management REST API** is an enterprise-grade, asynchronous backend service built to handle personal and team task workflows. The application provides high-throughput, low-latency CRUD operations, granular query filtering, and strict data validation using modern Python asynchronous paradigms (`FastAPI`, `AsyncSQLAlchemy`, `Pydantic v2`, and `SQLite`).

---

## 2. Goals & Objectives
- **Domain Consolidation:** Eliminate legacy dual-entity models (`Todo` and `Task`) in favor of a single, unified `Task` domain.
- **Enterprise Architecture:** Shift from monolithic route handlers to a clean 3-tier architecture (**Router → Service → Repository**).
- **Production Reliability:** Achieve 100% test coverage across all architectural layers with automated continuous testing hooks.
- **Developer Ergonomics:** Standardize codebase governance via `CLAUDE.md`, custom skills, and lifecycle hooks.

---

## 3. Functional Requirements

### FR-1: Task Lifecycle Management
- **Create Task:** `POST /tasks/` accepts a task payload, validates input, assigns defaults, and returns a fully serialized task item (`201 Created`).
- **List Tasks:** `GET /tasks/` retrieves tasks with optional filtering by `completed` status (`true`/`false`) and pagination support (`limit`, `offset`).
- **Get Task by ID:** `GET /tasks/{id}` returns details for a specific task. Returns `404 Not Found` if the task does not exist.
- **Update Task:** `PATCH /tasks/{id}` performs partial updates on task fields (title, description, completion status).
- **Delete Task:** `DELETE /tasks/{id}` removes a task item from storage (`204 No Content`). Returns `404 Not Found` if missing.

### FR-2: Input Validation & Schemas
- **Title:** Required, string, 1 to 255 characters.
- **Description:** Optional, string, max 2000 characters.
- **Priority:** Optional, string, max 50 characters, default `"MEDIUM"`.
- **Completed:** Optional, boolean, default `False`.
- **Extra Fields Handling:** Reject unknown query parameters or body fields strictly (`extra="forbid"`).

### FR-3: System Health Checks
- **Health Endpoint:** `GET /health` returns operational status (`"status": "ok"`), database connection check, and timestamp.

---

## 4. Non-Functional Requirements

### NFR-1: Performance & Latency
- Read/write API operations must process within **< 50ms** under normal load.
- Asynchronous non-blocking database queries via `AsyncSession` and `aiosqlite`.

### NFR-2: Maintainability & Quality
- Strict separation of concerns (Routers contain zero SQL logic).
- Mandatory Python 3.10+ static typing and standard docstrings across all modules.

### NFR-3: Testability
- 100% passing automated test suite (`pytest`, `pytest-asyncio`, `httpx.AsyncClient`).
- In-memory database isolation per test run
# Security and Access Document (SAD)

## 1. Threat Vectors & Protection Mechanisms

### 1.1 Parameter Pollution & Payload Manipulation
- **Mitigation:** All request schemas leverage Pydantic v2 with `extra="forbid"`. Any unexpected JSON fields submitted by a client trigger an instant `422 Unprocessable Entity` validation error, preventing parameter injection attacks.

### 1.2 SQL Injection (SQLi)
- **Mitigation:** Direct raw SQL string building is strictly forbidden across all modules. Data persistence is managed exclusively via SQLAlchemy 2.0 object-relational mappings and parameterized statements (`select(Task).where(...)`).

### 1.3 Denial of Service (DoS) & Memory Overload
- **Mitigation:** List endpoints (`GET /tasks/`) enforce default pagination thresholds (`limit: int = Query(100, le=100)`). Unbounded fetch queries are prohibited at the repository layer.

---

## 2. API Error Handling & Disclosure Prevention

- **Standardized Error Responses:** Exceptions raised by the Service layer (e.g., `TaskNotFoundException`) map cleanly to standard HTTP status codes (`404`, `400`, `422`) via FastAPI exception handlers.
- **Trace Masking:** Internal database errors and stack traces are suppressed in non-debug modes to prevent schema exposure.

---

## 3. CORS & Middleware Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

def setup_security_middleware(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production environment
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )
```

---

## 4. Authentication Architecture Roadmap (Future Integration)

The current stateless service-repository structure allows seamless integration of JWT / OAuth2 authentication:
1. Inject `get_current_user` dependency in router handlers.
2. Pass `user_id` context into `TaskService` and `TaskRepository`.
3. Enforce tenant isolation (`WHERE tasks.user_id = :user_id`) in all SQL queries.
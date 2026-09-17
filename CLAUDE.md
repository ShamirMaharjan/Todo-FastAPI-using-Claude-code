# FastAPI Industrial Coding Standards

## Architecture & Layers
- Layered Separation: Routers MUST NOT import `AsyncSession` or execute direct SQLAlchemy queries.
- Flow: `Router (HTTP) -> Service (Business Logic) -> Repository (Database Access) -> Model`.
- Statelessness: Keep route handlers strictly stateless. Depend on injected Services/Repositories.

## Coding Style
- Pydantic v2 for DTOs/Schemas (use `model_config = ConfigDict(extra="forbid")`).
- SQLAlchemy 2.0 async style for models (`Mapped` and `mapped_column`).
- Type Hints: Mandatory type annotations across all function arguments and returns.

## Testing & Quality
- All endpoints must have corresponding integration tests in `tests/`.
- Use `httpx.AsyncClient` for testing async endpoints with `pytest-asyncio`.
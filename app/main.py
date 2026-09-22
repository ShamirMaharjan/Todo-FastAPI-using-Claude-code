"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse

from .database import Base
from .database import engine
from .routers import auth_router
from .routers import task_router
from .services.task_service import TaskNotFoundError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler.

    Creates database tables on startup and disposes the engine on shutdown.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="FastAPI Todo",
    description="A simple Todo API built with FastAPI, async SQLAlchemy, "
    "and PostgreSQL.",
    version="0.1.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(auth_router)
app.include_router(task_router)


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(
    request: Request, exc: TaskNotFoundError
) -> JSONResponse:
    """Translate ``TaskNotFoundError`` into a 404 HTTP response."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"Task with id {exc.task_id} not found"},
    )


@app.get("/", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A dictionary with a status message indicating the server is running.
    """
    return {"status": "ok"}


@app.get("/info", tags=["info"])
async def info() -> dict[str, str]:
    """Application information endpoint.

    Returns:
        A dictionary containing the application name and version.
    """
    return {
        "app": "FastAPI Todo",
        "version": app.version,
    }

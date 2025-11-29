"""FastAPI Application Entry Point.

Main application configuration with routers, middleware, and exception handlers.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routers import (
    health_router,
    keywords_router,
    pages_router,
    scans_router,
)
from src.app.api.exceptions import register_exception_handlers
from src.app.infrastructure.settings.runtime_settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    print(f"Starting {settings.name} v{settings.version} ({settings.environment})")
    yield
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.name,
        description="Meta Ads Intelligence Platform - Track and analyze Shopify stores via Meta Ads",
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include routers
    app.include_router(health_router)
    app.include_router(keywords_router, prefix="/api/v1")
    app.include_router(pages_router, prefix="/api/v1")
    app.include_router(scans_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_app()

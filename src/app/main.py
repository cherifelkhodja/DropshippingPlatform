"""FastAPI Application Entry Point.

Main application configuration with routers, middleware, and exception handlers.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routers import (
    admin_router,
    health_router,
    keywords_router,
    pages_router,
    scans_router,
)
from src.app.api.exceptions import register_exception_handlers
from src.app.infrastructure.logging.config import configure_logging
from src.app.infrastructure.settings.runtime_settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler.

    Handles startup and shutdown events.
    Creates shared HTTP session for all external API calls.
    """
    settings = get_settings()

    # Configure logging at startup
    configure_logging(level=settings.log_level)

    logger.info(
        "Starting application",
        extra={
            "name": settings.name,
            "version": settings.version,
            "environment": settings.environment,
        },
    )

    # Create shared HTTP session
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
    timeout = aiohttp.ClientTimeout(total=settings.scraper.default_timeout)
    headers = {"User-Agent": settings.scraper.user_agent}

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers,
    ) as http_session:
        # Store in app.state for dependency injection
        app.state.http_session = http_session
        logger.info("HTTP session initialized")

        yield

        # Cleanup on shutdown
        logger.info("Shutting down application")


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
    app.include_router(admin_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_app()

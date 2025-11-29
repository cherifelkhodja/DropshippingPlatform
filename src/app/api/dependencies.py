"""FastAPI Dependency Injection.

Provides dependencies for routers including database sessions,
repositories, and use cases.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated, Any

import aiohttp
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.infrastructure.db.database import Database, DatabaseConfig
from src.app.infrastructure.settings.runtime_settings import AppSettings, get_settings

from src.app.adapters.outbound.repositories.page_repository import (
    PostgresPageRepository,
)
from src.app.adapters.outbound.repositories.ads_repository import PostgresAdsRepository
from src.app.adapters.outbound.repositories.scan_repository import (
    PostgresScanRepository,
)
from src.app.adapters.outbound.repositories.keyword_run_repository import (
    PostgresKeywordRunRepository,
)
from src.app.adapters.outbound.meta.meta_ads_client import MetaAdsClient
from src.app.adapters.outbound.scraper.html_scraper import HtmlScraperClient
from src.app.adapters.outbound.sitemap.sitemap_client import SitemapClient
from src.app.adapters.outbound.tasks.celery_task_dispatcher import CeleryTaskDispatcher
from src.app.infrastructure.celery.celery_app import celery_app

from src.app.core.usecases.search_ads_by_keyword import SearchAdsByKeywordUseCase
from src.app.core.usecases.compute_page_active_ads_count import (
    ComputePageActiveAdsCountUseCase,
)
from src.app.core.usecases.analyse_website import AnalyseWebsiteUseCase
from src.app.core.usecases.analyse_page_deep import AnalysePageDeepUseCase
from src.app.core.usecases.extract_product_count import ExtractProductCountUseCase


# =============================================================================
# Settings
# =============================================================================


def get_app_settings() -> AppSettings:
    """Get application settings."""
    return get_settings()


# =============================================================================
# Database
# =============================================================================


@lru_cache
def get_database() -> Database:
    """Get cached database instance."""
    settings = get_settings()
    config = DatabaseConfig(
        url=settings.database.url,
        echo=settings.database.echo,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
    )
    return Database(config)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    Yields:
        AsyncSession: Database session that auto-closes.
    """
    database = get_database()
    async with database.session() as session:
        yield session


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
Settings = Annotated[AppSettings, Depends(get_app_settings)]


# =============================================================================
# Logger (Simple implementation for now)
# =============================================================================


class SimpleLogger:
    """Simple logger implementation for API layer."""

    def info(self, msg: str, **context: Any) -> None:
        """Log info message."""
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        print(f"INFO: {msg} {ctx}")

    def warning(self, msg: str, **context: Any) -> None:
        """Log warning message."""
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        print(f"WARNING: {msg} {ctx}")

    def error(self, msg: str, **context: Any) -> None:
        """Log error message."""
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        print(f"ERROR: {msg} {ctx}")

    def debug(self, msg: str, **context: Any) -> None:
        """Log debug message."""
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        print(f"DEBUG: {msg} {ctx}")

    def critical(self, msg: str, **context: Any) -> None:
        """Log critical message."""
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        print(f"CRITICAL: {msg} {ctx}")


@lru_cache
def get_logger() -> SimpleLogger:
    """Get logger instance."""
    return SimpleLogger()


# =============================================================================
# Repositories
# =============================================================================


def get_page_repository(session: DbSession) -> PostgresPageRepository:
    """Get page repository."""
    return PostgresPageRepository(session)


def get_ads_repository(session: DbSession) -> PostgresAdsRepository:
    """Get ads repository."""
    return PostgresAdsRepository(session)


def get_scan_repository(session: DbSession) -> PostgresScanRepository:
    """Get scan repository."""
    return PostgresScanRepository(session)


def get_keyword_run_repository(session: DbSession) -> PostgresKeywordRunRepository:
    """Get keyword run repository."""
    return PostgresKeywordRunRepository(session)


# Type aliases
PageRepo = Annotated[PostgresPageRepository, Depends(get_page_repository)]
AdsRepo = Annotated[PostgresAdsRepository, Depends(get_ads_repository)]
ScanRepo = Annotated[PostgresScanRepository, Depends(get_scan_repository)]
KeywordRunRepo = Annotated[
    PostgresKeywordRunRepository, Depends(get_keyword_run_repository)
]


# =============================================================================
# HTTP Session
# =============================================================================


def get_http_session(request: Request) -> aiohttp.ClientSession:
    """Get shared HTTP session from app.state.

    The session is created in the application lifespan (main.py)
    and stored in app.state.http_session.

    Args:
        request: FastAPI request object (provides access to app).

    Returns:
        aiohttp.ClientSession: Shared HTTP client session.
    """
    return request.app.state.http_session


HttpSession = Annotated[aiohttp.ClientSession, Depends(get_http_session)]


# =============================================================================
# External Clients
# =============================================================================


def get_meta_ads_client(
    http_session: HttpSession,
    settings: Settings,
) -> MetaAdsClient:
    """Get Meta Ads API client."""
    from src.app.adapters.outbound.meta.config import MetaAdsConfig

    config = MetaAdsConfig(
        access_token=settings.meta_ads.access_token.get_secret_value(),
        base_url=settings.meta_ads.base_url,
        api_version=settings.meta_ads.api_version,
        timeout_seconds=settings.meta_ads.timeout_seconds,
    )
    return MetaAdsClient(
        config=config,
        session=http_session,
        logger=get_logger(),
    )


def get_html_scraper(http_session: HttpSession) -> HtmlScraperClient:
    """Get HTML scraper client."""
    return HtmlScraperClient(
        session=http_session,
        logger=get_logger(),
    )


def get_sitemap_client(http_session: HttpSession) -> SitemapClient:
    """Get sitemap client."""
    return SitemapClient(
        session=http_session,
        logger=get_logger(),
    )


# =============================================================================
# Task Dispatcher
# =============================================================================


@lru_cache
def get_task_dispatcher() -> CeleryTaskDispatcher:
    """Get Celery task dispatcher.

    Returns a cached CeleryTaskDispatcher instance that uses
    the global celery_app for task dispatching.
    """
    import logging

    return CeleryTaskDispatcher(
        celery_app=celery_app,
        logger=logging.getLogger("celery.dispatcher"),
    )


TaskDispatcher = Annotated[CeleryTaskDispatcher, Depends(get_task_dispatcher)]


# =============================================================================
# Use Cases
# =============================================================================


def get_search_ads_use_case(
    session: DbSession,
    http_session: HttpSession,
    settings: Settings,
) -> SearchAdsByKeywordUseCase:
    """Get SearchAdsByKeyword use case."""
    return SearchAdsByKeywordUseCase(
        meta_ads_port=get_meta_ads_client(http_session, settings),
        page_repository=PostgresPageRepository(session),
        keyword_run_repository=PostgresKeywordRunRepository(session),
        logger=get_logger(),
    )


def get_compute_ads_count_use_case(
    session: DbSession,
    http_session: HttpSession,
    settings: Settings,
) -> ComputePageActiveAdsCountUseCase:
    """Get ComputePageActiveAdsCount use case."""
    return ComputePageActiveAdsCountUseCase(
        meta_ads_port=get_meta_ads_client(http_session, settings),
        page_repository=PostgresPageRepository(session),
        logger=get_logger(),
    )


def get_analyse_website_use_case(
    session: DbSession,
    http_session: HttpSession,
) -> AnalyseWebsiteUseCase:
    """Get AnalyseWebsite use case."""
    return AnalyseWebsiteUseCase(
        html_scraper=get_html_scraper(http_session),
        page_repository=PostgresPageRepository(session),
        task_dispatcher=get_task_dispatcher(),
        logger=get_logger(),
    )


def get_analyse_page_deep_use_case(
    session: DbSession,
    http_session: HttpSession,
    settings: Settings,
) -> AnalysePageDeepUseCase:
    """Get AnalysePageDeep use case."""
    return AnalysePageDeepUseCase(
        meta_ads_port=get_meta_ads_client(http_session, settings),
        ads_repository=PostgresAdsRepository(session),
        scan_repository=PostgresScanRepository(session),
        page_repository=PostgresPageRepository(session),
        task_dispatcher=get_task_dispatcher(),
        logger=get_logger(),
    )


def get_extract_product_count_use_case(
    session: DbSession,
    http_session: HttpSession,
) -> ExtractProductCountUseCase:
    """Get ExtractProductCount use case."""
    return ExtractProductCountUseCase(
        page_repository=PostgresPageRepository(session),
        sitemap_port=get_sitemap_client(http_session),
        logger=get_logger(),
    )


# Type aliases for use cases
SearchAdsUseCase = Annotated[
    SearchAdsByKeywordUseCase,
    Depends(get_search_ads_use_case),
]
ComputeAdsCountUseCase = Annotated[
    ComputePageActiveAdsCountUseCase,
    Depends(get_compute_ads_count_use_case),
]
AnalyseWebsiteUC = Annotated[
    AnalyseWebsiteUseCase,
    Depends(get_analyse_website_use_case),
]
AnalysePageDeepUC = Annotated[
    AnalysePageDeepUseCase,
    Depends(get_analyse_page_deep_use_case),
]
ExtractProductCountUC = Annotated[
    ExtractProductCountUseCase,
    Depends(get_extract_product_count_use_case),
]

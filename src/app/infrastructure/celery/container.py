"""Celery Worker Dependency Container.

Provides dependency injection for Celery workers, mirroring the API layer DI
but in a synchronous context suitable for Celery task execution.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiohttp
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.adapters.outbound.meta.config import MetaAdsConfig
from src.app.adapters.outbound.meta.meta_ads_client import MetaAdsClient
from src.app.adapters.outbound.repositories.ads_repository import PostgresAdsRepository
from src.app.adapters.outbound.repositories.page_repository import (
    PostgresPageRepository,
)
from src.app.adapters.outbound.repositories.scan_repository import (
    PostgresScanRepository,
)
from src.app.adapters.outbound.repositories.scoring_repository import (
    PostgresScoringRepository,
)
from src.app.adapters.outbound.scraper.html_scraper import HtmlScraperClient
from src.app.adapters.outbound.sitemap.sitemap_client import SitemapClient
from src.app.adapters.outbound.tasks.celery_task_dispatcher import CeleryTaskDispatcher
from src.app.adapters.outbound.repositories.watchlist_repository import (
    PostgresWatchlistRepository,
)
from src.app.adapters.outbound.repositories.alert_repository import (
    PostgresAlertRepository,
)
from src.app.core.usecases.analyse_page_deep import AnalysePageDeepUseCase
from src.app.core.usecases.analyse_website import AnalyseWebsiteUseCase
from src.app.core.usecases.compute_shop_score import ComputeShopScoreUseCase
from src.app.core.usecases.extract_product_count import ExtractProductCountUseCase
from src.app.core.usecases.watchlists import RescoreWatchlistUseCase
from src.app.core.usecases.detect_alerts_for_page import DetectAlertsForPageUseCase
from src.app.infrastructure.logging.logger_adapter import StandardLoggingAdapter
from src.app.infrastructure.settings.runtime_settings import get_settings

logger = logging.getLogger(__name__)


class WorkerContainer:
    """Dependency container for Celery worker tasks.

    Manages database connections, HTTP sessions, and use case instances
    for executing tasks within Celery workers.

    This class provides a clean way to construct all dependencies needed
    by use cases without coupling the task definitions to infrastructure.
    """

    def __init__(self) -> None:
        """Initialize the worker container with settings."""
        self._settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def _get_engine(self) -> AsyncEngine:
        """Get or create the async database engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine instance.
        """
        if self._engine is None:
            self._engine = create_async_engine(
                self._settings.database.url,
                echo=self._settings.database.echo,
                pool_size=self._settings.database.pool_size,
                max_overflow=self._settings.database.max_overflow,
            )
        return self._engine

    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory.

        Returns:
            async_sessionmaker: Factory for creating async sessions.
        """
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self._get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory

    @asynccontextmanager
    async def _session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new database session.

        Yields:
            AsyncSession: A new database session with auto-commit/rollback.
        """
        session = self._get_session_factory()()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def _http_session(self) -> AsyncGenerator[aiohttp.ClientSession, None]:
        """Create a new HTTP session.

        Yields:
            aiohttp.ClientSession: HTTP client session for external requests.
        """
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=self._settings.scraper.default_timeout)
        headers = {"User-Agent": self._settings.scraper.user_agent}

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
        ) as session:
            yield session

    def _get_logger(self, name: str) -> StandardLoggingAdapter:
        """Get a logger adapter for the specified name.

        Args:
            name: Logger name for categorization.

        Returns:
            StandardLoggingAdapter: Logging port implementation.
        """
        return StandardLoggingAdapter(logging.getLogger(name))

    def _get_meta_ads_client(
        self,
        http_session: aiohttp.ClientSession,
    ) -> MetaAdsClient:
        """Create a Meta Ads client.

        Args:
            http_session: HTTP session for API calls.

        Returns:
            MetaAdsClient: Meta Ads API client.
        """
        config = MetaAdsConfig(
            access_token=self._settings.meta_ads.access_token.get_secret_value(),
            base_url=self._settings.meta_ads.base_url,
            api_version=self._settings.meta_ads.api_version,
            timeout_seconds=self._settings.meta_ads.timeout_seconds,
        )
        return MetaAdsClient(
            config=config,
            session=http_session,
            logger=self._get_logger("meta_ads"),
        )

    def _get_html_scraper(
        self,
        http_session: aiohttp.ClientSession,
    ) -> HtmlScraperClient:
        """Create an HTML scraper client.

        Args:
            http_session: HTTP session for scraping.

        Returns:
            HtmlScraperClient: HTML scraper implementation.
        """
        return HtmlScraperClient(
            session=http_session,
            logger=self._get_logger("html_scraper"),
        )

    def _get_sitemap_client(
        self,
        http_session: aiohttp.ClientSession,
    ) -> SitemapClient:
        """Create a sitemap client.

        Args:
            http_session: HTTP session for fetching sitemaps.

        Returns:
            SitemapClient: Sitemap parser implementation.
        """
        return SitemapClient(
            session=http_session,
            logger=self._get_logger("sitemap"),
        )

    def _get_task_dispatcher(self) -> CeleryTaskDispatcher:
        """Get the Celery task dispatcher.

        Returns:
            CeleryTaskDispatcher: Task dispatcher for chaining tasks.
        """
        from src.app.infrastructure.celery.celery_app import celery_app

        return CeleryTaskDispatcher(
            celery_app=celery_app,
            logger=logging.getLogger("celery.dispatcher"),
        )

    async def get_analyse_page_deep_use_case(
        self,
        db_session: AsyncSession,
        http_session: aiohttp.ClientSession,
    ) -> AnalysePageDeepUseCase:
        """Create the AnalysePageDeep use case with all dependencies.

        Args:
            db_session: Database session for repositories.
            http_session: HTTP session for external API calls.

        Returns:
            AnalysePageDeepUseCase: Configured use case instance.
        """
        return AnalysePageDeepUseCase(
            meta_ads_port=self._get_meta_ads_client(http_session),
            ads_repository=PostgresAdsRepository(db_session),
            scan_repository=PostgresScanRepository(db_session),
            page_repository=PostgresPageRepository(db_session),
            task_dispatcher=self._get_task_dispatcher(),
            logger=self._get_logger("analyse_page_deep"),
        )

    async def get_analyse_website_use_case(
        self,
        db_session: AsyncSession,
        http_session: aiohttp.ClientSession,
    ) -> AnalyseWebsiteUseCase:
        """Create the AnalyseWebsite use case with all dependencies.

        Args:
            db_session: Database session for repositories.
            http_session: HTTP session for scraping.

        Returns:
            AnalyseWebsiteUseCase: Configured use case instance.
        """
        return AnalyseWebsiteUseCase(
            html_scraper=self._get_html_scraper(http_session),
            page_repository=PostgresPageRepository(db_session),
            task_dispatcher=self._get_task_dispatcher(),
            logger=self._get_logger("analyse_website"),
        )

    async def get_extract_product_count_use_case(
        self,
        db_session: AsyncSession,
        http_session: aiohttp.ClientSession,
    ) -> ExtractProductCountUseCase:
        """Create the ExtractProductCount use case with all dependencies.

        Args:
            db_session: Database session for repositories.
            http_session: HTTP session for sitemap fetching.

        Returns:
            ExtractProductCountUseCase: Configured use case instance.
        """
        return ExtractProductCountUseCase(
            page_repository=PostgresPageRepository(db_session),
            sitemap_port=self._get_sitemap_client(http_session),
            logger=self._get_logger("extract_product_count"),
        )

    async def get_compute_shop_score_use_case(
        self,
        db_session: AsyncSession,
    ) -> ComputeShopScoreUseCase:
        """Create the ComputeShopScore use case with all dependencies.

        Args:
            db_session: Database session for repositories.

        Returns:
            ComputeShopScoreUseCase: Configured use case instance.
        """
        return ComputeShopScoreUseCase(
            page_repository=PostgresPageRepository(db_session),
            ads_repository=PostgresAdsRepository(db_session),
            scoring_repository=PostgresScoringRepository(db_session),
            logger=self._get_logger("compute_shop_score"),
        )

    async def get_rescore_watchlist_use_case(
        self,
        db_session: AsyncSession,
    ) -> RescoreWatchlistUseCase:
        """Create the RescoreWatchlist use case with all dependencies.

        Args:
            db_session: Database session for repositories.

        Returns:
            RescoreWatchlistUseCase: Configured use case instance.
        """
        return RescoreWatchlistUseCase(
            watchlist_repository=PostgresWatchlistRepository(db_session),
            task_dispatcher=self._get_task_dispatcher(),
            logger=self._get_logger("rescore_watchlist"),
        )

    async def get_detect_alerts_for_page_use_case(
        self,
        db_session: AsyncSession,
    ) -> DetectAlertsForPageUseCase:
        """Create the DetectAlertsForPage use case with all dependencies.

        Args:
            db_session: Database session for repositories.

        Returns:
            DetectAlertsForPageUseCase: Configured use case instance.
        """
        return DetectAlertsForPageUseCase(
            alert_repository=PostgresAlertRepository(db_session),
            logger=self._get_logger("detect_alerts"),
        )

    @asynccontextmanager
    async def execution_context(
        self,
    ) -> AsyncGenerator[
        tuple[AsyncSession, aiohttp.ClientSession],
        None,
    ]:
        """Create an execution context with database and HTTP sessions.

        Provides both sessions needed for use case execution within
        a properly managed context.

        Yields:
            Tuple of (db_session, http_session) for use case execution.
        """
        async with self._session() as db_session:
            async with self._http_session() as http_session:
                yield db_session, http_session

    async def cleanup(self) -> None:
        """Clean up resources (engine disposal)."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global container instance for worker tasks
_container: WorkerContainer | None = None


def get_container() -> WorkerContainer:
    """Get or create the global worker container.

    Returns:
        WorkerContainer: Singleton container instance.
    """
    global _container
    if _container is None:
        _container = WorkerContainer()
    return _container

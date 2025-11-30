"""FastAPI Dependency Injection.

Provides dependencies for routers including database sessions,
repositories, and use cases.

DI Architecture:
    - Settings: Cached globally via lru_cache
    - Database: Cached Database instance, sessions per request
    - Repositories: Created per request with injected session
    - External Clients: Created per request with injected HTTP session
    - Use Cases: Composed from injected repositories and clients
    - Logger: StandardLoggingAdapter wrapping Python logging
"""

import logging
from collections.abc import AsyncGenerator
from functools import lru_cache
from typing import Annotated

import aiohttp
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.adapters.outbound.meta.meta_ads_client import MetaAdsClient
from src.app.adapters.outbound.repositories.ads_repository import PostgresAdsRepository
from src.app.adapters.outbound.repositories.keyword_run_repository import (
    PostgresKeywordRunRepository,
)
from src.app.adapters.outbound.repositories.page_repository import (
    PostgresPageRepository,
)
from src.app.adapters.outbound.repositories.scan_repository import (
    PostgresScanRepository,
)
from src.app.adapters.outbound.repositories.scoring_repository import (
    PostgresScoringRepository,
)
from src.app.adapters.outbound.repositories.watchlist_repository import (
    PostgresWatchlistRepository,
)
from src.app.adapters.outbound.repositories.alert_repository import (
    PostgresAlertRepository,
)
from src.app.adapters.outbound.repositories.product_repository import (
    PostgresProductRepository,
)
from src.app.adapters.outbound.repositories.page_metrics_repository import (
    PostgresPageMetricsRepository,
)
from src.app.adapters.outbound.repositories.creative_analysis_repository import (
    PostgresCreativeAnalysisRepository,
)
from src.app.adapters.outbound.creative_text_analyzer import HeuristicCreativeTextAnalyzer
from src.app.adapters.outbound.scraper.html_scraper import HtmlScraperClient
from src.app.adapters.outbound.product_extractor.shopify_product_extractor import (
    ShopifyProductExtractor,
)
from src.app.adapters.outbound.sitemap.sitemap_client import SitemapClient
from src.app.adapters.outbound.tasks.celery_task_dispatcher import CeleryTaskDispatcher
from src.app.core.ports.repository_port import (
    PageRepository,
    AdsRepository,
    ScanRepository,
    KeywordRunRepository,
    ScoringRepository,
    WatchlistRepository,
    AlertRepository,
    ProductRepository,
    PageMetricsRepository,
    CreativeAnalysisRepository,
)
from src.app.core.ports.creative_text_analyzer_port import CreativeTextAnalyzerPort
from src.app.core.ports.task_dispatcher_port import TaskDispatcherPort
from src.app.core.usecases.analyse_page_deep import AnalysePageDeepUseCase
from src.app.core.usecases.analyse_website import AnalyseWebsiteUseCase
from src.app.core.usecases.compute_page_active_ads_count import (
    ComputePageActiveAdsCountUseCase,
)
from src.app.core.usecases.compute_shop_score import ComputeShopScoreUseCase
from src.app.core.usecases.get_ranked_shops import GetRankedShopsUseCase
from src.app.core.usecases.extract_product_count import ExtractProductCountUseCase
from src.app.core.usecases.search_ads_by_keyword import SearchAdsByKeywordUseCase
from src.app.core.usecases.sync_products_for_page import SyncProductsForPageUseCase
from src.app.core.usecases.build_product_insights import BuildProductInsightsForPageUseCase
from src.app.core.usecases.metrics import GetPageMetricsHistoryUseCase
from src.app.core.usecases.creative_insights import BuildPageCreativeInsightsUseCase
from src.app.core.usecases.watchlists import (
    CreateWatchlistUseCase,
    GetWatchlistUseCase,
    ListWatchlistsUseCase,
    AddPageToWatchlistUseCase,
    RemovePageFromWatchlistUseCase,
    ListWatchlistItemsUseCase,
    RescoreWatchlistUseCase,
)
from src.app.core.usecases.watchlist_details import (
    GetWatchlistWithDetailsUseCase,
    ListWatchlistsWithCountsUseCase,
    GetPageWatchlistsUseCase,
)
from src.app.core.usecases.monitoring import GetMonitoringSummaryUseCase
from src.app.infrastructure.celery.celery_app import celery_app
from src.app.infrastructure.db.database import Database, DatabaseConfig
from src.app.infrastructure.logging.logger_adapter import StandardLoggingAdapter
from src.app.infrastructure.settings.runtime_settings import AppSettings, get_settings


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
# Logger
# =============================================================================


def get_logger(name: str = "api") -> StandardLoggingAdapter:
    """Get a logger adapter for the specified name.

    Args:
        name: Logger name for categorization. Defaults to "api".

    Returns:
        StandardLoggingAdapter implementing LoggingPort.
    """
    return StandardLoggingAdapter(logging.getLogger(name))


# =============================================================================
# Admin Authentication
# =============================================================================


def get_admin_auth(
    settings: AppSettings = Depends(get_app_settings),
    x_admin_api_key: str | None = Header(default=None, alias="X-Admin-Api-Key"),
) -> None:
    """Validate admin API key authentication.

    This dependency validates the X-Admin-Api-Key header against
    the configured admin_api_key in settings.

    If no admin_api_key is configured in settings, the endpoint
    is accessible without authentication (development mode).

    Args:
        settings: Application settings (injected).
        x_admin_api_key: API key from X-Admin-Api-Key header (injected).

    Raises:
        HTTPException: 401 if key is missing or invalid when auth is configured.
    """
    # Skip auth if no admin key is configured (dev mode)
    if not settings.security.admin_api_key:
        return

    if not x_admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Admin-Api-Key header",
        )

    if x_admin_api_key != settings.security.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key",
        )


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


def get_scoring_repository(session: DbSession) -> PostgresScoringRepository:
    """Get scoring repository."""
    return PostgresScoringRepository(session)


# Type aliases - using Protocol interfaces for decoupling
PageRepo = Annotated[PageRepository, Depends(get_page_repository)]
AdsRepo = Annotated[AdsRepository, Depends(get_ads_repository)]
ScanRepo = Annotated[ScanRepository, Depends(get_scan_repository)]
KeywordRunRepo = Annotated[KeywordRunRepository, Depends(get_keyword_run_repository)]
ScoringRepo = Annotated[ScoringRepository, Depends(get_scoring_repository)]


def get_watchlist_repository(session: DbSession) -> PostgresWatchlistRepository:
    """Get watchlist repository."""
    return PostgresWatchlistRepository(session)


WatchlistRepo = Annotated[WatchlistRepository, Depends(get_watchlist_repository)]


def get_alert_repository(session: DbSession) -> PostgresAlertRepository:
    """Get alert repository."""
    return PostgresAlertRepository(session)


AlertRepo = Annotated[AlertRepository, Depends(get_alert_repository)]


def get_product_repository(session: DbSession) -> PostgresProductRepository:
    """Get product repository."""
    return PostgresProductRepository(session)


ProductRepo = Annotated[ProductRepository, Depends(get_product_repository)]


def get_page_metrics_repository(session: DbSession) -> PostgresPageMetricsRepository:
    """Get page metrics repository."""
    return PostgresPageMetricsRepository(session)


PageMetricsRepo = Annotated[PageMetricsRepository, Depends(get_page_metrics_repository)]


def get_creative_analysis_repository(session: DbSession) -> PostgresCreativeAnalysisRepository:
    """Get creative analysis repository."""
    return PostgresCreativeAnalysisRepository(session)


CreativeAnalysisRepo = Annotated[
    CreativeAnalysisRepository,
    Depends(get_creative_analysis_repository),
]


def get_creative_text_analyzer() -> HeuristicCreativeTextAnalyzer:
    """Get creative text analyzer (V1 heuristic implementation)."""
    return HeuristicCreativeTextAnalyzer()


CreativeTextAnalyzer = Annotated[
    CreativeTextAnalyzerPort,
    Depends(get_creative_text_analyzer),
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


def get_product_extractor(http_session: HttpSession) -> ShopifyProductExtractor:
    """Get Shopify product extractor."""
    return ShopifyProductExtractor(
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


# Type alias using Protocol interface for decoupling
TaskDispatcher = Annotated[TaskDispatcherPort, Depends(get_task_dispatcher)]


# =============================================================================
# Use Cases
# =============================================================================


def get_search_ads_use_case(
    page_repo: PageRepo,
    keyword_run_repo: KeywordRunRepo,
    http_session: HttpSession,
    settings: Settings,
) -> SearchAdsByKeywordUseCase:
    """Get SearchAdsByKeyword use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return SearchAdsByKeywordUseCase(
        meta_ads_port=get_meta_ads_client(http_session, settings),
        page_repository=page_repo,
        keyword_run_repository=keyword_run_repo,
        logger=get_logger("usecase.search_ads"),
    )


def get_compute_ads_count_use_case(
    page_repo: PageRepo,
    http_session: HttpSession,
    settings: Settings,
) -> ComputePageActiveAdsCountUseCase:
    """Get ComputePageActiveAdsCount use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return ComputePageActiveAdsCountUseCase(
        meta_ads_port=get_meta_ads_client(http_session, settings),
        page_repository=page_repo,
        logger=get_logger("usecase.compute_ads_count"),
    )


def get_analyse_website_use_case(
    page_repo: PageRepo,
    http_session: HttpSession,
) -> AnalyseWebsiteUseCase:
    """Get AnalyseWebsite use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return AnalyseWebsiteUseCase(
        html_scraper=get_html_scraper(http_session),
        page_repository=page_repo,
        task_dispatcher=get_task_dispatcher(),
        logger=get_logger("usecase.analyse_website"),
    )


def get_analyse_page_deep_use_case(
    page_repo: PageRepo,
    ads_repo: AdsRepo,
    scan_repo: ScanRepo,
    http_session: HttpSession,
    settings: Settings,
) -> AnalysePageDeepUseCase:
    """Get AnalysePageDeep use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return AnalysePageDeepUseCase(
        meta_ads_port=get_meta_ads_client(http_session, settings),
        ads_repository=ads_repo,
        scan_repository=scan_repo,
        page_repository=page_repo,
        task_dispatcher=get_task_dispatcher(),
        logger=get_logger("usecase.analyse_page_deep"),
    )


def get_extract_product_count_use_case(
    page_repo: PageRepo,
    http_session: HttpSession,
) -> ExtractProductCountUseCase:
    """Get ExtractProductCount use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return ExtractProductCountUseCase(
        page_repository=page_repo,
        sitemap_port=get_sitemap_client(http_session),
        logger=get_logger("usecase.extract_product_count"),
    )


def get_compute_shop_score_use_case(
    page_repo: PageRepo,
    ads_repo: AdsRepo,
    scoring_repo: ScoringRepo,
) -> ComputeShopScoreUseCase:
    """Get ComputeShopScore use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return ComputeShopScoreUseCase(
        page_repository=page_repo,
        ads_repository=ads_repo,
        scoring_repository=scoring_repo,
        logger=get_logger("usecase.compute_shop_score"),
    )


def get_ranked_shops_use_case(
    scoring_repo: ScoringRepo,
) -> GetRankedShopsUseCase:
    """Get GetRankedShops use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return GetRankedShopsUseCase(
        scoring_repository=scoring_repo,
        logger=get_logger("usecase.get_ranked_shops"),
    )


def get_sync_products_use_case(
    page_repo: PageRepo,
    product_repo: ProductRepo,
    http_session: HttpSession,
) -> SyncProductsForPageUseCase:
    """Get SyncProductsForPage use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return SyncProductsForPageUseCase(
        page_repository=page_repo,
        product_repository=product_repo,
        product_extractor=get_product_extractor(http_session),
        logger=get_logger("usecase.sync_products"),
    )


def get_build_product_insights_use_case(
    page_repo: PageRepo,
    product_repo: ProductRepo,
    ads_repo: AdsRepo,
) -> BuildProductInsightsForPageUseCase:
    """Get BuildProductInsightsForPage use case.

    Uses injected repository dependencies for cleaner composition.
    """
    return BuildProductInsightsForPageUseCase(
        page_repository=page_repo,
        product_repository=product_repo,
        ads_repository=ads_repo,
        logger=get_logger("usecase.build_product_insights"),
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
ComputeShopScoreUC = Annotated[
    ComputeShopScoreUseCase,
    Depends(get_compute_shop_score_use_case),
]
GetRankedShopsUC = Annotated[
    GetRankedShopsUseCase,
    Depends(get_ranked_shops_use_case),
]
SyncProductsUC = Annotated[
    SyncProductsForPageUseCase,
    Depends(get_sync_products_use_case),
]
BuildProductInsightsUC = Annotated[
    BuildProductInsightsForPageUseCase,
    Depends(get_build_product_insights_use_case),
]


def get_build_page_creative_insights_use_case(
    page_repo: PageRepo,
    ads_repo: AdsRepo,
    creative_analysis_repo: CreativeAnalysisRepo,
    text_analyzer: CreativeTextAnalyzer,
) -> BuildPageCreativeInsightsUseCase:
    """Get BuildPageCreativeInsights use case.

    Uses injected repository and analyzer dependencies for cleaner composition.
    """
    return BuildPageCreativeInsightsUseCase(
        page_repository=page_repo,
        ads_repository=ads_repo,
        creative_analysis_repository=creative_analysis_repo,
        text_analyzer=text_analyzer,
        logger=get_logger("usecase.creative_insights"),
    )


BuildPageCreativeInsightsUC = Annotated[
    BuildPageCreativeInsightsUseCase,
    Depends(get_build_page_creative_insights_use_case),
]


# =============================================================================
# Watchlist Use Cases
# =============================================================================


def get_create_watchlist_use_case(
    watchlist_repo: WatchlistRepo,
) -> CreateWatchlistUseCase:
    """Get CreateWatchlist use case."""
    return CreateWatchlistUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.create_watchlist"),
    )


def get_get_watchlist_use_case(
    watchlist_repo: WatchlistRepo,
) -> GetWatchlistUseCase:
    """Get GetWatchlist use case."""
    return GetWatchlistUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.get_watchlist"),
    )


def get_list_watchlists_use_case(
    watchlist_repo: WatchlistRepo,
) -> ListWatchlistsUseCase:
    """Get ListWatchlists use case."""
    return ListWatchlistsUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.list_watchlists"),
    )


def get_add_page_to_watchlist_use_case(
    watchlist_repo: WatchlistRepo,
) -> AddPageToWatchlistUseCase:
    """Get AddPageToWatchlist use case."""
    return AddPageToWatchlistUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.add_page_to_watchlist"),
    )


def get_remove_page_from_watchlist_use_case(
    watchlist_repo: WatchlistRepo,
) -> RemovePageFromWatchlistUseCase:
    """Get RemovePageFromWatchlist use case."""
    return RemovePageFromWatchlistUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.remove_page_from_watchlist"),
    )


def get_list_watchlist_items_use_case(
    watchlist_repo: WatchlistRepo,
) -> ListWatchlistItemsUseCase:
    """Get ListWatchlistItems use case."""
    return ListWatchlistItemsUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.list_watchlist_items"),
    )


def get_rescore_watchlist_use_case(
    watchlist_repo: WatchlistRepo,
    task_dispatcher: TaskDispatcher,
) -> RescoreWatchlistUseCase:
    """Get RescoreWatchlist use case."""
    return RescoreWatchlistUseCase(
        watchlist_repository=watchlist_repo,
        task_dispatcher=task_dispatcher,
        logger=get_logger("usecase.rescore_watchlist"),
    )


# Type aliases for watchlist use cases
CreateWatchlistUC = Annotated[
    CreateWatchlistUseCase,
    Depends(get_create_watchlist_use_case),
]
GetWatchlistUC = Annotated[
    GetWatchlistUseCase,
    Depends(get_get_watchlist_use_case),
]
ListWatchlistsUC = Annotated[
    ListWatchlistsUseCase,
    Depends(get_list_watchlists_use_case),
]
AddPageToWatchlistUC = Annotated[
    AddPageToWatchlistUseCase,
    Depends(get_add_page_to_watchlist_use_case),
]
RemovePageFromWatchlistUC = Annotated[
    RemovePageFromWatchlistUseCase,
    Depends(get_remove_page_from_watchlist_use_case),
]
ListWatchlistItemsUC = Annotated[
    ListWatchlistItemsUseCase,
    Depends(get_list_watchlist_items_use_case),
]
RescoreWatchlistUC = Annotated[
    RescoreWatchlistUseCase,
    Depends(get_rescore_watchlist_use_case),
]


# =============================================================================
# Metrics Use Cases
# =============================================================================


def get_page_metrics_history_use_case(
    page_repo: PageRepo,
    page_metrics_repo: PageMetricsRepo,
) -> GetPageMetricsHistoryUseCase:
    """Get GetPageMetricsHistory use case."""
    return GetPageMetricsHistoryUseCase(
        page_repository=page_repo,
        page_metrics_repository=page_metrics_repo,
        logger=get_logger("usecase.get_page_metrics_history"),
    )


GetPageMetricsHistoryUC = Annotated[
    GetPageMetricsHistoryUseCase,
    Depends(get_page_metrics_history_use_case),
]


# =============================================================================
# Extended Watchlist Use Cases (Sprint 8.1)
# =============================================================================


def get_watchlist_with_details_use_case(
    watchlist_repo: WatchlistRepo,
    page_repo: PageRepo,
    scoring_repo: ScoringRepo,
) -> GetWatchlistWithDetailsUseCase:
    """Get GetWatchlistWithDetails use case."""
    return GetWatchlistWithDetailsUseCase(
        watchlist_repository=watchlist_repo,
        page_repository=page_repo,
        scoring_repository=scoring_repo,
        logger=get_logger("usecase.get_watchlist_details"),
    )


def get_list_watchlists_with_counts_use_case(
    watchlist_repo: WatchlistRepo,
) -> ListWatchlistsWithCountsUseCase:
    """Get ListWatchlistsWithCounts use case."""
    return ListWatchlistsWithCountsUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.list_watchlists_counts"),
    )


def get_page_watchlists_use_case(
    watchlist_repo: WatchlistRepo,
) -> GetPageWatchlistsUseCase:
    """Get GetPageWatchlists use case."""
    return GetPageWatchlistsUseCase(
        watchlist_repository=watchlist_repo,
        logger=get_logger("usecase.get_page_watchlists"),
    )


GetWatchlistWithDetailsUC = Annotated[
    GetWatchlistWithDetailsUseCase,
    Depends(get_watchlist_with_details_use_case),
]
ListWatchlistsWithCountsUC = Annotated[
    ListWatchlistsWithCountsUseCase,
    Depends(get_list_watchlists_with_counts_use_case),
]
GetPageWatchlistsUC = Annotated[
    GetPageWatchlistsUseCase,
    Depends(get_page_watchlists_use_case),
]


# =============================================================================
# Monitoring Use Cases (Sprint 8.1)
# =============================================================================


def get_monitoring_summary_use_case(
    page_repo: PageRepo,
    scoring_repo: ScoringRepo,
    alert_repo: AlertRepo,
    metrics_repo: PageMetricsRepo,
) -> GetMonitoringSummaryUseCase:
    """Get GetMonitoringSummary use case."""
    return GetMonitoringSummaryUseCase(
        page_repository=page_repo,
        scoring_repository=scoring_repo,
        alert_repository=alert_repo,
        metrics_repository=metrics_repo,
        logger=get_logger("usecase.monitoring_summary"),
    )


GetMonitoringSummaryUC = Annotated[
    GetMonitoringSummaryUseCase,
    Depends(get_monitoring_summary_use_case),
]

"""Celery Task Definitions.

Defines the async tasks that can be dispatched via Celery.
These tasks are thin wrappers that call the actual use case implementations.

Architecture Note - AsyncTask Pattern:
    Celery workers run in a synchronous context, but our use cases are async.
    The AsyncTask base class provides a `run_async()` helper that creates
    a new event loop per task execution to bridge this gap.

    Trade-offs:
    - Simplicity: Easy to understand and debug
    - Overhead: New event loop per task (acceptable for our scale)
    - Isolation: Each task has its own loop, preventing cross-contamination

    This pattern is suitable for I/O-bound tasks with moderate throughput.
    For high-volume scenarios, consider a dedicated async worker (e.g., arq).
"""

import asyncio
import logging
from typing import Any

from celery import Task

from src.app.core.domain.value_objects import Country, ScanId, Url
from src.app.infrastructure.celery.celery_app import celery_app
from src.app.infrastructure.celery.container import get_container
from src.app.infrastructure.logging.config import configure_logging

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base class for async task execution in Celery.

    Provides a helper to run async coroutines within synchronous Celery tasks.
    Each task execution creates a new event loop to ensure isolation.

    Why a new event loop per task?
    1. Celery workers are multi-threaded/multi-process by default
    2. Event loops are not thread-safe and shouldn't be shared
    3. Creating a new loop per task ensures clean state
    4. The overhead is acceptable for I/O-bound operations

    Usage:
        @celery_app.task(bind=True, base=AsyncTask)
        def my_task(self):
            return self.run_async(my_async_function())
    """

    abstract = True

    def run_async(self, coro: Any) -> Any:
        """Run an async coroutine in a sync context.

        Creates a new event loop, runs the coroutine to completion,
        and properly cleans up the loop afterward.

        Args:
            coro: An awaitable coroutine object.

        Returns:
            The result of the coroutine execution.
        """
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name="tasks.scan_page",
    max_retries=3,
    default_retry_delay=60,
)
def scan_page_task(
    self: AsyncTask,
    page_id: str,
    scan_id: str,
    country: str,
) -> dict[str, Any]:
    """Scan a page for ads - performs deep page analysis.

    Executes AnalysePageDeepUseCase to:
    1. Fetch detailed ads via Meta Ads API
    2. Save ads to the database
    3. Extract destination URLs
    4. Dispatch website analysis task

    Args:
        page_id: The page identifier to scan.
        scan_id: The scan operation identifier (UUID string).
        country: Target country code (e.g., 'US', 'FR').

    Returns:
        Dict with scan results including ads_found count and status.
    """
    # Ensure logging is configured for worker process
    configure_logging(level="INFO")

    logger.info(
        "Starting page scan task",
        extra={
            "page_id": page_id,
            "scan_id": scan_id,
            "country": country,
            "task_id": self.request.id,
        },
    )

    async def _execute() -> dict[str, Any]:
        container = get_container()
        async with container.execution_context() as (db_session, http_session):
            use_case = await container.get_analyse_page_deep_use_case(
                db_session=db_session,
                http_session=http_session,
            )

            # Convert string parameters to domain value objects
            country_vo = Country(country)
            scan_id_vo = ScanId(scan_id)

            result = await use_case.execute(
                page_id=page_id,
                country=country_vo,
                scan_id=scan_id_vo,
            )

            return {
                "page_id": result.page_id,
                "scan_id": scan_id,
                "status": "completed",
                "ads_found": result.ads_found,
                "ads_saved": result.ads_saved,
                "destination_url": str(result.destination_url)
                if result.destination_url
                else None,
                "website_analysis_dispatched": result.website_analysis_dispatched,
            }

    try:
        result = self.run_async(_execute())
        logger.info(
            "Page scan completed",
            extra={
                "page_id": page_id,
                "scan_id": scan_id,
                "result": result,
            },
        )
        return result

    except Exception as exc:
        logger.error(
            "Page scan failed",
            extra={
                "page_id": page_id,
                "scan_id": scan_id,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name="tasks.analyse_website",
    max_retries=3,
    default_retry_delay=60,
)
def analyse_website_task(
    self: AsyncTask,
    page_id: str,
    url: str,
) -> dict[str, Any]:
    """Analyze a website for Shopify detection and store information.

    Executes AnalyseWebsiteUseCase to:
    1. Fetch HTML and headers
    2. Detect if site is Shopify
    3. Extract theme, currency, payment methods, category
    4. Update page with metadata
    5. Dispatch sitemap counting if Shopify

    Args:
        page_id: The associated page identifier.
        url: The website URL to analyze.

    Returns:
        Dict with analysis results including is_shopify, theme, etc.
    """
    configure_logging(level="INFO")

    logger.info(
        "Starting website analysis task",
        extra={
            "page_id": page_id,
            "url": url,
            "task_id": self.request.id,
        },
    )

    async def _execute() -> dict[str, Any]:
        container = get_container()
        async with container.execution_context() as (db_session, http_session):
            use_case = await container.get_analyse_website_use_case(
                db_session=db_session,
                http_session=http_session,
            )

            # Convert string URL to domain value object
            url_vo = Url(url)

            result = await use_case.execute(
                page_id=page_id,
                url=url_vo,
            )

            return {
                "page_id": result.page_id,
                "url": url,
                "status": "completed",
                "is_shopify": result.is_shopify,
                "shop_name": result.shop_name,
                "theme": result.theme_name,
                "currency": result.currency,
                "category": result.category,
                "payment_methods": result.payment_methods,
                "sitemap_count_dispatched": result.sitemap_count_dispatched,
            }

    try:
        result = self.run_async(_execute())
        logger.info(
            "Website analysis completed",
            extra={
                "page_id": page_id,
                "url": url,
                "result": result,
            },
        )
        return result

    except Exception as exc:
        logger.error(
            "Website analysis failed",
            extra={
                "page_id": page_id,
                "url": url,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name="tasks.count_sitemap_products",
    max_retries=3,
    default_retry_delay=60,
)
def count_sitemap_products_task(
    self: AsyncTask,
    page_id: str,
    website: str,
    country: str,
) -> dict[str, Any]:
    """Count products from a website's sitemap.

    Executes ExtractProductCountUseCase to:
    1. Discover sitemaps
    2. Parse product URLs
    3. Count products for the target country
    4. Update page with product count

    Args:
        page_id: The associated page identifier.
        website: The website URL.
        country: Target country code for filtering.

    Returns:
        Dict with product count results.
    """
    configure_logging(level="INFO")

    logger.info(
        "Starting sitemap product count task",
        extra={
            "page_id": page_id,
            "website": website,
            "country": country,
            "task_id": self.request.id,
        },
    )

    async def _execute() -> dict[str, Any]:
        container = get_container()
        async with container.execution_context() as (db_session, http_session):
            use_case = await container.get_extract_product_count_use_case(
                db_session=db_session,
                http_session=http_session,
            )

            # Convert string parameters to domain value objects
            website_url = Url(website)
            country_vo = Country(country)

            result = await use_case.execute(
                page_id=page_id,
                website_url=website_url,
                country=country_vo,
            )

            return {
                "page_id": result.page_id,
                "website": website,
                "country": country,
                "status": "completed",
                "product_count": result.product_count,
                "sitemaps_found": result.sitemaps_found,
                "previous_count": result.previous_count,
            }

    try:
        result = self.run_async(_execute())
        logger.info(
            "Sitemap product count completed",
            extra={
                "page_id": page_id,
                "website": website,
                "result": result,
            },
        )
        return result

    except Exception as exc:
        logger.error(
            "Sitemap product count failed",
            extra={
                "page_id": page_id,
                "website": website,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name="tasks.compute_shop_score",
    max_retries=3,
    default_retry_delay=60,
)
def compute_shop_score_task(
    self: AsyncTask,
    page_id: str,
) -> dict[str, Any]:
    """Compute the score for a shop/page.

    Executes ComputeShopScoreUseCase to:
    1. Gather data about the page (ads, Shopify profile, products)
    2. Calculate weighted score components:
       - Ads Activity Score (40%)
       - Shopify Score (30%)
       - Creative Quality Score (20%)
       - Catalog Score (10%)
    3. Save the computed score to the database

    Args:
        page_id: The page identifier to score.

    Returns:
        Dict with scoring results including overall score and components.
    """
    configure_logging(level="INFO")

    logger.info(
        "Starting shop score computation task",
        extra={
            "page_id": page_id,
            "task_id": self.request.id,
        },
    )

    async def _execute() -> dict[str, Any]:
        container = get_container()
        async with container.execution_context() as (db_session, _http_session):
            use_case = await container.get_compute_shop_score_use_case(
                db_session=db_session,
            )

            result = await use_case.execute(page_id=page_id)

            return {
                "page_id": result.page_id,
                "status": "completed",
                "score": result.score,
                "ads_activity_score": result.ads_activity_score,
                "shopify_score": result.shopify_score,
                "creative_quality_score": result.creative_quality_score,
                "catalog_score": result.catalog_score,
                "tier": result.tier,
            }

    try:
        result = self.run_async(_execute())
        logger.info(
            "Shop score computation completed",
            extra={
                "page_id": page_id,
                "result": result,
            },
        )
        return result

    except Exception as exc:
        logger.error(
            "Shop score computation failed",
            extra={
                "page_id": page_id,
                "error": str(exc),
            },
            exc_info=True,
        )
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name="tasks.rescore_all_watchlists",
    max_retries=1,
    default_retry_delay=300,
)
def rescore_all_watchlists_task(
    self: AsyncTask,
) -> dict[str, Any]:
    """Rescore all pages in all active watchlists.

    Periodic task that iterates over all active watchlists and dispatches
    compute_shop_score tasks for all pages in each watchlist.

    This task is designed to be run on a schedule (e.g., daily) via
    Celery Beat to keep shop scores up to date for watchlist members.

    Returns:
        Dict with summary of rescoring: total watchlists processed,
        total tasks dispatched, and any errors encountered.
    """
    configure_logging(level="INFO")

    logger.info(
        "Starting rescore all watchlists task",
        extra={
            "task_id": self.request.id,
        },
    )

    async def _execute() -> dict[str, Any]:
        from src.app.adapters.outbound.repositories.watchlist_repository import (
            PostgresWatchlistRepository,
        )

        container = get_container()
        total_dispatched = 0
        watchlists_processed = 0
        errors: list[dict[str, str]] = []

        async with container.execution_context() as (db_session, _http_session):
            # Get all active watchlists
            watchlist_repo = PostgresWatchlistRepository(db_session)
            watchlists = await watchlist_repo.list_watchlists(limit=1000, offset=0)

            logger.info(
                "Found watchlists to rescore",
                extra={"count": len(watchlists)},
            )

            for watchlist in watchlists:
                try:
                    use_case = await container.get_rescore_watchlist_use_case(
                        db_session=db_session,
                    )
                    dispatched = await use_case.execute(watchlist_id=watchlist.id)
                    total_dispatched += dispatched
                    watchlists_processed += 1
                    logger.debug(
                        "Rescored watchlist",
                        extra={
                            "watchlist_id": watchlist.id,
                            "watchlist_name": watchlist.name,
                            "dispatched": dispatched,
                        },
                    )
                except Exception as exc:
                    logger.error(
                        "Failed to rescore watchlist",
                        extra={
                            "watchlist_id": watchlist.id,
                            "error": str(exc),
                        },
                    )
                    errors.append({
                        "watchlist_id": watchlist.id,
                        "error": str(exc),
                    })

        return {
            "status": "completed",
            "watchlists_found": len(watchlists),
            "watchlists_processed": watchlists_processed,
            "total_tasks_dispatched": total_dispatched,
            "errors": errors,
        }

    try:
        result = self.run_async(_execute())
        logger.info(
            "Rescore all watchlists completed",
            extra={
                "result": result,
            },
        )
        return result

    except Exception as exc:
        logger.error(
            "Rescore all watchlists failed",
            extra={
                "error": str(exc),
            },
            exc_info=True,
        )
        raise self.retry(exc=exc)

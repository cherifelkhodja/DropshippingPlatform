"""Celery Task Definitions.

Defines the async tasks that can be dispatched via Celery.
These tasks are thin wrappers that call the actual use case implementations.
"""

import asyncio
import logging
from typing import Any

from celery import Task

from .celery_app import celery_app

logger = logging.getLogger(__name__)


class AsyncTask(Task):
    """Base class for async task execution.

    Provides a helper to run async coroutines within Celery tasks.
    """

    abstract = True

    def run_async(self, coro: Any) -> Any:
        """Run an async coroutine in a sync context."""
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
    """Scan a page for ads.

    Performs deep page analysis to find and analyze ads.

    Args:
        page_id: The page identifier to scan.
        scan_id: The scan operation identifier.
        country: Target country code (e.g., 'US', 'FR').

    Returns:
        Dict with scan results including ads_found count.
    """
    logger.info(
        "Starting page scan task",
        extra={
            "page_id": page_id,
            "scan_id": scan_id,
            "country": country,
            "task_id": self.request.id,
        },
    )

    try:
        # TODO: Implement actual scan logic with use case injection
        # For now, return placeholder result
        result = {
            "page_id": page_id,
            "scan_id": scan_id,
            "status": "completed",
            "ads_found": 0,
        }

        logger.info(
            "Page scan completed",
            extra={"page_id": page_id, "scan_id": scan_id, "result": result},
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
    """Analyze a website.

    Performs website analysis including Shopify detection,
    theme identification, and payment method detection.

    Args:
        page_id: The associated page identifier.
        url: The website URL to analyze.

    Returns:
        Dict with analysis results.
    """
    logger.info(
        "Starting website analysis task",
        extra={
            "page_id": page_id,
            "url": url,
            "task_id": self.request.id,
        },
    )

    try:
        # TODO: Implement actual analysis logic with use case injection
        # For now, return placeholder result
        result: dict[str, Any] = {
            "page_id": page_id,
            "url": url,
            "status": "completed",
            "is_shopify": None,
            "theme": None,
            "payment_methods": [],
        }

        logger.info(
            "Website analysis completed",
            extra={"page_id": page_id, "url": url, "result": result},
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

    Parses the sitemap and counts products available
    in the specified country.

    Args:
        page_id: The associated page identifier.
        website: The website URL.
        country: Target country code for filtering.

    Returns:
        Dict with product count results.
    """
    logger.info(
        "Starting sitemap product count task",
        extra={
            "page_id": page_id,
            "website": website,
            "country": country,
            "task_id": self.request.id,
        },
    )

    try:
        # TODO: Implement actual sitemap parsing logic with use case injection
        # For now, return placeholder result
        result = {
            "page_id": page_id,
            "website": website,
            "country": country,
            "status": "completed",
            "product_count": 0,
        }

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

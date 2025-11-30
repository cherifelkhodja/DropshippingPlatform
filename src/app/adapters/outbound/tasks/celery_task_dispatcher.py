"""Celery Task Dispatcher Adapter.

Implements TaskDispatcherPort using Celery for async task dispatch.
"""

import logging
from typing import Optional

from celery import Celery
from celery.result import AsyncResult

from ....core.domain.errors import TaskDispatchError
from ....core.domain.value_objects import Country, ScanId, Url
from ....core.ports.task_dispatcher_port import TaskDispatcherPort


class CeleryTaskDispatcher(TaskDispatcherPort):
    """Celery-based implementation of TaskDispatcherPort.

    Dispatches async tasks to the Celery task queue for
    background processing by workers.
    """

    def __init__(
        self,
        celery_app: Celery,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the Celery task dispatcher.

        Args:
            celery_app: The Celery application instance.
            logger: Optional logger instance.
        """
        self._celery = celery_app
        self._logger = logger or logging.getLogger(__name__)

    async def dispatch_scan_page(
        self,
        page_id: str,
        scan_id: ScanId,
        country: Country,
    ) -> None:
        """Dispatch a deep page analysis task.

        Args:
            page_id: The page to analyze.
            scan_id: The scan operation identifier.
            country: Target country for the analysis.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        self._logger.info(
            "Dispatching scan_page task",
            extra={
                "page_id": page_id,
                "scan_id": str(scan_id),
                "country": str(country),
            },
        )

        try:
            result: AsyncResult = self._celery.send_task(
                "tasks.scan_page",
                args=[page_id, str(scan_id), str(country)],
            )
            self._logger.debug(
                "Task dispatched successfully",
                extra={"task_id": result.id, "task_name": "scan_page"},
            )
        except Exception as exc:
            self._logger.error(
                "Failed to dispatch scan_page task",
                extra={
                    "page_id": page_id,
                    "scan_id": str(scan_id),
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise TaskDispatchError(
                task_name="scan_page",
                reason=str(exc),
            ) from exc

    async def dispatch_analyse_website(
        self,
        page_id: str,
        url: Url,
    ) -> None:
        """Dispatch a website analysis task.

        Args:
            page_id: The associated page identifier.
            url: The website URL to analyze.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        self._logger.info(
            "Dispatching analyse_website task",
            extra={
                "page_id": page_id,
                "url": str(url),
            },
        )

        try:
            result: AsyncResult = self._celery.send_task(
                "tasks.analyse_website",
                args=[page_id, str(url)],
            )
            self._logger.debug(
                "Task dispatched successfully",
                extra={"task_id": result.id, "task_name": "analyse_website"},
            )
        except Exception as exc:
            self._logger.error(
                "Failed to dispatch analyse_website task",
                extra={
                    "page_id": page_id,
                    "url": str(url),
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise TaskDispatchError(
                task_name="analyse_website",
                reason=str(exc),
            ) from exc

    async def dispatch_sitemap_count(
        self,
        page_id: str,
        website: Url,
        country: Country,
    ) -> None:
        """Dispatch a sitemap product counting task.

        Args:
            page_id: The associated page identifier.
            website: The website URL.
            country: Target country for filtering.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        self._logger.info(
            "Dispatching sitemap_count task",
            extra={
                "page_id": page_id,
                "website": str(website),
                "country": str(country),
            },
        )

        try:
            result: AsyncResult = self._celery.send_task(
                "tasks.count_sitemap_products",
                args=[page_id, str(website), str(country)],
            )
            self._logger.debug(
                "Task dispatched successfully",
                extra={"task_id": result.id, "task_name": "count_sitemap_products"},
            )
        except Exception as exc:
            self._logger.error(
                "Failed to dispatch sitemap_count task",
                extra={
                    "page_id": page_id,
                    "website": str(website),
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise TaskDispatchError(
                task_name="sitemap_count",
                reason=str(exc),
            ) from exc

    async def dispatch_compute_shop_score(
        self,
        page_id: str,
    ) -> str:
        """Dispatch a shop score computation task.

        Args:
            page_id: The page to compute score for.

        Returns:
            The task ID for tracking the dispatched task.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        self._logger.info(
            "Dispatching compute_shop_score task",
            extra={
                "page_id": page_id,
            },
        )

        try:
            result: AsyncResult = self._celery.send_task(
                "tasks.compute_shop_score",
                args=[page_id],
            )
            self._logger.debug(
                "Task dispatched successfully",
                extra={"task_id": result.id, "task_name": "compute_shop_score"},
            )
            return str(result.id)
        except Exception as exc:
            self._logger.error(
                "Failed to dispatch compute_shop_score task",
                extra={
                    "page_id": page_id,
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise TaskDispatchError(
                task_name="compute_shop_score",
                reason=str(exc),
            ) from exc

    def dispatch_analyze_creatives_for_page(
        self,
        page_id: str,
    ) -> AsyncResult:
        """Dispatch a creative analysis task for a page.

        Args:
            page_id: The page to analyze creatives for.

        Returns:
            The AsyncResult for tracking the dispatched task.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        self._logger.info(
            "Dispatching analyze_creatives_for_page task",
            extra={
                "page_id": page_id,
            },
        )

        try:
            result: AsyncResult = self._celery.send_task(
                "tasks.analyze_creatives_for_page",
                args=[page_id],
            )
            self._logger.debug(
                "Task dispatched successfully",
                extra={"task_id": result.id, "task_name": "analyze_creatives_for_page"},
            )
            return result
        except Exception as exc:
            self._logger.error(
                "Failed to dispatch analyze_creatives_for_page task",
                extra={
                    "page_id": page_id,
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise TaskDispatchError(
                task_name="analyze_creatives_for_page",
                reason=str(exc),
            ) from exc

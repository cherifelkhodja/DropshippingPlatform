"""Task Dispatcher Port.

Interface for async task orchestration (Celery).
"""

from typing import Protocol

from ..domain.value_objects import ScanId, Url, Country


class TaskDispatcherPort(Protocol):
    """Port interface for async task dispatching.

    This port defines the contract for dispatching asynchronous
    background tasks. Implementations will handle the actual
    task queue integration (e.g., Celery).
    """

    async def dispatch_scan_page(
        self,
        page_id: str,
        scan_id: ScanId,
        country: Country,
    ) -> None:
        """Dispatch a deep page analysis task.

        Launches an asynchronous job to analyze ads for a specific page.

        Args:
            page_id: The page to analyze.
            scan_id: The scan operation identifier.
            country: Target country for the analysis.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        ...

    async def dispatch_analyse_website(
        self,
        page_id: str,
        url: Url,
    ) -> None:
        """Dispatch a website analysis task.

        Launches an asynchronous job to analyze a website
        (Shopify detection, theme, payment methods, etc.).

        Args:
            page_id: The associated page identifier.
            url: The website URL to analyze.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        ...

    async def dispatch_sitemap_count(
        self,
        page_id: str,
        website: Url,
        country: Country,
    ) -> None:
        """Dispatch a sitemap product counting task.

        Launches an asynchronous job to count products from
        the website's sitemap.

        Args:
            page_id: The associated page identifier.
            website: The website URL.
            country: Target country for filtering.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        ...

    async def dispatch_compute_shop_score(
        self,
        page_id: str,
    ) -> str:
        """Dispatch a shop score computation task.

        Launches an asynchronous job to compute the shop score
        for a specific page based on ads, Shopify signals, etc.

        Args:
            page_id: The page to compute score for.

        Returns:
            The task ID for tracking the dispatched task.

        Raises:
            TaskDispatchError: If the task cannot be dispatched.
        """
        ...

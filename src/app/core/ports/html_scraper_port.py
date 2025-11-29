"""HTML Scraper Port.

Interface for fetching HTML content from web pages.
"""

from typing import Protocol

from ..domain.value_objects import Url


class HtmlScraperPort(Protocol):
    """Port interface for HTML scraping operations.

    This port defines the contract for fetching raw HTML content
    and HTTP headers from web pages. Implementations will handle
    the actual HTTP requests, timeouts, and error handling.
    """

    async def fetch_html(
        self,
        url: Url,
        timeout_seconds: int = 15,
    ) -> str:
        """Fetch the raw HTML content of a page.

        Args:
            url: The URL to fetch.
            timeout_seconds: Request timeout in seconds.

        Returns:
            The raw HTML content as a string.

        Raises:
            ScrapingError: On timeout, network error, or invalid response.
            ScrapingTimeoutError: When the request times out.
            ScrapingBlockedError: When the request is blocked (403, captcha).
        """
        ...

    async def fetch_headers(
        self,
        url: Url,
        timeout_seconds: int = 10,
    ) -> dict[str, str]:
        """Fetch the HTTP response headers for a URL.

        Useful for detecting server type, redirects, and other metadata
        without downloading the full page content.

        Args:
            url: The URL to check.
            timeout_seconds: Request timeout in seconds.

        Returns:
            Dictionary of HTTP response headers.

        Raises:
            ScrapingError: On timeout, network error, or invalid response.
        """
        ...

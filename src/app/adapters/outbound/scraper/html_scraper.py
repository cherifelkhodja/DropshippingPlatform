"""HTML Scraper Client.

Implementation of HtmlScraperPort for fetching raw HTML content.
"""

import aiohttp

from src.app.core.domain.value_objects import Url
from src.app.core.ports.logging_port import LoggingPort
from src.app.infrastructure.http.base_http_client import BaseHttpClient


class HtmlScraperClient:
    """HTTP-based HTML scraper implementing HtmlScraperPort.

    Fetches raw HTML content and headers using aiohttp.
    No JavaScript rendering - static HTML only.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        logger: LoggingPort,
    ) -> None:
        """Initialize HTML scraper client.

        Args:
            session: aiohttp client session.
            logger: Logging port for structured logging.
        """
        self._http = BaseHttpClient(session=session, logger=logger)
        self._logger = logger

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
            ScrapingError: On network error or invalid response.
            ScrapingTimeoutError: When the request times out.
            ScrapingBlockedError: When the request is blocked (403, 429).
        """
        self._logger.info(
            "Fetching HTML",
            url=url.value,
            timeout_seconds=timeout_seconds,
        )

        response = await self._http.get(
            url=url.value,
            timeout_seconds=timeout_seconds,
        )

        async with response:
            html_content = await response.text()

        self._logger.info(
            "HTML fetched successfully",
            url=url.value,
            content_length=len(html_content),
        )

        return html_content

    async def fetch_headers(
        self,
        url: Url,
        timeout_seconds: int = 10,
    ) -> dict[str, str]:
        """Fetch the HTTP response headers for a URL.

        Args:
            url: The URL to check.
            timeout_seconds: Request timeout in seconds.

        Returns:
            Dictionary of HTTP response headers.

        Raises:
            ScrapingError: On network error or invalid response.
            ScrapingTimeoutError: When the request times out.
            ScrapingBlockedError: When the request is blocked (403, 429).
        """
        self._logger.info(
            "Fetching headers",
            url=url.value,
            timeout_seconds=timeout_seconds,
        )

        response = await self._http.head(
            url=url.value,
            timeout_seconds=timeout_seconds,
        )

        # Convert CIMultiDictProxy to regular dict
        headers = {key: value for key, value in response.headers.items()}

        self._logger.info(
            "Headers fetched successfully",
            url=url.value,
            headers_count=len(headers),
        )

        return headers

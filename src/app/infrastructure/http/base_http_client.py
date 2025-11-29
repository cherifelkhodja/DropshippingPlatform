"""Base HTTP Client.

Shared HTTP utilities for scraping and sitemap clients.
"""

import asyncio

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.app.core.domain.errors import (
    ScrapingBlockedError,
    ScrapingError,
    ScrapingTimeoutError,
)
from src.app.core.ports.logging_port import LoggingPort


class RetryableHttpError(Exception):
    """Marker exception for retryable HTTP errors."""

    pass


# Default headers to mimic a real browser
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class BaseHttpClient:
    """Base HTTP client with retry logic and error handling.

    Provides common functionality for HTTP clients that need:
    - Retry with exponential backoff
    - Structured logging
    - Consistent error handling
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        logger: LoggingPort,
    ) -> None:
        """Initialize base HTTP client.

        Args:
            session: aiohttp client session.
            logger: Logging port for structured logging.
        """
        self._session = session
        self._logger = logger

    @retry(
        retry=retry_if_exception_type(RetryableHttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get(
        self,
        url: str,
        timeout_seconds: int = 15,
        headers: dict[str, str] | None = None,
    ) -> aiohttp.ClientResponse:
        """Execute GET request with retry logic.

        Args:
            url: Request URL.
            timeout_seconds: Request timeout.
            headers: Optional custom headers.

        Returns:
            aiohttp response object.

        Raises:
            ScrapingTimeoutError: On timeout.
            ScrapingBlockedError: On 403/429 responses.
            ScrapingError: On other errors.
        """
        request_headers = {**DEFAULT_HEADERS, **(headers or {})}
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        try:
            response = await self._session.get(
                url,
                headers=request_headers,
                timeout=timeout,
                allow_redirects=True,
            )

            return self._handle_response(response, url)

        except asyncio.TimeoutError as exc:
            self._logger.warning(
                "Request timeout",
                url=url,
                timeout_seconds=timeout_seconds,
            )
            raise ScrapingTimeoutError(url=url, timeout_seconds=timeout_seconds) from exc

        except aiohttp.ClientError as exc:
            self._logger.error(
                "HTTP client error",
                url=url,
                error=str(exc),
            )
            raise ScrapingError(url=url, reason=f"HTTP error: {exc}") from exc

    @retry(
        retry=retry_if_exception_type(RetryableHttpError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def head(
        self,
        url: str,
        timeout_seconds: int = 10,
        headers: dict[str, str] | None = None,
    ) -> aiohttp.ClientResponse:
        """Execute HEAD request with retry logic.

        Args:
            url: Request URL.
            timeout_seconds: Request timeout.
            headers: Optional custom headers.

        Returns:
            aiohttp response object.

        Raises:
            ScrapingTimeoutError: On timeout.
            ScrapingBlockedError: On 403/429 responses.
            ScrapingError: On other errors.
        """
        request_headers = {**DEFAULT_HEADERS, **(headers or {})}
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        try:
            response = await self._session.head(
                url,
                headers=request_headers,
                timeout=timeout,
                allow_redirects=True,
            )

            return self._handle_response(response, url)

        except asyncio.TimeoutError as exc:
            self._logger.warning(
                "Request timeout",
                url=url,
                timeout_seconds=timeout_seconds,
            )
            raise ScrapingTimeoutError(url=url, timeout_seconds=timeout_seconds) from exc

        except aiohttp.ClientError as exc:
            self._logger.error(
                "HTTP client error",
                url=url,
                error=str(exc),
            )
            raise ScrapingError(url=url, reason=f"HTTP error: {exc}") from exc

    def _handle_response(
        self,
        response: aiohttp.ClientResponse,
        url: str,
    ) -> aiohttp.ClientResponse:
        """Handle HTTP response status codes.

        Args:
            response: aiohttp response object.
            url: Original request URL.

        Returns:
            The response if successful.

        Raises:
            ScrapingBlockedError: On 403/429 responses.
            RetryableHttpError: On 5xx responses.
            ScrapingError: On other error responses.
        """
        status = response.status

        # Success
        if 200 <= status < 300:
            return response

        # Blocked (403, 429)
        if status in (403, 429):
            self._logger.warning(
                "Request blocked",
                url=url,
                status=status,
            )
            raise ScrapingBlockedError(url=url, status_code=status)

        # Server errors - retryable
        if status >= 500:
            self._logger.warning(
                "Server error, will retry",
                url=url,
                status=status,
            )
            raise RetryableHttpError(f"Server error {status}")

        # Other client errors
        self._logger.warning(
            "HTTP error",
            url=url,
            status=status,
        )
        raise ScrapingError(url=url, reason=f"HTTP {status}")

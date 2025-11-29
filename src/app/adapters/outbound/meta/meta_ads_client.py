"""Meta Ads Client.

Implementation of MetaAdsPort for Meta Ads Library API.
"""

from collections.abc import Iterable, Sequence

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.app.adapters.outbound.meta.config import MetaAdsConfig
from src.app.core.domain.errors import (
    MetaAdsApiError,
    MetaAdsAuthenticationError,
    MetaAdsRateLimitError,
)
from src.app.core.domain.value_objects import Country, Language
from src.app.core.ports.logging_port import LoggingPort


# Fields for basic ad search (search_ads_by_keyword, get_ads_by_page)
BASIC_FIELDS = "id,page_id"

# Fields for detailed ad information (get_ads_details)
DETAIL_FIELDS = (
    "id,page_id,page_name,ad_creation_time,ad_creative_bodies,"
    "ad_creative_link_captions,ad_creative_link_titles,ad_snapshot_url,"
    "eu_total_reach,total_reach_by_location,age_country_gender_reach_breakdown,"
    "languages,country,publisher_platforms,target_ages,target_gender,"
    "beneficiary_payers"
)


class RetryableError(Exception):
    """Marker exception for retryable errors."""

    pass


class MetaAdsClient:
    """Meta Ads Library API client implementing MetaAdsPort.

    Handles API requests, pagination, rate limiting, and error handling
    for the Meta Ads Library (ads_archive endpoint).
    """

    def __init__(
        self,
        config: MetaAdsConfig,
        session: aiohttp.ClientSession,
        logger: LoggingPort,
    ) -> None:
        """Initialize Meta Ads client.

        Args:
            config: Meta Ads API configuration.
            session: aiohttp client session for HTTP requests.
            logger: Logging port for structured logging.
        """
        self._config = config
        self._session = session
        self._logger = logger

    async def search_ads_by_keyword(
        self,
        keyword: str,
        country: Country,
        language: Language | None = None,
        limit: int = 1000,
    ) -> Iterable[dict[str, object]]:
        """Search for active ads by keyword.

        Args:
            keyword: The search keyword.
            country: Target country for the search.
            language: Optional language filter.
            limit: Maximum number of ads to return.

        Returns:
            Iterable of raw ad dictionaries from Meta API.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
        """
        self._logger.info(
            "Starting keyword search",
            keyword=keyword,
            country=country.code,
            language=language.code if language else None,
            limit=limit,
        )

        params: dict[str, str | int] = {
            "ad_type": "ALL",
            "ad_active_status": "ACTIVE",
            "search_type": "KEYWORD_UNORDERED",
            "ad_reached_countries": country.code,
            "search_terms": keyword,
            "limit": min(limit, 1000),
            "fields": BASIC_FIELDS,
        }

        if language:
            params["languages"] = language.code

        ads = await self._fetch_with_pagination(params, limit)

        self._logger.info(
            "Keyword search completed",
            keyword=keyword,
            ads_count=len(ads),
        )

        return ads

    async def get_ads_by_page(
        self,
        page_ids: Sequence[str],
        country: Country,
        limit: int = 1000,
    ) -> Iterable[dict[str, object]]:
        """Retrieve active ads for a list of page IDs.

        Args:
            page_ids: List of Meta page IDs to fetch ads for (max 10).
            country: Target country for filtering.
            limit: Maximum number of ads to return per page.

        Returns:
            Iterable of raw ad dictionaries from Meta API.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
        """
        if not page_ids:
            return []

        # Meta API supports max 10 page IDs per request
        page_ids_batch = list(page_ids)[:10]

        self._logger.info(
            "Fetching ads by page IDs",
            page_ids=page_ids_batch,
            country=country.code,
            limit=limit,
        )

        params: dict[str, str | int] = {
            "ad_type": "ALL",
            "ad_active_status": "ACTIVE",
            "ad_reached_countries": country.code,
            "search_page_ids": ",".join(page_ids_batch),
            "limit": min(limit, 1000),
            "fields": BASIC_FIELDS,
        }

        ads = await self._fetch_with_pagination(params, limit)

        self._logger.info(
            "Page ads fetch completed",
            page_ids_count=len(page_ids_batch),
            ads_count=len(ads),
        )

        return ads

    async def get_ads_details(
        self,
        page_id: str,
        country: Country,
        limit: int = 1000,
    ) -> Iterable[dict[str, object]]:
        """Retrieve detailed ad information for a specific page.

        Args:
            page_id: The Meta page ID.
            country: Target country for filtering.
            limit: Maximum number of ads to return.

        Returns:
            Iterable of detailed ad dictionaries from Meta API.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
        """
        self._logger.info(
            "Fetching ad details",
            page_id=page_id,
            country=country.code,
            limit=limit,
        )

        params: dict[str, str | int] = {
            "ad_type": "ALL",
            "ad_active_status": "ACTIVE",
            "ad_reached_countries": country.code,
            "search_page_ids": page_id,
            "limit": min(limit, 1000),
            "fields": DETAIL_FIELDS,
        }

        ads = await self._fetch_with_pagination(params, limit)

        self._logger.info(
            "Ad details fetch completed",
            page_id=page_id,
            ads_count=len(ads),
        )

        return ads

    async def _fetch_with_pagination(
        self,
        params: dict[str, str | int],
        max_results: int,
    ) -> list[dict[str, object]]:
        """Fetch ads with automatic pagination handling.

        Args:
            params: Request parameters.
            max_results: Maximum total results to fetch.

        Returns:
            List of ad dictionaries.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
        """
        all_ads: list[dict[str, object]] = []
        next_url: str | None = None

        while len(all_ads) < max_results:
            if next_url:
                # For pagination, use the full next URL
                response_data = await self._request_url(next_url)
            else:
                # Initial request
                response_data = await self._request(params)

            # Extract ads data
            ads_data = response_data.get("data", [])
            if not isinstance(ads_data, list):
                break

            all_ads.extend(ads_data)

            # Check for pagination
            paging = response_data.get("paging", {})
            next_url = paging.get("next") if isinstance(paging, dict) else None

            if not next_url:
                break

            # Respect the limit
            if len(all_ads) >= max_results:
                break

        # Trim to max_results
        return all_ads[:max_results]

    async def _request(
        self,
        params: dict[str, str | int],
    ) -> dict[str, object]:
        """Make a request to the Meta Ads API.

        Args:
            params: Request parameters.

        Returns:
            Parsed JSON response.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
        """
        # Add access token
        full_params = {**params, "access_token": self._config.access_token}

        return await self._execute_request(
            url=self._config.ads_archive_url,
            params=full_params,
        )

    async def _request_url(self, url: str) -> dict[str, object]:
        """Make a request to a specific URL (for pagination).

        Args:
            url: Full URL to request (includes access_token).

        Returns:
            Parsed JSON response.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
        """
        return await self._execute_request(url=url, params=None)

    @retry(
        retry=retry_if_exception_type(RetryableError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _execute_request(
        self,
        url: str,
        params: dict[str, str | int] | None,
    ) -> dict[str, object]:
        """Execute HTTP request with retry logic.

        Args:
            url: Request URL.
            params: Optional query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
            RetryableError: On retryable errors (5xx).
        """
        timeout = aiohttp.ClientTimeout(total=self._config.timeout_seconds)

        try:
            async with self._session.get(
                url,
                params=params,
                timeout=timeout,
            ) as response:
                return await self._handle_response(response)

        except aiohttp.ClientError as exc:
            self._logger.error(
                "HTTP client error",
                url=url,
                error=str(exc),
            )
            raise MetaAdsApiError(reason=f"HTTP error: {exc}") from exc

    async def _handle_response(
        self,
        response: aiohttp.ClientResponse,
    ) -> dict[str, object]:
        """Handle HTTP response and convert to appropriate result/error.

        Args:
            response: aiohttp response object.

        Returns:
            Parsed JSON response data.

        Raises:
            MetaAdsApiError: On API errors.
            MetaAdsAuthenticationError: On authentication failures.
            MetaAdsRateLimitError: On rate limit exceeded.
            RetryableError: On retryable errors (5xx).
        """
        status = response.status

        # Success
        if status == 200:
            data = await response.json()
            if isinstance(data, dict):
                return data
            return {"data": data}

        # Parse error response
        error_data: dict[str, object] = {}
        try:
            error_data = await response.json()
        except (aiohttp.ContentTypeError, ValueError):
            error_data = {"error": {"message": await response.text()}}

        error_info = error_data.get("error", {})
        error_message = (
            error_info.get("message", "Unknown error")
            if isinstance(error_info, dict)
            else str(error_info)
        )

        self._logger.warning(
            "Meta API error response",
            status=status,
            error=error_message,
        )

        # Authentication errors (401, 403)
        if status in (401, 403):
            raise MetaAdsAuthenticationError()

        # Rate limit (429)
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else None
            raise MetaAdsRateLimitError(retry_after=retry_seconds)

        # Client errors (400, other 4xx)
        if 400 <= status < 500:
            raise MetaAdsApiError(reason=f"Client error {status}: {error_message}")

        # Server errors (5xx) - retryable
        if status >= 500:
            raise RetryableError(f"Server error {status}: {error_message}")

        # Unknown status
        raise MetaAdsApiError(reason=f"Unexpected status {status}: {error_message}")

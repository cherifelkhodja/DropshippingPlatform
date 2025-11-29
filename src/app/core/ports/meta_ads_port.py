"""Meta Ads Port.

Interface for interacting with Meta Ads Library API.
"""

from typing import Protocol, Iterable, Sequence

from ..domain.value_objects import Country, Language


class MetaAdsPort(Protocol):
    """Port interface for Meta Ads Library operations.

    This port defines the contract for fetching advertisement data
    from the Meta Ads Library. Implementations will handle the actual
    API communication, pagination, and rate limiting.
    """

    async def search_ads_by_keyword(
        self,
        keyword: str,
        country: Country,
        language: Language | None = None,
        limit: int = 1000,
    ) -> Iterable[dict]:
        """Search for active ads by keyword.

        Pagination is handled by the adapter implementation.
        Returns raw dicts (Meta API mapping) that will be normalized
        in use cases.

        Args:
            keyword: The search keyword.
            country: Target country for the search.
            language: Optional language filter.
            limit: Maximum number of ads to return.

        Returns:
            Iterable of raw ad dictionaries from Meta API.

        Raises:
            Domain errors for rate limiting, authentication failures, etc.
        """
        ...

    async def get_ads_by_page(
        self,
        page_ids: Sequence[str],
        country: Country,
        limit: int = 1000,
    ) -> Iterable[dict]:
        """Retrieve active ads for a list of page IDs.

        Supports batch requests (max 10 page IDs per request).

        Args:
            page_ids: List of Meta page IDs to fetch ads for.
            country: Target country for filtering.
            limit: Maximum number of ads to return per page.

        Returns:
            Iterable of raw ad dictionaries from Meta API.

        Raises:
            Domain errors for rate limiting, invalid page IDs, etc.
        """
        ...

    async def get_ads_details(
        self,
        page_id: str,
        country: Country,
        limit: int = 1000,
    ) -> Iterable[dict]:
        """Retrieve detailed ad information for a specific page.

        Includes creative content, reach estimates, targeting info, etc.

        Args:
            page_id: The Meta page ID.
            country: Target country for filtering.
            limit: Maximum number of ads to return.

        Returns:
            Iterable of detailed ad dictionaries from Meta API.

        Raises:
            Domain errors for rate limiting, page not found, etc.
        """
        ...

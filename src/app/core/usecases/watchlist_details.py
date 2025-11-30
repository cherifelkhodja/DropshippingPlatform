"""Watchlist Details Use Cases.

Extended use cases for watchlists that include page details.
These are optimized for UI/frontend consumption.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..domain.entities import Watchlist, WatchlistItem, Page, ShopScore
from ..domain.errors import EntityNotFoundError
from ..ports import (
    LoggingPort,
    WatchlistRepository,
    PageRepository,
    ScoringRepository,
)


@dataclass
class WatchlistPageInfo:
    """Enriched page information for watchlist display.

    Contains page details along with scoring information
    for display in watchlist views.
    """

    page_id: str
    page_name: str
    url: str
    country: Optional[str]
    is_shopify: bool
    shop_score: float
    tier: str
    active_ads_count: int
    added_at: datetime


@dataclass
class WatchlistWithDetails:
    """Watchlist with enriched page information.

    Contains the watchlist metadata along with detailed
    information about each page in the watchlist.
    """

    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool
    pages_count: int
    pages: list[WatchlistPageInfo]


class GetWatchlistWithDetailsUseCase:
    """Use case for retrieving a watchlist with full page details.

    This use case combines watchlist items with page and scoring
    information for a complete view suitable for UI display.
    """

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        page_repository: PageRepository,
        scoring_repository: ScoringRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            page_repository: Repository for Page entities.
            scoring_repository: Repository for ShopScore entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._page_repo = page_repository
        self._scoring_repo = scoring_repository
        self._logger = logger

    async def execute(self, watchlist_id: str) -> WatchlistWithDetails:
        """Execute the get watchlist with details use case.

        Args:
            watchlist_id: The unique watchlist identifier.

        Returns:
            WatchlistWithDetails with full page information.

        Raises:
            EntityNotFoundError: If the watchlist does not exist.
        """
        self._logger.debug(
            "Getting watchlist with details",
            watchlist_id=watchlist_id,
        )

        # Get the watchlist
        watchlist = await self._watchlist_repo.get_watchlist(watchlist_id)
        if watchlist is None:
            self._logger.warning("Watchlist not found", watchlist_id=watchlist_id)
            raise EntityNotFoundError("Watchlist", watchlist_id)

        # Get all items in the watchlist
        items = await self._watchlist_repo.list_items(watchlist_id)

        # Enrich each item with page details
        enriched_pages: list[WatchlistPageInfo] = []
        for item in items:
            try:
                page = await self._page_repo.get(item.page_id)
                if page is None:
                    self._logger.warning(
                        "Page not found for watchlist item",
                        page_id=item.page_id,
                        watchlist_id=watchlist_id,
                    )
                    continue

                # Get the score
                score = await self._scoring_repo.get_latest_by_page_id(item.page_id)
                shop_score = score.score if score else 0.0
                tier = score.tier if score else "XS"

                enriched_pages.append(
                    WatchlistPageInfo(
                        page_id=item.page_id,
                        page_name=page.domain,
                        url=str(page.url),
                        country=str(page.country) if page.country else None,
                        is_shopify=page.is_shopify,
                        shop_score=shop_score,
                        tier=tier,
                        active_ads_count=page.active_ads_count,
                        added_at=item.created_at,
                    )
                )
            except Exception as exc:
                self._logger.error(
                    "Error enriching watchlist item",
                    page_id=item.page_id,
                    error=str(exc),
                )
                continue

        self._logger.debug(
            "Got watchlist with details",
            watchlist_id=watchlist_id,
            pages_count=len(enriched_pages),
        )

        return WatchlistWithDetails(
            id=watchlist.id,
            name=watchlist.name,
            description=watchlist.description,
            created_at=watchlist.created_at,
            is_active=watchlist.is_active,
            pages_count=len(enriched_pages),
            pages=enriched_pages,
        )


@dataclass
class WatchlistSummary:
    """Summary information for a watchlist.

    Used in list views where full page details aren't needed.
    """

    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool
    pages_count: int


class ListWatchlistsWithCountsUseCase:
    """Use case for listing watchlists with item counts.

    This use case retrieves watchlists with their page counts
    for display in list views.
    """

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WatchlistSummary]:
        """Execute the list watchlists with counts use case.

        Args:
            limit: Maximum number of watchlists to return.
            offset: Number of watchlists to skip.

        Returns:
            List of WatchlistSummary with page counts.
        """
        self._logger.debug(
            "Listing watchlists with counts",
            limit=limit,
            offset=offset,
        )

        watchlists = await self._watchlist_repo.list_watchlists(
            limit=limit,
            offset=offset,
        )

        summaries: list[WatchlistSummary] = []
        for watchlist in watchlists:
            # Get item count for each watchlist
            items = await self._watchlist_repo.list_items(watchlist.id)
            summaries.append(
                WatchlistSummary(
                    id=watchlist.id,
                    name=watchlist.name,
                    description=watchlist.description,
                    created_at=watchlist.created_at,
                    is_active=watchlist.is_active,
                    pages_count=len(items),
                )
            )

        self._logger.debug(
            "Listed watchlists with counts",
            count=len(summaries),
        )

        return summaries


class GetPageWatchlistsUseCase:
    """Use case for finding which watchlists contain a page.

    This is useful for showing watchlist badges on page detail views.
    """

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(self, page_id: str) -> list[Watchlist]:
        """Execute the get page watchlists use case.

        Args:
            page_id: The page identifier to search for.

        Returns:
            List of Watchlist entities that contain this page.
        """
        self._logger.debug(
            "Getting watchlists for page",
            page_id=page_id,
        )

        # Get all watchlists
        all_watchlists = await self._watchlist_repo.list_watchlists(limit=1000)

        # Filter to those containing this page
        containing_watchlists: list[Watchlist] = []
        for watchlist in all_watchlists:
            is_in = await self._watchlist_repo.is_page_in_watchlist(
                watchlist_id=watchlist.id,
                page_id=page_id,
            )
            if is_in:
                containing_watchlists.append(watchlist)

        self._logger.debug(
            "Found watchlists for page",
            page_id=page_id,
            count=len(containing_watchlists),
        )

        return containing_watchlists

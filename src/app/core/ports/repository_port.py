"""Repository Ports.

Interfaces for data persistence operations.
"""

from typing import Protocol, Sequence

from ..domain.entities import (
    Page,
    Ad,
    Scan,
    KeywordRun,
    ShopScore,
    RankedShop,
    Watchlist,
    WatchlistItem,
    Alert,
    Product,
)
from ..domain.value_objects import ScanId, RankingCriteria


class PageRepository(Protocol):
    """Port interface for Page entity persistence.

    Defines the contract for storing and retrieving Page entities.
    Implementations will handle the actual database operations.
    """

    async def save(self, page: Page) -> None:
        """Save or update a page.

        Args:
            page: The Page entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def get(self, page_id: str) -> Page | None:
        """Retrieve a page by its ID.

        Args:
            page_id: The unique page identifier.

        Returns:
            The Page entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def exists(self, page_id: str) -> bool:
        """Check if a page exists.

        Args:
            page_id: The unique page identifier.

        Returns:
            True if the page exists, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_all(self) -> list[Page]:
        """List all pages.

        Returns:
            List of all Page entities.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def is_blacklisted(self, page_id: str) -> bool:
        """Check if a page is blacklisted.

        Args:
            page_id: The unique page identifier.

        Returns:
            True if the page is blacklisted, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def blacklist(self, page_id: str) -> None:
        """Add a page to the blacklist.

        Args:
            page_id: The unique page identifier.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class AdsRepository(Protocol):
    """Port interface for Ad entity persistence.

    Defines the contract for storing and retrieving Ad entities.
    """

    async def save_many(self, ads: Sequence[Ad]) -> None:
        """Save multiple ads in batch.

        Args:
            ads: Sequence of Ad entities to save.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_by_page(self, page_id: str) -> list[Ad]:
        """List all ads for a specific page.

        Args:
            page_id: The page identifier to filter by.

        Returns:
            List of Ad entities for the page.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class ScanRepository(Protocol):
    """Port interface for Scan entity persistence.

    Defines the contract for storing and retrieving Scan entities.
    """

    async def save_scan(self, scan: Scan) -> None:
        """Save or update a scan.

        Args:
            scan: The Scan entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def get_scan(self, scan_id: ScanId) -> Scan | None:
        """Retrieve a scan by its ID.

        Args:
            scan_id: The unique scan identifier.

        Returns:
            The Scan entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class KeywordRunRepository(Protocol):
    """Port interface for KeywordRun entity persistence.

    Defines the contract for storing and retrieving KeywordRun entities.
    """

    async def save(self, run: KeywordRun) -> None:
        """Save or update a keyword run.

        Args:
            run: The KeywordRun entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_recent(self, limit: int = 50) -> list[KeywordRun]:
        """List recent keyword runs.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            List of recent KeywordRun entities, ordered by creation date desc.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class ScoringRepository(Protocol):
    """Port interface for ShopScore entity persistence.

    Defines the contract for storing and retrieving ShopScore entities.
    """

    async def save(self, score: ShopScore) -> None:
        """Save a shop score.

        Args:
            score: The ShopScore entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def get_latest_by_page_id(self, page_id: str) -> ShopScore | None:
        """Retrieve the most recent score for a page.

        Args:
            page_id: The unique page identifier.

        Returns:
            The most recent ShopScore for the page, or None if no scores exist.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_top(self, limit: int = 50, offset: int = 0) -> list[ShopScore]:
        """List top-scoring pages.

        Returns scores ordered by score descending (highest first),
        then by created_at descending for ties.

        Args:
            limit: Maximum number of scores to return.
            offset: Number of scores to skip.

        Returns:
            List of ShopScore entities ordered by score descending.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def count(self) -> int:
        """Count total number of shop scores.

        Returns:
            The total count of ShopScore entities.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_ranked(
        self,
        criteria: RankingCriteria,
    ) -> list[RankedShop]:
        """Return a ranked list of shops matching the criteria.

        Shops are ordered by score descending, then by created_at descending
        for ties. Applies filters from criteria (tier, min_score, country).

        Args:
            criteria: The ranking criteria including filters and pagination.

        Returns:
            List of RankedShop projections matching the criteria.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def count_ranked(
        self,
        criteria: RankingCriteria,
    ) -> int:
        """Return total count of shops matching the criteria.

        Counts shops matching the same filters as list_ranked (tier, min_score,
        country) but ignores limit/offset for pagination purposes.

        Args:
            criteria: The ranking criteria including filters (limit/offset ignored).

        Returns:
            Total count of shops matching the filter criteria.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class WatchlistRepository(Protocol):
    """Port interface for Watchlist entity persistence.

    Defines the contract for storing and retrieving Watchlist and
    WatchlistItem entities.
    """

    async def create_watchlist(self, watchlist: Watchlist) -> Watchlist:
        """Create a new watchlist.

        Args:
            watchlist: The Watchlist entity to create.

        Returns:
            The created Watchlist entity.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def get_watchlist(self, watchlist_id: str) -> Watchlist | None:
        """Retrieve a watchlist by its ID.

        Args:
            watchlist_id: The unique watchlist identifier.

        Returns:
            The Watchlist entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_watchlists(
        self, limit: int = 50, offset: int = 0
    ) -> list[Watchlist]:
        """List all watchlists.

        Returns watchlists ordered by created_at descending (newest first).

        Args:
            limit: Maximum number of watchlists to return.
            offset: Number of watchlists to skip.

        Returns:
            List of Watchlist entities.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def add_item(self, item: WatchlistItem) -> WatchlistItem:
        """Add a page to a watchlist.

        Args:
            item: The WatchlistItem entity to add.

        Returns:
            The created WatchlistItem entity.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def remove_item(self, watchlist_id: str, page_id: str) -> None:
        """Remove a page from a watchlist.

        Args:
            watchlist_id: The watchlist identifier.
            page_id: The page identifier to remove.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_items(self, watchlist_id: str) -> list[WatchlistItem]:
        """List all items in a watchlist.

        Returns items ordered by created_at ascending (oldest first).

        Args:
            watchlist_id: The watchlist identifier.

        Returns:
            List of WatchlistItem entities.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def is_page_in_watchlist(self, watchlist_id: str, page_id: str) -> bool:
        """Check if a page is already in a watchlist.

        Args:
            watchlist_id: The watchlist identifier.
            page_id: The page identifier.

        Returns:
            True if the page is in the watchlist, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class AlertRepository(Protocol):
    """Port interface for Alert entity persistence.

    Defines the contract for storing and retrieving Alert entities
    created during shop rescoring operations.
    """

    async def save(self, alert: Alert) -> Alert:
        """Save a new alert.

        Args:
            alert: The Alert entity to save.

        Returns:
            The saved Alert entity.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_by_page(
        self, page_id: str, limit: int = 50, offset: int = 0
    ) -> list[Alert]:
        """List all alerts for a specific page.

        Returns alerts ordered by created_at descending (newest first).

        Args:
            page_id: The page identifier to filter by.
            limit: Maximum number of alerts to return.
            offset: Number of alerts to skip.

        Returns:
            List of Alert entities for the page.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_recent(self, limit: int = 100) -> list[Alert]:
        """List recent alerts across all pages.

        Returns alerts ordered by created_at descending (newest first).

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            List of recent Alert entities.

        Raises:
            RepositoryError: On database errors.
        """
        ...


class ProductRepository(Protocol):
    """Port interface for Product entity persistence.

    Defines the contract for storing and retrieving Product entities
    from a store's catalog.
    """

    async def upsert_many(self, products: Sequence[Product]) -> None:
        """Upsert multiple products in batch.

        Updates existing products (matched by page_id + handle) or inserts
        new ones. This enables efficient catalog synchronization.

        Args:
            products: Sequence of Product entities to upsert.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def list_by_page(
        self, page_id: str, limit: int = 50, offset: int = 0
    ) -> list[Product]:
        """List all products for a specific page (store).

        Returns products ordered by title ascending.

        Args:
            page_id: The page identifier to filter by.
            limit: Maximum number of products to return.
            offset: Number of products to skip.

        Returns:
            List of Product entities for the page.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def get_by_id(self, product_id: str) -> Product | None:
        """Retrieve a product by its ID.

        Args:
            product_id: The unique product identifier.

        Returns:
            The Product entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def delete_by_page(self, page_id: str) -> int:
        """Delete all products for a page.

        Used for full catalog resync operations.

        Args:
            page_id: The page identifier whose products to delete.

        Returns:
            Number of products deleted.

        Raises:
            RepositoryError: On database errors.
        """
        ...

    async def count_by_page(self, page_id: str) -> int:
        """Count products for a specific page.

        Args:
            page_id: The page identifier to count products for.

        Returns:
            Total count of products for the page.

        Raises:
            RepositoryError: On database errors.
        """
        ...

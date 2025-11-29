"""Repository Ports.

Interfaces for data persistence operations.
"""

from typing import Protocol, Sequence

from ..domain.entities import Page, Ad, Scan, KeywordRun, ShopScore, RankedShop
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

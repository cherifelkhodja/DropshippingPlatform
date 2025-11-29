"""Ranked Shop Entities.

Read-model projections for ranked shop queries.
These entities are optimized for reading and displaying ranking data,
not for domain behavior or mutations.
"""

from dataclasses import dataclass, field


@dataclass
class RankedShop:
    """Read-model projection of a shop in a ranking context.

    This entity represents a shop's ranking information, combining
    score data with basic page information for display purposes.
    It's designed for read operations (queries) rather than writes.

    Attributes:
        page_id: Unique identifier of the page/shop.
        score: The computed shop score (0-100).
        tier: The tier classification based on score ("XS", "S", "M", "L", "XL", "XXL").
        url: Optional URL of the shop.
        country: Optional ISO 3166-1 alpha-2 country code.
        name: Optional shop name or title.
    """

    page_id: str
    score: float
    tier: str
    url: str | None = None
    country: str | None = None
    name: str | None = None

    def __eq__(self, other: object) -> bool:
        """Check equality based on page_id (identity)."""
        if isinstance(other, RankedShop):
            return self.page_id == other.page_id
        return False

    def __hash__(self) -> int:
        """Hash based on page_id."""
        return hash(self.page_id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<RankedShop(page_id={self.page_id}, score={self.score:.1f}, tier={self.tier})>"
        )


@dataclass
class RankedShopsResult:
    """Result container for paginated ranked shop queries.

    Encapsulates the results of a ranking query along with
    pagination metadata for building paginated responses.

    Attributes:
        items: List of ranked shops matching the query criteria.
        total: Total count of shops matching criteria (without pagination).
        limit: Maximum items requested (page size).
        offset: Number of items skipped (for pagination).
    """

    items: list[RankedShop] = field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results beyond this page.

        Returns:
            True if there are more items to fetch after this page.
        """
        return self.offset + len(self.items) < self.total

    @property
    def page_count(self) -> int:
        """Calculate total number of pages.

        Returns:
            Total number of pages based on total items and limit.
        """
        if self.limit <= 0:
            return 0
        return (self.total + self.limit - 1) // self.limit

    @property
    def current_page(self) -> int:
        """Calculate current page number (1-indexed).

        Returns:
            Current page number starting from 1.
        """
        if self.limit <= 0:
            return 1
        return (self.offset // self.limit) + 1

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<RankedShopsResult(items={len(self.items)}, total={self.total}, "
            f"limit={self.limit}, offset={self.offset})>"
        )

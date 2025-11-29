"""Watchlist Domain Entities.

Entities for managing watchlists - collections of pages that users
want to monitor for scoring changes and alerts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Watchlist:
    """Entity representing a watchlist.

    A Watchlist is a named collection of pages that a user wants to
    track for monitoring purposes (scoring changes, alerts, etc.).

    Attributes:
        id: Unique identifier for this watchlist.
        name: Human-readable name for the watchlist (e.g., "Top FR winners").
        description: Optional description of the watchlist purpose.
        created_at: When this watchlist was created.
        is_active: Whether this watchlist is active for monitoring.
    """

    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate watchlist after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Watchlist name cannot be empty")
        # Normalize name (strip whitespace)
        object.__setattr__(self, "name", self.name.strip())

    @classmethod
    def create(
        cls,
        id: str,
        name: str,
        description: Optional[str] = None,
    ) -> "Watchlist":
        """Factory method to create a new Watchlist.

        Args:
            id: Unique identifier for the watchlist.
            name: Human-readable name for the watchlist.
            description: Optional description.

        Returns:
            A new Watchlist instance.
        """
        return cls(
            id=id,
            name=name,
            description=description,
            created_at=datetime.utcnow(),
            is_active=True,
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on identity (id)."""
        if isinstance(other, Watchlist):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<Watchlist(id={self.id}, name={self.name!r})>"


@dataclass
class WatchlistItem:
    """Entity representing an item in a watchlist.

    A WatchlistItem links a page to a watchlist, allowing the page
    to be tracked within that watchlist.

    Attributes:
        id: Unique identifier for this watchlist item.
        watchlist_id: The watchlist this item belongs to.
        page_id: The page being tracked.
        created_at: When this item was added to the watchlist.
    """

    id: str
    watchlist_id: str
    page_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        id: str,
        watchlist_id: str,
        page_id: str,
    ) -> "WatchlistItem":
        """Factory method to create a new WatchlistItem.

        Args:
            id: Unique identifier for the item.
            watchlist_id: The watchlist to add to.
            page_id: The page to track.

        Returns:
            A new WatchlistItem instance.
        """
        return cls(
            id=id,
            watchlist_id=watchlist_id,
            page_id=page_id,
            created_at=datetime.utcnow(),
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on identity (id)."""
        if isinstance(other, WatchlistItem):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<WatchlistItem(id={self.id}, "
            f"watchlist_id={self.watchlist_id}, page_id={self.page_id})>"
        )

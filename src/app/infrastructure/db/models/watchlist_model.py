"""Watchlist ORM Models.

SQLAlchemy models for the watchlists and watchlist_items tables.
No domain logic - purely structural.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base


class WatchlistModel(Base):
    """ORM model for watchlists table.

    Represents a named collection of pages for monitoring.
    Maps to the Watchlist domain entity (mapping done in mappers).

    Attributes:
        id: Primary key UUID.
        name: Human-readable name for the watchlist.
        description: Optional description of the watchlist.
        created_at: When this watchlist was created.
        is_active: Whether this watchlist is active.
    """

    __tablename__ = "watchlists"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationship to items
    items: Mapped[list["WatchlistItemModel"]] = relationship(
        "WatchlistItemModel",
        back_populates="watchlist",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<WatchlistModel(id={self.id}, name={self.name!r})>"


class WatchlistItemModel(Base):
    """ORM model for watchlist_items table.

    Represents a page tracked in a watchlist.
    Maps to the WatchlistItem domain entity (mapping done in mappers).

    Attributes:
        id: Primary key UUID.
        watchlist_id: Foreign key to watchlists table.
        page_id: Foreign key to pages table.
        created_at: When this item was added.
    """

    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "page_id", name="uq_watchlist_items_watchlist_page"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    watchlist_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationship to watchlist
    watchlist: Mapped["WatchlistModel"] = relationship(
        "WatchlistModel",
        back_populates="items",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<WatchlistItemModel(id={self.id}, "
            f"watchlist_id={self.watchlist_id}, page_id={self.page_id})>"
        )

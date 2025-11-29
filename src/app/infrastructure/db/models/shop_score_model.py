"""Shop Score ORM Model.

SQLAlchemy model for the shop_scores table.
No domain logic - purely structural.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base


class ShopScoreModel(Base):
    """ORM model for shop_scores table.

    Represents a computed score for a page/shop at a specific point in time.
    Maps to the ShopScore domain entity (mapping done in mappers).

    Attributes:
        id: Primary key UUID.
        page_id: Foreign key to pages table.
        score: The computed overall score (0-100).
        components: JSONB containing component sub-scores.
        created_at: When this score was computed.
    """

    __tablename__ = "shop_scores"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        index=True,
    )
    components: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Relationship
    page: Mapped["PageModel"] = relationship(  # noqa: F821
        "PageModel",
        back_populates="shop_scores",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<ShopScoreModel(id={self.id}, page_id={self.page_id}, score={self.score:.1f})>"

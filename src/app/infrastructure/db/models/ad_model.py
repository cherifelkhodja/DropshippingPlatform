"""Ad ORM Model.

SQLAlchemy model for the ads table.
No domain logic - purely structural.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base

if TYPE_CHECKING:
    from src.app.infrastructure.db.models.page_model import PageModel


class AdModel(Base):
    """ORM model for ads table.

    Represents a Meta advertisement in the database.
    Maps to the Ad domain entity (mapping done in adapters).

    Attributes:
        id: Primary key UUID.
        page_id: Foreign key to pages table.
        meta_page_id: Meta/Facebook page ID.
        meta_ad_id: Original Meta ad library ID.
        title: Ad title/headline.
        body: Ad body text/description.
        link_url: Destination URL of the ad.
        image_url: URL to the ad creative image.
        video_url: URL to the ad video.
        cta_type: Call-to-action type.
        status: Current status (active/inactive/unknown).
        platforms: Platforms where ad is shown (JSONB array).
        countries: Target countries (JSONB array).
        started_at: When ad started running.
        ended_at: When ad stopped running.
        impressions_lower: Lower bound of impression estimate.
        impressions_upper: Upper bound of impression estimate.
        spend_lower: Lower bound of spend estimate.
        spend_upper: Upper bound of spend estimate.
        currency: Currency for spend estimates.
        first_seen_at: When we first detected this ad.
        last_seen_at: When we last saw this ad active.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "ads"

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
    meta_page_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    meta_ad_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    link_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    platforms: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    countries: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    impressions_lower: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impressions_upper: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spend_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    spend_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    page: Mapped["PageModel"] = relationship(
        "PageModel",
        back_populates="ads",
    )
    creative_analysis: Mapped["CreativeAnalysisModel"] = relationship(  # noqa: F821
        "CreativeAnalysisModel",
        back_populates="ad",
        uselist=False,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<AdModel(id={self.id}, meta_ad_id={self.meta_ad_id})>"

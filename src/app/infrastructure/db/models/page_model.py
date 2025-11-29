"""Page ORM Model.

SQLAlchemy model for the pages table.
No domain logic - purely structural.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base

if TYPE_CHECKING:
    from src.app.infrastructure.db.models.ad_model import AdModel
    from src.app.infrastructure.db.models.scan_model import ScanModel
    from src.app.infrastructure.db.models.shop_score_model import ShopScoreModel


class PageModel(Base):
    """ORM model for pages table.

    Represents a tracked page/store in the database.
    Maps to the Page domain entity (mapping done in adapters).

    Attributes:
        id: Primary key UUID.
        url: Full URL of the page.
        domain: Domain extracted from URL.
        state: Current state in tracking pipeline.
        country: ISO 3166-1 alpha-2 country code.
        language: ISO 639-1 language code.
        currency: ISO 4217 currency code.
        category: Product category.
        product_count: Number of products in store.
        is_shopify: Whether confirmed as Shopify store.
        shopify_profile_id: Reference to ShopifyProfile.
        active_ads_count: Number of currently active ads.
        total_ads_count: Total ads ever detected.
        score: Computed relevance/quality score.
        first_seen_at: When page was first discovered.
        last_scanned_at: When page was last analyzed.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    __tablename__ = "pages"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(50), nullable=False, default="discovered")
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    language: Mapped[str | None] = mapped_column(String(2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_shopify: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    shopify_profile_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    active_ads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_ads_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    first_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_scanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    ads: Mapped[list["AdModel"]] = relationship(
        "AdModel",
        back_populates="page",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    scans: Mapped[list["ScanModel"]] = relationship(
        "ScanModel",
        back_populates="page",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    shop_scores: Mapped[list["ShopScoreModel"]] = relationship(
        "ShopScoreModel",
        back_populates="page",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<PageModel(id={self.id}, domain={self.domain})>"

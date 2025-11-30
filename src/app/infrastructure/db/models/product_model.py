"""Product ORM Model.

SQLAlchemy model for the products table.
No domain logic - purely structural.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.infrastructure.db.models.base import Base

if TYPE_CHECKING:
    from src.app.infrastructure.db.models.page_model import PageModel


class ProductModel(Base):
    """ORM model for products table.

    Represents a product from a store's catalog in the database.
    Maps to the Product domain entity (mapping done in adapters).

    Attributes:
        id: Primary key UUID.
        page_id: Foreign key to pages table.
        handle: Shopify product handle (URL slug).
        title: Product title/name.
        url: Full URL to product page.
        price_min: Minimum price across variants.
        price_max: Maximum price across variants.
        currency: Currency code (e.g., "EUR").
        available: Whether product is available.
        tags: Array of product tags.
        vendor: Product vendor/brand.
        image_url: URL to main product image.
        product_type: Product type classification.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
        raw_data: Original JSON data from source.
    """

    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    handle: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    price_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(100)),
        nullable=False,
        default=list,
    )
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Unique constraint on (page_id, handle) for upsert operations
    __table_args__ = (
        UniqueConstraint("page_id", "handle", name="uq_products_page_id_handle"),
    )

    # Relationship to Page (not using FK constraint to avoid migration complexity)
    # The page_id column references pages.id logically

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<ProductModel(id={self.id}, handle={self.handle})>"

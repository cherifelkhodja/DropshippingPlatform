"""Page Daily Metrics ORM Model.

SQLAlchemy model for the page_daily_metrics table.
No domain logic - purely structural.

Sprint 7: Historisation & Time Series
This model stores daily snapshots of page metrics for time series analysis.
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.app.infrastructure.db.models.base import Base


class PageDailyMetricsModel(Base):
    """ORM model for page_daily_metrics table.

    Represents a daily snapshot of metrics for a page in the database.
    Maps to the PageDailyMetrics domain entity (mapping done in adapters).

    Attributes:
        id: Primary key UUID.
        page_id: Foreign key to pages table.
        date: The date of this snapshot (YYYY-MM-DD).
        ads_count: Number of active ads at snapshot time.
        shop_score: The computed shop score (0-100) at snapshot time.
        tier: The tier classification (XXL, XL, L, M, S, XS).
        products_count: Number of products in catalog (optional).
        created_at: When this snapshot was recorded.
    """

    __tablename__ = "page_daily_metrics"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
    )
    page_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ads_count: Mapped[int] = mapped_column(Integer, nullable=False)
    shop_score: Mapped[float] = mapped_column(Float, nullable=False)
    tier: Mapped[str] = mapped_column(String(10), nullable=False)
    products_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    # Unique constraint: one snapshot per page per date
    __table_args__ = (
        UniqueConstraint("page_id", "date", name="uq_page_daily_metrics_page_id_date"),
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"<PageDailyMetricsModel(id={self.id}, page_id={self.page_id}, "
            f"date={self.date}, score={self.shop_score})>"
        )

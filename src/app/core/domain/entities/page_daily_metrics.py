"""Page Daily Metrics Entity.

Represents a daily snapshot of metrics for a page/shop at a specific date.
Used for historical tracking and time series analysis (trends, weak signals).

Usage:
    This entity is the foundation for the Historisation & Time Series feature
    (Sprint 7). Each snapshot captures the key metrics of a page at a given date,
    enabling:
    - Evolution graphs (ads count, score over time)
    - Trend detection (growth, decline patterns)
    - Weak signals identification (early warning indicators)
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from ..tiering import score_to_tier


@dataclass
class PageDailyMetrics:
    """Entity representing a daily metrics snapshot for a page.

    Captures the state of a page's key metrics at a specific date.
    One snapshot per page per day is stored (enforced by unique constraint).

    Attributes:
        id: Unique identifier for this snapshot record.
        page_id: The page this snapshot belongs to.
        date: The date of this snapshot (YYYY-MM-DD).
        ads_count: Number of active ads at snapshot time.
        shop_score: The computed shop score (0-100) at snapshot time.
        tier: The tier classification (computed from shop_score).
        products_count: Number of products in catalog (optional).
        created_at: When this snapshot was recorded.
    """

    id: str
    page_id: str
    date: date
    ads_count: int
    shop_score: float
    tier: str
    products_count: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate and normalize values after initialization."""
        # Clamp shop_score to 0-100 range
        clamped_score = max(0.0, min(100.0, self.shop_score))
        object.__setattr__(self, "shop_score", clamped_score)

        # Ensure ads_count is non-negative
        if self.ads_count < 0:
            object.__setattr__(self, "ads_count", 0)

        # Ensure tier is valid (recalculate from score if needed)
        valid_tier = score_to_tier(clamped_score)
        if self.tier != valid_tier:
            object.__setattr__(self, "tier", valid_tier)

    @classmethod
    def create(
        cls,
        id: str,
        page_id: str,
        snapshot_date: date,
        ads_count: int,
        shop_score: float,
        products_count: Optional[int] = None,
    ) -> "PageDailyMetrics":
        """Factory method to create a new PageDailyMetrics snapshot.

        The tier is automatically computed from the shop_score using
        the centralized tiering logic (core/domain/tiering.py).

        Args:
            id: Unique identifier for the snapshot.
            page_id: The page this snapshot belongs to.
            snapshot_date: The date of this snapshot.
            ads_count: Number of active ads.
            shop_score: The computed shop score (0-100).
            products_count: Optional number of products.

        Returns:
            A new PageDailyMetrics instance.
        """
        # Compute tier from score using centralized logic
        tier = score_to_tier(shop_score)

        return cls(
            id=id,
            page_id=page_id,
            date=snapshot_date,
            ads_count=ads_count,
            shop_score=shop_score,
            tier=tier,
            products_count=products_count,
            created_at=datetime.utcnow(),
        )

    def is_high_performing(self, threshold: float = 70.0) -> bool:
        """Check if this snapshot indicates a high-performing page.

        Args:
            threshold: The minimum score to be considered high performing.

        Returns:
            True if shop_score meets or exceeds the threshold.
        """
        return self.shop_score >= threshold

    def is_low_performing(self, threshold: float = 30.0) -> bool:
        """Check if this snapshot indicates a low-performing page.

        Args:
            threshold: The maximum score to be considered low performing.

        Returns:
            True if shop_score is below the threshold.
        """
        return self.shop_score < threshold

    def has_active_ads(self) -> bool:
        """Check if the page had active ads at this snapshot."""
        return self.ads_count > 0

    def __eq__(self, other: object) -> bool:
        """Check equality based on identity (id)."""
        if isinstance(other, PageDailyMetrics):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<PageDailyMetrics(id={self.id}, page_id={self.page_id}, "
            f"date={self.date}, score={self.shop_score:.1f}, tier={self.tier})>"
        )


@dataclass(frozen=True)
class PageMetricsHistoryResult:
    """Result of a page metrics history query.

    Attributes:
        page_id: The page identifier.
        metrics: List of daily metrics snapshots, ordered by date ASC.
    """

    page_id: str
    metrics: list[PageDailyMetrics]

    @property
    def count(self) -> int:
        """Number of snapshots in the history."""
        return len(self.metrics)

    @property
    def first_date(self) -> date | None:
        """First date in the history, or None if empty."""
        return self.metrics[0].date if self.metrics else None

    @property
    def last_date(self) -> date | None:
        """Last date in the history, or None if empty."""
        return self.metrics[-1].date if self.metrics else None

    @property
    def score_trend(self) -> float | None:
        """Calculate simple score trend (last - first).

        Returns:
            Score difference between last and first snapshot,
            or None if less than 2 snapshots.
        """
        if len(self.metrics) < 2:
            return None
        return self.metrics[-1].shop_score - self.metrics[0].shop_score

    @property
    def ads_trend(self) -> int | None:
        """Calculate simple ads count trend (last - first).

        Returns:
            Ads count difference between last and first snapshot,
            or None if less than 2 snapshots.
        """
        if len(self.metrics) < 2:
            return None
        return self.metrics[-1].ads_count - self.metrics[0].ads_count

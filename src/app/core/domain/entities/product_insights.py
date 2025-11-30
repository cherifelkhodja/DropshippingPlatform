"""Product Insights Read-Model.

A read-model entity representing product insights with ad matching information.
This is a computed/derived entity that is not persisted to the database.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from .product import Product
from .ad import Ad


class MatchStrength(Enum):
    """Enumeration of match strength levels."""

    STRONG = "strong"  # URL/handle direct match
    MEDIUM = "medium"  # Handle in ad text
    WEAK = "weak"  # Text similarity only
    NONE = "none"  # No match


@dataclass(frozen=True)
class AdMatch:
    """Represents a match between a product and an ad.

    Attributes:
        ad: The matched Ad entity.
        score: Match confidence score (0.0 to 1.0).
        strength: Overall match strength level.
        reasons: List of reasons why this match was detected.
    """

    ad: Ad
    score: float
    strength: MatchStrength
    reasons: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate score is within bounds."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0 and 1, got {self.score}")


@dataclass(frozen=True)
class ProductInsights:
    """Read-model for product insights with ad matching.

    This entity aggregates information about a product and its
    relationship to advertising campaigns. It is computed on-the-fly
    and not persisted.

    Attributes:
        product: The Product entity.
        matched_ads: List of ads matched to this product.
        total_ads_analyzed: Total number of ads analyzed for matching.
        match_score: Overall match score (0.0 to 1.0).
        match_reasons: Combined list of match reasons.
        is_promoted: Whether the product appears to be actively promoted.
        has_strong_match: Whether there's at least one strong match.
        best_match: The highest-scoring ad match (if any).
        computed_at: When insights were computed.
    """

    product: Product
    matched_ads: list[AdMatch] = field(default_factory=list)
    total_ads_analyzed: int = 0
    computed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def match_score(self) -> float:
        """Calculate overall match score from matched ads."""
        if not self.matched_ads:
            return 0.0
        # Use the best match score as the overall score
        return max(match.score for match in self.matched_ads)

    @property
    def match_reasons(self) -> list[str]:
        """Aggregate all unique match reasons."""
        reasons: set[str] = set()
        for match in self.matched_ads:
            reasons.update(match.reasons)
        return sorted(reasons)

    @property
    def is_promoted(self) -> bool:
        """Check if product appears to be actively promoted.

        A product is considered promoted if it has at least one
        medium or strong match with an active ad.
        """
        for match in self.matched_ads:
            if match.strength in (MatchStrength.STRONG, MatchStrength.MEDIUM):
                if match.ad.is_active():
                    return True
        return False

    @property
    def has_strong_match(self) -> bool:
        """Check if there's at least one strong match."""
        return any(
            match.strength == MatchStrength.STRONG
            for match in self.matched_ads
        )

    @property
    def best_match(self) -> Optional[AdMatch]:
        """Get the highest-scoring ad match."""
        if not self.matched_ads:
            return None
        return max(self.matched_ads, key=lambda m: (m.score, m.strength.value))

    @property
    def strong_matches_count(self) -> int:
        """Count of strong matches."""
        return sum(
            1 for match in self.matched_ads
            if match.strength == MatchStrength.STRONG
        )

    @property
    def medium_matches_count(self) -> int:
        """Count of medium matches."""
        return sum(
            1 for match in self.matched_ads
            if match.strength == MatchStrength.MEDIUM
        )

    @property
    def weak_matches_count(self) -> int:
        """Count of weak matches."""
        return sum(
            1 for match in self.matched_ads
            if match.strength == MatchStrength.WEAK
        )

    def get_active_ad_matches(self) -> list[AdMatch]:
        """Get only matches with currently active ads."""
        return [
            match for match in self.matched_ads
            if match.ad.is_active()
        ]

    def has_match_above_threshold(self, threshold: float = 0.5) -> bool:
        """Check if any match exceeds the given threshold."""
        return any(match.score >= threshold for match in self.matched_ads)


@dataclass(frozen=True)
class PageProductInsights:
    """Aggregated product insights for an entire page/store.

    Attributes:
        page_id: The page identifier.
        product_insights: List of insights for each product.
        total_products: Total number of products analyzed.
        total_ads: Total number of ads analyzed.
        products_with_ads: Count of products that have at least one ad match.
        promoted_products_count: Count of products appearing to be promoted.
        computed_at: When insights were computed.
    """

    page_id: str
    product_insights: list[ProductInsights] = field(default_factory=list)
    total_products: int = 0
    total_ads: int = 0
    computed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def products_with_ads(self) -> int:
        """Count of products with at least one matched ad."""
        return sum(
            1 for insight in self.product_insights
            if insight.matched_ads
        )

    @property
    def promoted_products_count(self) -> int:
        """Count of products that appear to be promoted."""
        return sum(
            1 for insight in self.product_insights
            if insight.is_promoted
        )

    @property
    def coverage_ratio(self) -> float:
        """Ratio of products with ad matches to total products."""
        if self.total_products == 0:
            return 0.0
        return self.products_with_ads / self.total_products

    @property
    def promotion_ratio(self) -> float:
        """Ratio of promoted products to total products."""
        if self.total_products == 0:
            return 0.0
        return self.promoted_products_count / self.total_products

    def get_promoted_products(self) -> list[ProductInsights]:
        """Get insights for products that are promoted."""
        return [
            insight for insight in self.product_insights
            if insight.is_promoted
        ]

    def get_products_with_strong_matches(self) -> list[ProductInsights]:
        """Get insights for products with strong ad matches."""
        return [
            insight for insight in self.product_insights
            if insight.has_strong_match
        ]

    def get_top_products_by_score(self, limit: int = 10) -> list[ProductInsights]:
        """Get top products sorted by match score."""
        sorted_insights = sorted(
            self.product_insights,
            key=lambda i: i.match_score,
            reverse=True,
        )
        return sorted_insights[:limit]

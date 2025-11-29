"""Shop Score Entity.

Represents a computed score for a page/shop at a specific point in time.
Used for tracking and ranking shops by their quality and relevance metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..tiering import score_to_tier


@dataclass
class ShopScore:
    """Entity representing a computed shop score.

    A ShopScore captures the computed relevance/quality score for a page
    at a specific point in time, along with the component sub-scores
    that contributed to the final score.

    Attributes:
        id: Unique identifier for this score record.
        page_id: The page this score belongs to.
        score: The overall computed score (0-100).
        components: Dictionary of sub-scores contributing to the final score.
        created_at: When this score was computed.
    """

    id: str
    page_id: str
    score: float
    components: dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate and normalize score after initialization."""
        # Clamp score to 0-100 range
        clamped_score = max(0.0, min(100.0, self.score))
        object.__setattr__(self, "score", clamped_score)

    @classmethod
    def create(
        cls,
        id: str,
        page_id: str,
        score: float,
        components: Optional[dict[str, float]] = None,
    ) -> "ShopScore":
        """Factory method to create a new ShopScore.

        Args:
            id: Unique identifier for the score.
            page_id: The page this score belongs to.
            score: The overall computed score (will be clamped to 0-100).
            components: Optional dictionary of component sub-scores.

        Returns:
            A new ShopScore instance.
        """
        return cls(
            id=id,
            page_id=page_id,
            score=score,
            components=components or {},
            created_at=datetime.utcnow(),
        )

    def is_high_quality(self, threshold: float = 70.0) -> bool:
        """Check if this score indicates a high-quality shop.

        Args:
            threshold: The minimum score to be considered high quality.

        Returns:
            True if score meets or exceeds the threshold.
        """
        return self.score >= threshold

    def is_low_quality(self, threshold: float = 30.0) -> bool:
        """Check if this score indicates a low-quality shop.

        Args:
            threshold: The maximum score to be considered low quality.

        Returns:
            True if score is below the threshold.
        """
        return self.score < threshold

    def get_component(self, name: str, default: float = 0.0) -> float:
        """Get a specific component score.

        Args:
            name: The component name.
            default: Default value if component not found.

        Returns:
            The component score or default value.
        """
        return self.components.get(name, default)

    @property
    def tier(self) -> str:
        """Get the tier classification based on score.

        Tier classification is delegated to the central tiering module
        (core/domain/tiering.py) which is the single source of truth
        for all tier-related logic.

        Tiers are based on score ranges:
        - XXL: 85-100
        - XL: 70-85
        - L: 55-70
        - M: 40-55
        - S: 25-40
        - XS: 0-25

        Returns:
            The tier as a string (XS, S, M, L, XL, XXL).
        """
        return score_to_tier(self.score)

    def __eq__(self, other: object) -> bool:
        """Check equality based on identity (id)."""
        if isinstance(other, ShopScore):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<ShopScore(id={self.id}, page_id={self.page_id}, score={self.score:.1f})>"
        )

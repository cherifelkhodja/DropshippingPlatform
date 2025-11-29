"""Ranking Value Objects.

Value objects for ranking criteria and related ranking domain concepts.

Note:
    Tier definitions and score ranges are managed by the central tiering module
    (core/domain/tiering.py). This module imports from there to ensure consistency.
"""

from dataclasses import dataclass
from typing import ClassVar

from ..errors import DomainError
from ..tiering import TIER_SCORE_RANGES, VALID_TIERS, tier_to_score_range


class InvalidRankingCriteriaError(DomainError):
    """Raised when ranking criteria validation fails."""

    def __init__(self, reason: str) -> None:
        super().__init__(message="Invalid ranking criteria", value=reason)


# Re-export for backwards compatibility (consumers may import from here)
# These are now sourced from core/domain/tiering.py
__all__ = ["RankingCriteria", "InvalidRankingCriteriaError", "VALID_TIERS", "TIER_SCORE_RANGES"]


@dataclass(frozen=True)
class RankingCriteria:
    """Immutable value object representing criteria for ranking shops.

    This value object encapsulates the parameters used to filter and paginate
    ranked shop queries.

    Attributes:
        limit: Maximum number of results to return (1-200, default 50).
        offset: Number of results to skip for pagination (>= 0, default 0).
        tier: Optional tier filter ("XS", "S", "M", "L", "XL", "XXL").
        min_score: Optional minimum score filter (0-100).
        country: Optional country code filter (ISO 3166-1 alpha-2, e.g., "US", "FR").
    """

    # Class constants for validation
    MIN_LIMIT: ClassVar[int] = 1
    MAX_LIMIT: ClassVar[int] = 200
    DEFAULT_LIMIT: ClassVar[int] = 50

    limit: int = 50
    offset: int = 0
    tier: str | None = None
    min_score: float | None = None
    country: str | None = None

    def __post_init__(self) -> None:
        """Validate and normalize criteria after initialization."""
        # Validate and clamp limit
        if not isinstance(self.limit, int):
            raise InvalidRankingCriteriaError(f"limit must be an integer, got {type(self.limit).__name__}")
        clamped_limit = max(self.MIN_LIMIT, min(self.MAX_LIMIT, self.limit))
        object.__setattr__(self, "limit", clamped_limit)

        # Validate offset
        if not isinstance(self.offset, int):
            raise InvalidRankingCriteriaError(f"offset must be an integer, got {type(self.offset).__name__}")
        if self.offset < 0:
            object.__setattr__(self, "offset", 0)

        # Validate tier if provided
        if self.tier is not None:
            normalized_tier = self.tier.upper() if isinstance(self.tier, str) else str(self.tier)
            if normalized_tier not in VALID_TIERS:
                raise InvalidRankingCriteriaError(
                    f"tier must be one of {sorted(VALID_TIERS)}, got '{self.tier}'"
                )
            object.__setattr__(self, "tier", normalized_tier)

        # Validate min_score if provided
        if self.min_score is not None:
            if not isinstance(self.min_score, (int, float)):
                raise InvalidRankingCriteriaError(
                    f"min_score must be a number, got {type(self.min_score).__name__}"
                )
            clamped_min_score = max(0.0, min(100.0, float(self.min_score)))
            object.__setattr__(self, "min_score", clamped_min_score)

        # Validate and normalize country if provided
        if self.country is not None:
            if not isinstance(self.country, str) or len(self.country) != 2:
                raise InvalidRankingCriteriaError(
                    f"country must be a 2-letter ISO code, got '{self.country}'"
                )
            object.__setattr__(self, "country", self.country.upper())

    def get_tier_score_range(self) -> tuple[float, float] | None:
        """Get the score range for the current tier filter.

        Uses the central tiering module (core/domain/tiering.py) for
        tier-to-score-range conversion.

        Returns:
            Tuple of (min_score, max_score) for the tier, or None if no tier filter.
        """
        if self.tier is None:
            return None
        return tier_to_score_range(self.tier)

    def __eq__(self, other: object) -> bool:
        """Check equality based on all criteria fields."""
        if isinstance(other, RankingCriteria):
            return (
                self.limit == other.limit
                and self.offset == other.offset
                and self.tier == other.tier
                and self.min_score == other.min_score
                and self.country == other.country
            )
        return False

    def __hash__(self) -> int:
        """Hash based on all criteria fields."""
        return hash((self.limit, self.offset, self.tier, self.min_score, self.country))

    def __repr__(self) -> str:
        """String representation for debugging."""
        filters = []
        if self.tier:
            filters.append(f"tier={self.tier}")
        if self.min_score is not None:
            filters.append(f"min_score={self.min_score}")
        if self.country:
            filters.append(f"country={self.country}")
        filter_str = ", ".join(filters) if filters else "no filters"
        return f"<RankingCriteria(limit={self.limit}, offset={self.offset}, {filter_str})>"

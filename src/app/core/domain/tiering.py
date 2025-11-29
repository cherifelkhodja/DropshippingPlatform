"""Shop Tiering Module - Single Source of Truth.

This module provides the authoritative definition of shop tiers and their
corresponding score ranges. All tier-related logic in the codebase MUST
consume this module to ensure consistency.

Tier System:
    - XXL: Premium tier (score 85-100) - Top performing shops
    - XL:  High tier (score 70-85) - Strong performers
    - L:   Upper-mid tier (score 55-70) - Good performers
    - M:   Mid tier (score 40-55) - Average performers
    - S:   Lower tier (score 25-40) - Below average performers
    - XS:  Lowest tier (score 0-25) - Weak performers

Usage:
    from src.app.core.domain.tiering import score_to_tier, tier_to_score_range

    # Convert a score to its tier
    tier = score_to_tier(92.5)  # Returns "XXL"

    # Get the score range for a tier
    min_score, max_score = tier_to_score_range("XL")  # Returns (70.0, 85.0)

Note:
    - Score ranges use inclusive lower bound, exclusive upper bound
      (except XXL which includes 100.0)
    - Tiers are case-insensitive for lookups but always returned uppercase
"""

from typing import Final


# Tier score ranges: (min_inclusive, max_exclusive)
# XXL is special: max is inclusive at 100.0
TIER_SCORE_RANGES: Final[dict[str, tuple[float, float]]] = {
    "XXL": (85.0, 100.0),
    "XL": (70.0, 85.0),
    "L": (55.0, 70.0),
    "M": (40.0, 55.0),
    "S": (25.0, 40.0),
    "XS": (0.0, 25.0),
}

# Valid tier identifiers (frozen set for immutability and O(1) lookup)
VALID_TIERS: Final[frozenset[str]] = frozenset(TIER_SCORE_RANGES.keys())

# Ordered tiers from highest to lowest (for iteration/display)
TIERS_ORDERED: Final[tuple[str, ...]] = ("XXL", "XL", "L", "M", "S", "XS")


def score_to_tier(score: float) -> str:
    """Convert a numeric score to its corresponding tier.

    The score is clamped to [0, 100] before tier determination.
    Uses the tier score ranges defined in TIER_SCORE_RANGES.

    Args:
        score: The numeric score (will be clamped to 0-100).

    Returns:
        The tier string (one of: XXL, XL, L, M, S, XS).

    Examples:
        >>> score_to_tier(92.5)
        'XXL'
        >>> score_to_tier(70.0)
        'XL'
        >>> score_to_tier(69.9)
        'L'
        >>> score_to_tier(-5)
        'XS'
        >>> score_to_tier(150)
        'XXL'
    """
    # Clamp score to valid range
    clamped = max(0.0, min(100.0, score))

    # Check tiers in descending order
    if clamped >= 85.0:
        return "XXL"
    elif clamped >= 70.0:
        return "XL"
    elif clamped >= 55.0:
        return "L"
    elif clamped >= 40.0:
        return "M"
    elif clamped >= 25.0:
        return "S"
    return "XS"


def tier_to_score_range(tier: str) -> tuple[float, float]:
    """Get the score range for a given tier.

    Args:
        tier: The tier identifier (case-insensitive).

    Returns:
        Tuple of (min_score, max_score) for the tier.
        - min_score is inclusive
        - max_score is exclusive (except for XXL where it's inclusive at 100.0)

    Raises:
        ValueError: If the tier is not valid.

    Examples:
        >>> tier_to_score_range("XXL")
        (85.0, 100.0)
        >>> tier_to_score_range("xs")
        (0.0, 25.0)
        >>> tier_to_score_range("invalid")
        ValueError: Invalid tier 'INVALID'. Valid tiers: L, M, S, XL, XS, XXL
    """
    normalized = tier.upper() if isinstance(tier, str) else str(tier).upper()

    if normalized not in VALID_TIERS:
        valid_tiers_str = ", ".join(sorted(VALID_TIERS))
        raise ValueError(
            f"Invalid tier '{normalized}'. Valid tiers: {valid_tiers_str}"
        )

    return TIER_SCORE_RANGES[normalized]


def is_valid_tier(tier: str) -> bool:
    """Check if a tier identifier is valid.

    Args:
        tier: The tier identifier to validate (case-insensitive).

    Returns:
        True if the tier is valid, False otherwise.

    Examples:
        >>> is_valid_tier("XXL")
        True
        >>> is_valid_tier("xl")
        True
        >>> is_valid_tier("invalid")
        False
    """
    if not isinstance(tier, str):
        return False
    return tier.upper() in VALID_TIERS

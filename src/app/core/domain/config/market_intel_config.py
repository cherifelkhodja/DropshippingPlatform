"""Market Intelligence Configuration - Single Source of Truth.

This module centralizes all business rules, thresholds, and configuration
constants used across the Market Intelligence platform. All modules that
need these values MUST import from here to ensure consistency.

Configuration Categories:
    - Alert Detection: Thresholds for triggering various alert types
    - Product-Ad Matching: Weights and thresholds for matching heuristics

Usage:
    from src.app.core.domain.config import (
        SCORE_CHANGE_THRESHOLD,
        MatchThresholds,
        AlertThresholds,
    )

    # Use constants directly
    if score_diff >= SCORE_CHANGE_THRESHOLD:
        # trigger alert

    # Or use config classes for grouped access
    thresholds = AlertThresholds()
    if ads_ratio >= thresholds.ads_boost_ratio:
        # trigger NEW_ADS_BOOST

Note:
    - Tiering configuration remains in src/app/core/domain/tiering.py
    - Runtime environment settings are in src/app/infrastructure/settings/
"""

from dataclasses import dataclass
from typing import Final


# =============================================================================
# ALERT DETECTION THRESHOLDS
# =============================================================================

# Score change threshold for SCORE_JUMP and SCORE_DROP alerts
# Alert triggers when score changes by this many points or more
SCORE_CHANGE_THRESHOLD: Final[float] = 10.0

# Ads boost ratio threshold for NEW_ADS_BOOST alerts
# Alert triggers when ads count increases by this ratio (1.0 = 100% increase, i.e., doubled)
ADS_BOOST_RATIO_THRESHOLD: Final[float] = 1.0


@dataclass(frozen=True)
class AlertThresholds:
    """Alert detection thresholds.

    Provides typed access to alert thresholds with defaults matching
    the module-level constants.

    Attributes:
        score_change: Points required for SCORE_JUMP/SCORE_DROP alerts.
        ads_boost_ratio: Ratio increase required for NEW_ADS_BOOST (1.0 = 100%).
    """

    score_change: float = SCORE_CHANGE_THRESHOLD
    ads_boost_ratio: float = ADS_BOOST_RATIO_THRESHOLD


# =============================================================================
# PRODUCT-AD MATCHING THRESHOLDS
# =============================================================================

# Match strength score thresholds
# These define the score cutoffs for categorizing match strength
STRONG_MATCH_THRESHOLD: Final[float] = 0.8  # >= 0.8 = strong match
MEDIUM_MATCH_THRESHOLD: Final[float] = 0.5  # >= 0.5 = medium match
WEAK_MATCH_THRESHOLD: Final[float] = 0.3    # >= 0.3 = weak match (minimum for valid match)

# Text similarity threshold for weak matches
# Minimum SequenceMatcher ratio to consider text as matching
TEXT_SIMILARITY_THRESHOLD: Final[float] = 0.6


@dataclass(frozen=True)
class MatchThresholds:
    """Product-Ad match strength thresholds.

    Defines score cutoffs for categorizing match strength levels.

    Attributes:
        strong: Minimum score for STRONG match strength.
        medium: Minimum score for MEDIUM match strength.
        weak: Minimum score for WEAK match strength (also min valid match).
        text_similarity: Minimum text similarity ratio for text-based matching.
    """

    strong: float = STRONG_MATCH_THRESHOLD
    medium: float = MEDIUM_MATCH_THRESHOLD
    weak: float = WEAK_MATCH_THRESHOLD
    text_similarity: float = TEXT_SIMILARITY_THRESHOLD


# =============================================================================
# PRODUCT-AD MATCHING WEIGHTS
# =============================================================================

# Default weights for different matching heuristics
# These are multiplied with raw match scores to get weighted scores
DEFAULT_URL_MATCH_WEIGHT: Final[float] = 1.0       # URL matches are highest confidence
DEFAULT_HANDLE_MATCH_WEIGHT: Final[float] = 0.7    # Handle matches are medium confidence
DEFAULT_TEXT_SIMILARITY_WEIGHT: Final[float] = 0.4  # Text similarity is lower confidence


@dataclass(frozen=True)
class MatchWeights:
    """Product-Ad matching weights.

    Weights applied to different matching heuristics. Higher weights
    indicate higher confidence in that matching method.

    Attributes:
        url: Weight for URL-based matches (highest confidence).
        handle: Weight for handle-based matches (medium confidence).
        text_similarity: Weight for text similarity matches (lower confidence).
    """

    url: float = DEFAULT_URL_MATCH_WEIGHT
    handle: float = DEFAULT_HANDLE_MATCH_WEIGHT
    text_similarity: float = DEFAULT_TEXT_SIMILARITY_WEIGHT

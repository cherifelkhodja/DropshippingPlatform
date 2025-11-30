"""Domain Configuration Module.

Centralizes business rules and thresholds for the Market Intelligence platform.
"""

from .market_intel_config import (
    # Alert thresholds
    SCORE_CHANGE_THRESHOLD,
    ADS_BOOST_RATIO_THRESHOLD,
    # Match thresholds
    STRONG_MATCH_THRESHOLD,
    MEDIUM_MATCH_THRESHOLD,
    WEAK_MATCH_THRESHOLD,
    TEXT_SIMILARITY_THRESHOLD,
    # Match weights
    DEFAULT_URL_MATCH_WEIGHT,
    DEFAULT_HANDLE_MATCH_WEIGHT,
    DEFAULT_TEXT_SIMILARITY_WEIGHT,
    # Config classes
    AlertThresholds,
    MatchThresholds,
    MatchWeights,
)

__all__ = [
    # Alert thresholds
    "SCORE_CHANGE_THRESHOLD",
    "ADS_BOOST_RATIO_THRESHOLD",
    # Match thresholds
    "STRONG_MATCH_THRESHOLD",
    "MEDIUM_MATCH_THRESHOLD",
    "WEAK_MATCH_THRESHOLD",
    "TEXT_SIMILARITY_THRESHOLD",
    # Match weights
    "DEFAULT_URL_MATCH_WEIGHT",
    "DEFAULT_HANDLE_MATCH_WEIGHT",
    "DEFAULT_TEXT_SIMILARITY_WEIGHT",
    # Config classes
    "AlertThresholds",
    "MatchThresholds",
    "MatchWeights",
]

"""Domain services.

This module contains domain services that encapsulate business logic
that doesn't naturally fit within entities.
"""

from .product_ad_matcher import (
    MatchConfig,
    normalize_text,
    extract_handle_from_url,
    calculate_text_similarity,
    check_url_match,
    check_handle_match,
    check_text_similarity,
    match_product_to_ad,
    match_product_to_ads,
)

# Re-export thresholds from centralized config for backward compatibility
from ..config import (
    STRONG_MATCH_THRESHOLD,
    MEDIUM_MATCH_THRESHOLD,
    WEAK_MATCH_THRESHOLD,
    TEXT_SIMILARITY_THRESHOLD,
)

__all__ = [
    "MatchConfig",
    "normalize_text",
    "extract_handle_from_url",
    "calculate_text_similarity",
    "check_url_match",
    "check_handle_match",
    "check_text_similarity",
    "match_product_to_ad",
    "match_product_to_ads",
    "STRONG_MATCH_THRESHOLD",
    "MEDIUM_MATCH_THRESHOLD",
    "WEAK_MATCH_THRESHOLD",
    "TEXT_SIMILARITY_THRESHOLD",
]

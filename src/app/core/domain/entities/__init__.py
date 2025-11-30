"""Domain Entities for the Dropshipping Platform.

Entities are objects with a distinct identity that persists over time.
They are the core business objects of the domain.
"""

from .page import Page
from .ad import Ad, AdStatus, AdPlatform
from .shopify_profile import ShopifyProfile, ShopifyTheme, ShopifyApp
from .scan import Scan, ScanType, ScanStatus, ScanResult
from .keyword_run import KeywordRun, KeywordRunStatus, KeywordRunResult
from .shop_score import ShopScore
from .ranked_shop import RankedShop, RankedShopsResult
from .watchlist import Watchlist, WatchlistItem
from .alert import (
    Alert,
    ALERT_TYPE_NEW_ADS_BOOST,
    ALERT_TYPE_SCORE_JUMP,
    ALERT_TYPE_SCORE_DROP,
    ALERT_TYPE_TIER_UP,
    ALERT_TYPE_TIER_DOWN,
    VALID_ALERT_TYPES,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
    VALID_SEVERITIES,
)
from .product import Product
from .product_insights import (
    ProductInsights,
    PageProductInsights,
    AdMatch,
    MatchStrength,
)

__all__ = [
    # Page
    "Page",
    # Ad
    "Ad",
    "AdStatus",
    "AdPlatform",
    # Shopify Profile
    "ShopifyProfile",
    "ShopifyTheme",
    "ShopifyApp",
    # Scan
    "Scan",
    "ScanType",
    "ScanStatus",
    "ScanResult",
    # Keyword Run
    "KeywordRun",
    "KeywordRunStatus",
    "KeywordRunResult",
    # Shop Score
    "ShopScore",
    # Ranked Shop (read-model)
    "RankedShop",
    "RankedShopsResult",
    # Watchlist
    "Watchlist",
    "WatchlistItem",
    # Alert
    "Alert",
    "ALERT_TYPE_NEW_ADS_BOOST",
    "ALERT_TYPE_SCORE_JUMP",
    "ALERT_TYPE_SCORE_DROP",
    "ALERT_TYPE_TIER_UP",
    "ALERT_TYPE_TIER_DOWN",
    "VALID_ALERT_TYPES",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "SEVERITY_CRITICAL",
    "VALID_SEVERITIES",
    # Product
    "Product",
    # Product Insights (read-model)
    "ProductInsights",
    "PageProductInsights",
    "AdMatch",
    "MatchStrength",
]

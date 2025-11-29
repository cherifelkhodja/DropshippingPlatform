"""Domain Entities for the Dropshipping Platform.

Entities are objects with a distinct identity that persists over time.
They are the core business objects of the domain.
"""

from .page import Page
from .ad import Ad, AdStatus, AdPlatform
from .shopify_profile import ShopifyProfile, ShopifyTheme, ShopifyApp
from .scan import Scan, ScanType, ScanStatus, ScanResult
from .keyword_run import KeywordRun, KeywordRunStatus, KeywordRunResult

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
]

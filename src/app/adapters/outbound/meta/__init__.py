"""Meta Ads Adapter Package.

Provides Meta Ads Library API client implementation.
"""

from src.app.adapters.outbound.meta.config import MetaAdsConfig
from src.app.adapters.outbound.meta.meta_ads_client import MetaAdsClient

__all__ = [
    "MetaAdsClient",
    "MetaAdsConfig",
]

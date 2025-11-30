"""Use Cases for the Dropshipping Platform.

Use cases represent application-level business logic.
They orchestrate domain objects and ports to accomplish specific tasks.

All use cases:
- Depend only on ports and domain objects
- Are async
- Are 100% typed
- Contain no direct I/O
- Raise only domain errors
"""

from .search_ads_by_keyword import (
    SearchAdsByKeywordUseCase,
    SearchAdsResult,
)
from .compute_page_active_ads_count import (
    ComputePageActiveAdsCountUseCase,
    PageAdsCountResult,
    PageAdsTier,
)
from .analyse_page_deep import (
    AnalysePageDeepUseCase,
    AnalysePageDeepResult,
)
from .analyse_website import (
    AnalyseWebsiteUseCase,
    AnalyseWebsiteResult,
)
from .extract_product_count import (
    ExtractProductCountUseCase,
    ExtractProductCountResult,
)
from .compute_shop_score import (
    ComputeShopScoreUseCase,
    ComputeShopScoreResult,
)
from .get_ranked_shops import GetRankedShopsUseCase
from .watchlists import (
    CreateWatchlistUseCase,
    GetWatchlistUseCase,
    ListWatchlistsUseCase,
    AddPageToWatchlistUseCase,
    RemovePageFromWatchlistUseCase,
    ListWatchlistItemsUseCase,
    RescoreWatchlistUseCase,
)
from .detect_alerts_for_page import (
    DetectAlertsForPageUseCase,
    DetectAlertsInput,
)
from .sync_products_for_page import (
    SyncProductsForPageUseCase,
    SyncProductsResult,
)
from .build_product_insights import (
    BuildProductInsightsForPageUseCase,
    BuildProductInsightsResult,
)
from .creative_insights import (
    AnalyzeAdCreativeUseCase,
    AnalyzeAdCreativeResult,
    BuildPageCreativeInsightsUseCase,
    BuildPageCreativeInsightsResult,
)

__all__ = [
    # Search Ads
    "SearchAdsByKeywordUseCase",
    "SearchAdsResult",
    # Compute Page Active Ads
    "ComputePageActiveAdsCountUseCase",
    "PageAdsCountResult",
    "PageAdsTier",
    # Analyse Page Deep
    "AnalysePageDeepUseCase",
    "AnalysePageDeepResult",
    # Analyse Website
    "AnalyseWebsiteUseCase",
    "AnalyseWebsiteResult",
    # Extract Product Count
    "ExtractProductCountUseCase",
    "ExtractProductCountResult",
    # Compute Shop Score
    "ComputeShopScoreUseCase",
    "ComputeShopScoreResult",
    # Get Ranked Shops
    "GetRankedShopsUseCase",
    # Watchlists
    "CreateWatchlistUseCase",
    "GetWatchlistUseCase",
    "ListWatchlistsUseCase",
    "AddPageToWatchlistUseCase",
    "RemovePageFromWatchlistUseCase",
    "ListWatchlistItemsUseCase",
    "RescoreWatchlistUseCase",
    # Alerts
    "DetectAlertsForPageUseCase",
    "DetectAlertsInput",
    # Sync Products
    "SyncProductsForPageUseCase",
    "SyncProductsResult",
    # Build Product Insights
    "BuildProductInsightsForPageUseCase",
    "BuildProductInsightsResult",
    # Creative Insights (IA Marketing)
    "AnalyzeAdCreativeUseCase",
    "AnalyzeAdCreativeResult",
    "BuildPageCreativeInsightsUseCase",
    "BuildPageCreativeInsightsResult",
]

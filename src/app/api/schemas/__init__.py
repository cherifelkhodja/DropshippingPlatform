"""Pydantic schemas for API requests and responses."""

from .keywords import (
    KeywordSearchRequest,
    KeywordSearchResponse,
)
from .pages import (
    PageResponse,
    PageListResponse,
    PageFilters,
)
from .scans import (
    ScanResponse,
    ScanResultResponse,
)
from .scoring import (
    ShopScoreResponse,
    ScoreComponentsResponse,
    TopShopsFilters,
    TopShopEntry,
    TopShopsResponse,
    RecomputeScoreResponse,
)
from .common import (
    HealthResponse,
    ErrorResponse,
    PaginatedResponse,
)
from .watchlists import (
    WatchlistCreateRequest,
    WatchlistResponse,
    WatchlistListResponse,
    WatchlistItemRequest,
    WatchlistItemResponse,
    WatchlistItemListResponse,
    watchlist_to_response,
    watchlist_item_to_response,
)
from .alerts import (
    AlertResponse,
    AlertListResponse,
    alert_to_response,
)
from .metrics import (
    PageDailyMetricsResponse,
    PageMetricsHistoryResponse,
    TriggerDailySnapshotResponse,
    TriggerDailySnapshotRequest,
)

__all__ = [
    "KeywordSearchRequest",
    "KeywordSearchResponse",
    "PageResponse",
    "PageListResponse",
    "PageFilters",
    "ScanResponse",
    "ScanResultResponse",
    "ShopScoreResponse",
    "ScoreComponentsResponse",
    "TopShopsFilters",
    "TopShopEntry",
    "TopShopsResponse",
    "RecomputeScoreResponse",
    "HealthResponse",
    "ErrorResponse",
    "PaginatedResponse",
    # Watchlists
    "WatchlistCreateRequest",
    "WatchlistResponse",
    "WatchlistListResponse",
    "WatchlistItemRequest",
    "WatchlistItemResponse",
    "WatchlistItemListResponse",
    "watchlist_to_response",
    "watchlist_item_to_response",
    # Alerts
    "AlertResponse",
    "AlertListResponse",
    "alert_to_response",
    # Metrics
    "PageDailyMetricsResponse",
    "PageMetricsHistoryResponse",
    "TriggerDailySnapshotResponse",
    "TriggerDailySnapshotRequest",
]

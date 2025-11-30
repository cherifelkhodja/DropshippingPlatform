"""Watchlist API schemas.

Pydantic models for watchlist-related requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.app.core.domain.entities.watchlist import Watchlist, WatchlistItem


class WatchlistCreateRequest(BaseModel):
    """Request body for creating a watchlist."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="Human-readable name for the watchlist",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional description of the watchlist purpose",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Top FR Winners",
                    "description": "French stores with high scores to monitor",
                }
            ]
        }
    }


class WatchlistResponse(BaseModel):
    """Response for a single watchlist."""

    id: str = Field(description="Unique watchlist identifier")
    name: str = Field(description="Watchlist name")
    description: str | None = Field(description="Watchlist description")
    created_at: datetime = Field(description="When the watchlist was created")
    is_active: bool = Field(description="Whether the watchlist is active")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Top FR Winners",
                    "description": "French stores with high scores to monitor",
                    "created_at": "2024-03-20T15:45:00Z",
                    "is_active": True,
                }
            ]
        }
    }


class WatchlistListResponse(BaseModel):
    """Response for listing watchlists."""

    items: list[WatchlistResponse] = Field(description="List of watchlists")
    count: int = Field(description="Number of watchlists returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "Top FR Winners",
                            "description": "French stores with high scores",
                            "created_at": "2024-03-20T15:45:00Z",
                            "is_active": True,
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    }


class WatchlistItemRequest(BaseModel):
    """Request body for adding a page to a watchlist."""

    page_id: str = Field(description="Page identifier to add to the watchlist")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "550e8400-e29b-41d4-a716-446655440001",
                }
            ]
        }
    }


class WatchlistItemResponse(BaseModel):
    """Response for a single watchlist item."""

    id: str = Field(description="Unique watchlist item identifier")
    watchlist_id: str = Field(description="Parent watchlist identifier")
    page_id: str = Field(description="Page identifier")
    created_at: datetime = Field(description="When the item was added")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "watchlist_id": "550e8400-e29b-41d4-a716-446655440000",
                    "page_id": "550e8400-e29b-41d4-a716-446655440001",
                    "created_at": "2024-03-20T16:00:00Z",
                }
            ]
        }
    }


class WatchlistItemListResponse(BaseModel):
    """Response for listing watchlist items."""

    items: list[WatchlistItemResponse] = Field(description="List of watchlist items")
    count: int = Field(description="Number of items returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440002",
                            "watchlist_id": "550e8400-e29b-41d4-a716-446655440000",
                            "page_id": "550e8400-e29b-41d4-a716-446655440001",
                            "created_at": "2024-03-20T16:00:00Z",
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    }


class RescoreWatchlistResponse(BaseModel):
    """Response for rescoring a watchlist."""

    watchlist_id: str = Field(description="The watchlist that was rescored")
    tasks_dispatched: int = Field(
        description="Number of compute_shop_score tasks dispatched"
    )
    message: str = Field(description="Status message")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "watchlist_id": "550e8400-e29b-41d4-a716-446655440000",
                    "tasks_dispatched": 25,
                    "message": "Dispatched 25 scoring tasks for watchlist",
                }
            ]
        }
    }


# =============================================================================
# Converter Functions
# =============================================================================


def watchlist_to_response(watchlist: Watchlist) -> WatchlistResponse:
    """Convert domain Watchlist to API response.

    Args:
        watchlist: The domain Watchlist entity.

    Returns:
        API response model for the watchlist.
    """
    return WatchlistResponse(
        id=watchlist.id,
        name=watchlist.name,
        description=watchlist.description,
        created_at=watchlist.created_at,
        is_active=watchlist.is_active,
    )


def watchlist_item_to_response(item: WatchlistItem) -> WatchlistItemResponse:
    """Convert domain WatchlistItem to API response.

    Args:
        item: The domain WatchlistItem entity.

    Returns:
        API response model for the watchlist item.
    """
    return WatchlistItemResponse(
        id=item.id,
        watchlist_id=item.watchlist_id,
        page_id=item.page_id,
        created_at=item.created_at,
    )


# =============================================================================
# Extended Schemas for UI (Sprint 8.1)
# =============================================================================


class WatchlistPageInfoResponse(BaseModel):
    """Response for a page within a watchlist with details."""

    page_id: str = Field(description="Page identifier")
    page_name: str = Field(description="Page name/domain")
    url: str = Field(description="Page URL")
    country: str | None = Field(description="Country code")
    is_shopify: bool = Field(description="Whether the page is a Shopify store")
    shop_score: float = Field(description="Current shop score (0-100)")
    tier: str = Field(description="Current tier (XXL, XL, L, M, S, XS)")
    active_ads_count: int = Field(description="Number of active ads")
    added_at: datetime = Field(description="When the page was added to watchlist")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "550e8400-e29b-41d4-a716-446655440001",
                    "page_name": "example-store.com",
                    "url": "https://example-store.com",
                    "country": "FR",
                    "is_shopify": True,
                    "shop_score": 78.5,
                    "tier": "XL",
                    "active_ads_count": 15,
                    "added_at": "2024-03-20T16:00:00Z",
                }
            ]
        }
    }


class WatchlistWithDetailsResponse(BaseModel):
    """Response for a watchlist with full page details."""

    id: str = Field(description="Unique watchlist identifier")
    name: str = Field(description="Watchlist name")
    description: str | None = Field(description="Watchlist description")
    created_at: datetime = Field(description="When the watchlist was created")
    is_active: bool = Field(description="Whether the watchlist is active")
    pages_count: int = Field(description="Number of pages in the watchlist")
    pages: list[WatchlistPageInfoResponse] = Field(
        description="List of pages with details"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Top FR Winners",
                    "description": "French stores with high scores",
                    "created_at": "2024-03-20T15:45:00Z",
                    "is_active": True,
                    "pages_count": 1,
                    "pages": [
                        {
                            "page_id": "550e8400-e29b-41d4-a716-446655440001",
                            "page_name": "example-store.com",
                            "url": "https://example-store.com",
                            "country": "FR",
                            "is_shopify": True,
                            "shop_score": 78.5,
                            "tier": "XL",
                            "active_ads_count": 15,
                            "added_at": "2024-03-20T16:00:00Z",
                        }
                    ],
                }
            ]
        }
    }


class WatchlistSummaryResponse(BaseModel):
    """Response for a watchlist in list view with counts."""

    id: str = Field(description="Unique watchlist identifier")
    name: str = Field(description="Watchlist name")
    description: str | None = Field(description="Watchlist description")
    created_at: datetime = Field(description="When the watchlist was created")
    is_active: bool = Field(description="Whether the watchlist is active")
    pages_count: int = Field(description="Number of pages in the watchlist")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Top FR Winners",
                    "description": "French stores with high scores",
                    "created_at": "2024-03-20T15:45:00Z",
                    "is_active": True,
                    "pages_count": 42,
                }
            ]
        }
    }


class WatchlistSummaryListResponse(BaseModel):
    """Response for listing watchlists with counts."""

    items: list[WatchlistSummaryResponse] = Field(
        description="List of watchlist summaries"
    )
    count: int = Field(description="Number of watchlists returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "Top FR Winners",
                            "description": "French stores with high scores",
                            "created_at": "2024-03-20T15:45:00Z",
                            "is_active": True,
                            "pages_count": 42,
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    }


class PageWatchlistsResponse(BaseModel):
    """Response for listing watchlists that contain a page."""

    page_id: str = Field(description="The page identifier")
    watchlists: list[WatchlistResponse] = Field(
        description="Watchlists containing this page"
    )
    count: int = Field(description="Number of watchlists")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "550e8400-e29b-41d4-a716-446655440001",
                    "watchlists": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "Top FR Winners",
                            "description": "French stores with high scores",
                            "created_at": "2024-03-20T15:45:00Z",
                            "is_active": True,
                        }
                    ],
                    "count": 1,
                }
            ]
        }
    }

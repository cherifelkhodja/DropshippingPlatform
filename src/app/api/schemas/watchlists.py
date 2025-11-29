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

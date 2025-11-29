"""Admin monitoring API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Pages Admin Schemas
# =============================================================================


class AdminPageFilters(BaseModel):
    """Query filters for admin page listing."""

    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Filter by country code",
    )
    is_shopify: bool | None = Field(
        default=None,
        description="Filter by Shopify status",
    )
    min_ads: int | None = Field(
        default=None,
        ge=0,
        description="Minimum number of active ads",
    )
    max_ads: int | None = Field(
        default=None,
        ge=0,
        description="Maximum number of active ads",
    )
    state: str | None = Field(
        default=None,
        description="Filter by page state (new, active, stale, etc.)",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum items to return")


class AdminPageResponse(BaseModel):
    """Admin page summary response."""

    page_id: str = Field(description="Page identifier")
    page_name: str = Field(description="Page name/domain")
    country: str | None = Field(default=None, description="Country code")
    is_shopify: bool = Field(description="Whether the page is a Shopify store")
    ads_count: int = Field(description="Number of active ads")
    product_count: int = Field(description="Number of products")
    state: str = Field(description="Current page state")
    last_scan_at: datetime | None = Field(
        default=None, description="Last scan timestamp"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "550e8400-e29b-41d4-a716-446655440000",
                    "page_name": "example-store.com",
                    "country": "US",
                    "is_shopify": True,
                    "ads_count": 15,
                    "product_count": 250,
                    "state": "active",
                    "last_scan_at": "2024-03-20T15:45:00Z",
                }
            ]
        }
    }


class AdminPageListResponse(BaseModel):
    """Paginated admin page list response."""

    items: list[AdminPageResponse] = Field(description="List of pages")
    total: int = Field(description="Total number of matching pages")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Items per page")


# =============================================================================
# Keywords Admin Schemas
# =============================================================================


class AdminKeywordRunResponse(BaseModel):
    """Admin keyword run summary response."""

    keyword: str = Field(description="Searched keyword")
    country: str = Field(description="Country code")
    created_at: datetime = Field(description="Run creation timestamp")
    total_ads_found: int = Field(description="Total ads found in this run")
    total_pages_found: int = Field(description="Total unique pages found")
    scan_id: str = Field(description="Associated scan identifier")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "keyword": "dropshipping supplies",
                    "country": "US",
                    "created_at": "2024-03-20T10:30:00Z",
                    "total_ads_found": 150,
                    "total_pages_found": 45,
                    "scan_id": "550e8400-e29b-41d4-a716-446655440000",
                }
            ]
        }
    }


class AdminKeywordListResponse(BaseModel):
    """Admin keyword runs list response."""

    items: list[AdminKeywordRunResponse] = Field(description="List of keyword runs")
    total: int = Field(description="Total number of runs returned")


# =============================================================================
# Scans Admin Schemas
# =============================================================================


class AdminScanFilters(BaseModel):
    """Query filters for admin scan listing."""

    status: str | None = Field(
        default=None,
        description="Filter by scan status (pending, running, completed, failed)",
    )
    since: datetime | None = Field(
        default=None,
        description="Filter scans created after this datetime",
    )
    page_id: str | None = Field(
        default=None,
        description="Filter by associated page ID",
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum items to return")


class AdminScanResponse(BaseModel):
    """Admin scan summary response."""

    id: str = Field(description="Scan identifier")
    status: str = Field(description="Scan status")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    completed_at: datetime | None = Field(
        default=None, description="Completion timestamp"
    )
    page_id: str | None = Field(default=None, description="Associated page ID")
    result_summary: str | None = Field(default=None, description="Brief result summary")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "completed",
                    "started_at": "2024-03-20T10:30:00Z",
                    "completed_at": "2024-03-20T10:32:15Z",
                    "page_id": "page-12345",
                    "result_summary": "Found 25 ads, 150 products",
                }
            ]
        }
    }


class AdminScanListResponse(BaseModel):
    """Paginated admin scan list response."""

    items: list[AdminScanResponse] = Field(description="List of scans")
    total: int = Field(description="Total number of matching scans")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Items per page")

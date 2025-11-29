"""Page API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class PageFilters(BaseModel):
    """Query filters for page listing."""

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
    min_active_ads: int | None = Field(
        default=None,
        ge=0,
        description="Minimum number of active ads",
    )
    max_active_ads: int | None = Field(
        default=None,
        ge=0,
        description="Maximum number of active ads",
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")


class PageResponse(BaseModel):
    """Single page response."""

    id: str = Field(description="Page identifier")
    url: str = Field(description="Page URL")
    domain: str = Field(description="Page domain")
    country: str | None = Field(default=None, description="Country code")
    language: str | None = Field(default=None, description="Language code")
    currency: str | None = Field(default=None, description="Currency code")
    category: str | None = Field(default=None, description="Product category")
    is_shopify: bool = Field(description="Whether the page is a Shopify store")
    product_count: int = Field(description="Number of products")
    active_ads_count: int = Field(description="Number of active ads")
    total_ads_count: int = Field(description="Total ads detected")
    status: str = Field(description="Current page status")
    score: float = Field(description="Page score")
    first_seen_at: datetime | None = Field(default=None, description="First seen date")
    last_scanned_at: datetime | None = Field(default=None, description="Last scan date")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "page-12345",
                    "url": "https://example-store.com",
                    "domain": "example-store.com",
                    "country": "US",
                    "language": "en",
                    "currency": "USD",
                    "category": "fashion",
                    "is_shopify": True,
                    "product_count": 150,
                    "active_ads_count": 5,
                    "total_ads_count": 25,
                    "status": "active",
                    "score": 85.5,
                    "first_seen_at": "2024-01-15T10:30:00Z",
                    "last_scanned_at": "2024-03-20T15:45:00Z",
                }
            ]
        }
    }


class PageListResponse(BaseModel):
    """Paginated page list response."""

    items: list[PageResponse] = Field(description="List of pages")
    total: int = Field(description="Total number of matching pages")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    has_more: bool = Field(description="Whether there are more pages")

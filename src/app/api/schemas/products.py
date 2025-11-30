"""Product API schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MatchStrengthEnum(str, Enum):
    """Match strength levels for API responses."""

    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    NONE = "none"


class ProductResponse(BaseModel):
    """Single product response."""

    id: str = Field(description="Product identifier")
    page_id: str = Field(description="Parent page identifier")
    handle: str = Field(description="Product handle (URL slug)")
    title: str = Field(description="Product title")
    url: str = Field(description="Product page URL")
    price_min: float | None = Field(default=None, description="Minimum price")
    price_max: float | None = Field(default=None, description="Maximum price")
    currency: str | None = Field(default=None, description="Currency code")
    available: bool = Field(description="Whether product is available")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    vendor: str | None = Field(default=None, description="Product vendor/brand")
    image_url: str | None = Field(default=None, description="Main product image URL")
    product_type: str | None = Field(default=None, description="Product type")
    created_at: datetime = Field(description="When product was first synced")
    updated_at: datetime = Field(description="When product was last updated")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "prod-12345",
                    "page_id": "page-12345",
                    "handle": "awesome-t-shirt",
                    "title": "Awesome T-Shirt",
                    "url": "https://example-store.com/products/awesome-t-shirt",
                    "price_min": 29.99,
                    "price_max": 34.99,
                    "currency": "USD",
                    "available": True,
                    "tags": ["clothing", "t-shirt", "summer"],
                    "vendor": "Example Brand",
                    "image_url": "https://cdn.shopify.com/...",
                    "product_type": "T-Shirts",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-03-20T15:45:00Z",
                }
            ]
        }
    }


class ProductListResponse(BaseModel):
    """Paginated product list response."""

    items: list[ProductResponse] = Field(description="List of products")
    total: int = Field(description="Total number of products for the page")
    page_id: str = Field(description="Parent page identifier")
    limit: int = Field(description="Maximum items returned")
    offset: int = Field(description="Offset for pagination")


class SyncProductsResponse(BaseModel):
    """Response from product sync operation."""

    page_id: str = Field(description="Page identifier")
    products_synced: int = Field(description="Number of products synced")
    products_extracted: int = Field(description="Number of products extracted from source")
    is_shopify: bool = Field(description="Whether the page is a Shopify store")
    source: str | None = Field(default=None, description="Source of product data")
    error: str | None = Field(default=None, description="Error message if any")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "page-12345",
                    "products_synced": 150,
                    "products_extracted": 150,
                    "is_shopify": True,
                    "source": "products.json",
                    "error": None,
                }
            ]
        }
    }


# =============================================================================
# Product Insights Schemas
# =============================================================================


class AdMatchResponse(BaseModel):
    """Response for a single ad match."""

    ad_id: str = Field(description="Matched ad identifier")
    score: float = Field(description="Match confidence score (0.0 to 1.0)")
    strength: MatchStrengthEnum = Field(description="Match strength level")
    reasons: list[str] = Field(default_factory=list, description="Reasons for the match")
    ad_title: str | None = Field(default=None, description="Ad title")
    ad_link_url: str | None = Field(default=None, description="Ad destination URL")
    ad_is_active: bool = Field(description="Whether the ad is currently active")


class ProductInsightsData(BaseModel):
    """Insights data for a single product."""

    ads_count: int = Field(description="Number of matched ads")
    distinct_creatives_count: int = Field(description="Number of distinct ad creatives")
    match_score: float = Field(description="Overall match score (0.0 to 1.0)")
    has_strong_match: bool = Field(description="Whether there's a strong match")
    is_promoted: bool = Field(description="Whether the product is actively promoted")
    strong_matches_count: int = Field(default=0, description="Count of strong matches")
    medium_matches_count: int = Field(default=0, description="Count of medium matches")
    weak_matches_count: int = Field(default=0, description="Count of weak matches")
    first_seen_at: datetime | None = Field(
        default=None, description="First ad seen timestamp"
    )
    last_seen_at: datetime | None = Field(
        default=None, description="Last ad seen timestamp"
    )
    match_reasons: list[str] = Field(
        default_factory=list, description="All unique match reasons"
    )
    matched_ads: list[AdMatchResponse] = Field(
        default_factory=list, description="Details of matched ads"
    )


class ProductInsightsEntry(BaseModel):
    """Combined product and insights entry."""

    product: ProductResponse = Field(description="Product details")
    insights: ProductInsightsData = Field(description="Product insights data")


class PageProductInsightsSummary(BaseModel):
    """Summary of product insights for an entire page."""

    page_id: str = Field(description="Page identifier")
    products_count: int = Field(description="Total number of products")
    products_with_ads_count: int = Field(description="Products with at least one ad match")
    promoted_products_count: int = Field(description="Products that are actively promoted")
    total_ads_analyzed: int = Field(description="Total number of ads analyzed")
    coverage_ratio: float = Field(description="Ratio of products with ads (0.0 to 1.0)")
    promotion_ratio: float = Field(description="Ratio of promoted products (0.0 to 1.0)")
    computed_at: datetime = Field(description="When insights were computed")


class PageProductInsightsResponse(BaseModel):
    """Full response for page product insights."""

    summary: PageProductInsightsSummary = Field(description="Page-level summary")
    items: list[ProductInsightsEntry] = Field(description="Product insights list")
    total: int = Field(description="Total items (before pagination)")
    limit: int = Field(description="Maximum items returned")
    offset: int = Field(description="Pagination offset")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": {
                        "page_id": "page-12345",
                        "products_count": 50,
                        "products_with_ads_count": 15,
                        "promoted_products_count": 8,
                        "total_ads_analyzed": 25,
                        "coverage_ratio": 0.30,
                        "promotion_ratio": 0.16,
                        "computed_at": "2024-03-20T15:45:00Z",
                    },
                    "items": [],
                    "total": 50,
                    "limit": 50,
                    "offset": 0,
                }
            ]
        }
    }


class ProductInsightsSortBy(str, Enum):
    """Sort options for product insights."""

    ADS_COUNT = "ads_count"
    MATCH_SCORE = "match_score"
    LAST_SEEN_AT = "last_seen_at"


# =============================================================================
# Mapping Helper Functions
# =============================================================================


def product_to_response(product: "Product") -> ProductResponse:
    """Convert domain Product to API response.

    Args:
        product: Domain Product entity.

    Returns:
        ProductResponse for API.
    """
    return ProductResponse(
        id=product.id,
        page_id=product.page_id,
        handle=product.handle,
        title=product.title,
        url=product.url,
        price_min=product.price_min,
        price_max=product.price_max,
        currency=product.currency,
        available=product.available,
        tags=product.tags,
        vendor=product.vendor,
        image_url=product.image_url,
        product_type=product.product_type,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def ad_match_to_response(ad_match: "AdMatch") -> AdMatchResponse:
    """Convert domain AdMatch to API response.

    Args:
        ad_match: Domain AdMatch entity.

    Returns:
        AdMatchResponse for API.
    """
    return AdMatchResponse(
        ad_id=ad_match.ad.id,
        score=ad_match.score,
        strength=MatchStrengthEnum(ad_match.strength.value),
        reasons=list(ad_match.reasons),
        ad_title=ad_match.ad.title,
        ad_link_url=str(ad_match.ad.link_url) if ad_match.ad.link_url else None,
        ad_is_active=ad_match.ad.is_active(),
    )


def product_insights_to_data(insights: "ProductInsights") -> ProductInsightsData:
    """Convert domain ProductInsights to API data response.

    Args:
        insights: Domain ProductInsights entity.

    Returns:
        ProductInsightsData for API.
    """
    # Extract first/last seen from matched ads
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    for match in insights.matched_ads:
        ad = match.ad
        if ad.first_seen_at:
            if first_seen is None or ad.first_seen_at < first_seen:
                first_seen = ad.first_seen_at
        if ad.last_seen_at:
            if last_seen is None or ad.last_seen_at > last_seen:
                last_seen = ad.last_seen_at

    # Count distinct creatives (unique image/video URLs)
    creative_urls: set[str] = set()
    for match in insights.matched_ads:
        if match.ad.image_url:
            creative_urls.add(str(match.ad.image_url))
        if match.ad.video_url:
            creative_urls.add(str(match.ad.video_url))

    return ProductInsightsData(
        ads_count=len(insights.matched_ads),
        distinct_creatives_count=len(creative_urls) if creative_urls else len(insights.matched_ads),
        match_score=insights.match_score,
        has_strong_match=insights.has_strong_match,
        is_promoted=insights.is_promoted,
        strong_matches_count=insights.strong_matches_count,
        medium_matches_count=insights.medium_matches_count,
        weak_matches_count=insights.weak_matches_count,
        first_seen_at=first_seen,
        last_seen_at=last_seen,
        match_reasons=insights.match_reasons,
        matched_ads=[ad_match_to_response(m) for m in insights.matched_ads],
    )


def product_insights_to_entry(insights: "ProductInsights") -> ProductInsightsEntry:
    """Convert domain ProductInsights to API entry response.

    Args:
        insights: Domain ProductInsights entity.

    Returns:
        ProductInsightsEntry for API.
    """
    return ProductInsightsEntry(
        product=product_to_response(insights.product),
        insights=product_insights_to_data(insights),
    )


def page_product_insights_to_response(
    page_insights: "PageProductInsights",
    sorted_insights: list["ProductInsights"],
    limit: int,
    offset: int,
) -> PageProductInsightsResponse:
    """Convert domain PageProductInsights to API response with pagination.

    Args:
        page_insights: Domain PageProductInsights entity.
        sorted_insights: Pre-sorted and paginated list of ProductInsights.
        limit: Pagination limit.
        offset: Pagination offset.

    Returns:
        PageProductInsightsResponse for API.
    """
    summary = PageProductInsightsSummary(
        page_id=page_insights.page_id,
        products_count=page_insights.total_products,
        products_with_ads_count=page_insights.products_with_ads,
        promoted_products_count=page_insights.promoted_products_count,
        total_ads_analyzed=page_insights.total_ads,
        coverage_ratio=page_insights.coverage_ratio,
        promotion_ratio=page_insights.promotion_ratio,
        computed_at=page_insights.computed_at,
    )

    return PageProductInsightsResponse(
        summary=summary,
        items=[product_insights_to_entry(i) for i in sorted_insights],
        total=page_insights.total_products,
        limit=limit,
        offset=offset,
    )


# Type hints for imports (to avoid circular imports)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app.core.domain.entities.product import Product
    from src.app.core.domain.entities.product_insights import (
        AdMatch,
        ProductInsights,
        PageProductInsights,
    )

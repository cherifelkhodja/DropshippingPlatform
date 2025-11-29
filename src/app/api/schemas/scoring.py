"""Scoring API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScoreComponentsResponse(BaseModel):
    """Individual score components breakdown."""

    ads_activity: float = Field(
        ge=0,
        le=100,
        description="Ads activity score (0-100)",
    )
    shopify: float = Field(
        ge=0,
        le=100,
        description="Shopify store quality score (0-100)",
    )
    creative_quality: float = Field(
        ge=0,
        le=100,
        description="Creative quality score (0-100)",
    )
    catalog: float = Field(
        ge=0,
        le=100,
        description="Catalog richness score (0-100)",
    )


class ShopScoreResponse(BaseModel):
    """Shop score response."""

    page_id: str = Field(description="Page identifier")
    score: float = Field(
        ge=0,
        le=100,
        description="Overall weighted score (0-100)",
    )
    tier: str = Field(description="Score tier (XS, S, M, L, XL, XXL)")
    components: ScoreComponentsResponse = Field(
        description="Individual score components",
    )
    computed_at: datetime = Field(description="When the score was computed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "page-12345",
                    "score": 72.5,
                    "tier": "L",
                    "components": {
                        "ads_activity": 85.0,
                        "shopify": 70.0,
                        "creative_quality": 60.0,
                        "catalog": 55.0,
                    },
                    "computed_at": "2024-03-20T15:45:00Z",
                }
            ]
        }
    }


class TopShopsFilters(BaseModel):
    """Query filters for top shops listing."""

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Number of top shops to return",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination",
    )


class TopShopEntry(BaseModel):
    """Single entry in top shops list."""

    rank: int = Field(ge=1, description="Position in ranking")
    page_id: str = Field(description="Page identifier")
    domain: str = Field(description="Shop domain")
    score: float = Field(ge=0, le=100, description="Overall score")
    tier: str = Field(description="Score tier")
    computed_at: datetime = Field(description="When the score was computed")


class TopShopsResponse(BaseModel):
    """Top shops list response."""

    items: list[TopShopEntry] = Field(description="List of top-ranked shops")
    total: int = Field(description="Total number of scored shops")
    limit: int = Field(description="Requested limit")
    offset: int = Field(description="Requested offset")


class RecomputeScoreResponse(BaseModel):
    """Response for score recomputation request."""

    page_id: str = Field(description="Page identifier")
    task_id: str = Field(description="Celery task ID for tracking")
    status: str = Field(description="Task status (dispatched)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "page-12345",
                    "task_id": "abc123-def456-ghi789",
                    "status": "dispatched",
                }
            ]
        }
    }


# =============================================================================
# Ranking Schemas (Sprint 4.2)
# =============================================================================


class RankedShopEntry(BaseModel):
    """Single entry in ranked shops list."""

    page_id: str = Field(description="Page identifier")
    score: float = Field(ge=0, le=100, description="Overall score")
    tier: str = Field(description="Score tier (XS, S, M, L, XL, XXL)")
    url: str | None = Field(default=None, description="Shop URL")
    country: str | None = Field(default=None, description="Country code (ISO 3166-1 alpha-2)")
    name: str | None = Field(default=None, description="Shop name or domain")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "page-12345",
                    "score": 85.5,
                    "tier": "XXL",
                    "url": "https://example-store.com",
                    "country": "FR",
                    "name": "Example Store",
                }
            ]
        }
    }


class RankedShopsResponse(BaseModel):
    """Ranked shops list response with pagination."""

    items: list[RankedShopEntry] = Field(description="List of ranked shops")
    total: int = Field(description="Total number of shops matching filters")
    limit: int = Field(description="Requested limit")
    offset: int = Field(description="Requested offset")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "page_id": "page-001",
                            "score": 92.0,
                            "tier": "XXL",
                            "url": "https://top-store.com",
                            "country": "US",
                            "name": "Top Store",
                        },
                        {
                            "page_id": "page-002",
                            "score": 78.5,
                            "tier": "XL",
                            "url": "https://great-shop.com",
                            "country": "FR",
                            "name": "Great Shop",
                        },
                    ],
                    "total": 150,
                    "limit": 50,
                    "offset": 0,
                }
            ]
        }
    }


def ranked_result_to_response(
    result: "RankedShopsResult",
) -> RankedShopsResponse:
    """Convert domain RankedShopsResult to API response.

    Args:
        result: The domain result from GetRankedShopsUseCase.

    Returns:
        API response model for ranked shops.
    """
    from src.app.core.domain.entities.ranked_shop import RankedShopsResult

    return RankedShopsResponse(
        items=[
            RankedShopEntry(
                page_id=item.page_id,
                score=item.score,
                tier=item.tier,
                url=item.url,
                country=item.country,
                name=item.name,
            )
            for item in result.items
        ],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )

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

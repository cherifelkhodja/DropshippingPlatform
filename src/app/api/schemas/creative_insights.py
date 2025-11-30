"""Creative Insights API Schemas.

Pydantic models for creative analysis API requests and responses.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CreativeAnalysisResponse(BaseModel):
    """Response model for a single creative analysis."""

    id: str = Field(description="Analysis identifier (UUID)")
    ad_id: str = Field(description="Associated ad identifier (UUID)")
    creative_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Quality score (0-100)",
    )
    style_tags: list[str] = Field(
        default_factory=list,
        description="Creative style tags (e.g., 'minimalist', 'bold')",
    )
    angle_tags: list[str] = Field(
        default_factory=list,
        description="Marketing angle tags (e.g., 'urgency', 'social-proof')",
    )
    tone_tags: list[str] = Field(
        default_factory=list,
        description="Tone tags (e.g., 'casual', 'professional')",
    )
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall sentiment of the creative",
    )
    analysis_version: str = Field(
        description="Version of the analyzer used",
    )
    created_at: datetime = Field(
        description="When this analysis was performed",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "ad_id": "660e8400-e29b-41d4-a716-446655440001",
                    "creative_score": 78.5,
                    "style_tags": ["bold", "conversational"],
                    "angle_tags": ["urgency", "benefit-driven"],
                    "tone_tags": ["casual", "emotional"],
                    "sentiment": "positive",
                    "analysis_version": "v1.0",
                    "created_at": "2024-12-01T12:00:00Z",
                }
            ]
        }
    }


class PageCreativeInsightsResponse(BaseModel):
    """Response model for page-level creative insights."""

    page_id: str = Field(description="Page identifier (UUID)")
    avg_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Average creative score across all ads",
    )
    best_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Highest creative score among ads",
    )
    quality_tier: Literal["excellent", "good", "average", "poor"] = Field(
        description="Overall quality tier based on average score",
    )
    top_creatives: list[CreativeAnalysisResponse] = Field(
        default_factory=list,
        description="Top-scoring creative analyses",
    )
    total_analyzed: int = Field(
        ge=0,
        description="Total number of creatives analyzed",
    )
    computed_at: datetime = Field(
        description="When insights were computed",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "770e8400-e29b-41d4-a716-446655440002",
                    "avg_score": 65.3,
                    "best_score": 85.0,
                    "quality_tier": "good",
                    "top_creatives": [],
                    "total_analyzed": 15,
                    "computed_at": "2024-12-01T12:00:00Z",
                }
            ]
        }
    }


class AnalyzeCreativesRequest(BaseModel):
    """Request to trigger creative analysis for a page (admin endpoint)."""

    pass  # No body required, page_id is in path


class AnalyzeCreativesResponse(BaseModel):
    """Response for triggering creative analysis task."""

    status: Literal["dispatched", "error"] = Field(
        description="Status of the task dispatch",
    )
    message: str = Field(
        description="Human-readable status message",
    )
    task_id: str | None = Field(
        default=None,
        description="Celery task ID if dispatched",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "dispatched",
                    "message": "Creative analysis task dispatched successfully",
                    "task_id": "abc123-def456-ghi789",
                }
            ]
        }
    }

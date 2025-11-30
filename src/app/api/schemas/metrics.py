"""Metrics API Schemas.

Pydantic models for page metrics history endpoints.
Sprint 7: Historisation & Time Series.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class PageDailyMetricsResponse(BaseModel):
    """Response model for a single daily metrics snapshot."""

    date: date = Field(description="Date of the snapshot")
    ads_count: int = Field(description="Number of active ads at snapshot time", ge=0)
    shop_score: float = Field(description="Shop score (0-100) at snapshot time")
    tier: str = Field(description="Tier classification (XXL, XL, L, M, S, XS)")
    products_count: Optional[int] = Field(
        default=None, description="Number of products in catalog (if available)"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class PageMetricsHistoryResponse(BaseModel):
    """Response model for page metrics history.

    Returns a list of daily metrics snapshots ordered by date ASC
    for easy time series visualization in graphs.
    """

    page_id: str = Field(description="Page identifier")
    metrics: list[PageDailyMetricsResponse] = Field(
        default_factory=list, description="List of daily metrics snapshots"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class TriggerDailySnapshotResponse(BaseModel):
    """Response model for admin trigger daily snapshot endpoint."""

    status: str = Field(description="Status of the task dispatch")
    task_id: str = Field(description="Celery task ID for tracking")
    snapshot_date: Optional[str] = Field(
        default=None, description="Date for the snapshot (YYYY-MM-DD)"
    )

    class Config:
        """Pydantic config."""

        from_attributes = True


class TriggerDailySnapshotRequest(BaseModel):
    """Request model for admin trigger daily snapshot endpoint."""

    snapshot_date: Optional[str] = Field(
        default=None,
        description="Date for the snapshot (YYYY-MM-DD). Defaults to today.",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )

    class Config:
        """Pydantic config."""

        from_attributes = True

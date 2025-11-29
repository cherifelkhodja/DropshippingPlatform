"""Alert endpoints.

REST API endpoints for retrieving alerts.
"""

from fastapi import APIRouter, Query

from src.app.api.schemas.common import ErrorResponse
from src.app.api.schemas.alerts import (
    AlertListResponse,
    alert_to_response,
)
from src.app.api.dependencies import AlertRepo

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "/{page_id}",
    response_model=AlertListResponse,
    summary="List alerts for a page",
    description="Get all alerts for a specific page, ordered by creation date (newest first).",
    responses={
        200: {"description": "Alerts retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_alerts_for_page(
    page_id: str,
    alert_repo: AlertRepo,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of alerts to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of alerts to skip",
    ),
) -> AlertListResponse:
    """List all alerts for a specific page.

    Returns alerts ordered by creation date (newest first).
    Useful for monitoring significant changes detected during rescoring.
    """
    alerts = await alert_repo.list_by_page(
        page_id=page_id,
        limit=limit,
        offset=offset,
    )
    return AlertListResponse(
        items=[alert_to_response(a) for a in alerts],
        count=len(alerts),
    )


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List recent alerts",
    description="Get recent alerts across all pages, ordered by creation date (newest first).",
    responses={
        200: {"description": "Alerts retrieved successfully"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_recent_alerts(
    alert_repo: AlertRepo,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of alerts to return",
    ),
) -> AlertListResponse:
    """List recent alerts across all pages.

    Returns the most recent alerts ordered by creation date (newest first).
    Useful for a dashboard view of recent activity.
    """
    alerts = await alert_repo.list_recent(limit=limit)
    return AlertListResponse(
        items=[alert_to_response(a) for a in alerts],
        count=len(alerts),
    )

"""Alert API schemas.

Pydantic models for alert-related requests and responses.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from src.app.core.domain.entities.alert import Alert


class AlertResponse(BaseModel):
    """Response for a single alert."""

    id: str = Field(description="Unique alert identifier")
    page_id: str = Field(description="Page identifier this alert belongs to")
    type: str = Field(description="Alert type (NEW_ADS_BOOST, SCORE_JUMP, etc.)")
    message: str = Field(description="Human-readable alert message")
    severity: str = Field(description="Alert severity (info, warning, critical)")
    old_score: float | None = Field(
        default=None,
        description="Previous score value (for score change alerts)",
    )
    new_score: float | None = Field(
        default=None,
        description="New score value (for score change alerts)",
    )
    old_tier: str | None = Field(
        default=None,
        description="Previous tier (for tier change alerts)",
    )
    new_tier: str | None = Field(
        default=None,
        description="New tier (for tier change alerts)",
    )
    created_at: datetime = Field(description="When this alert was created")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "page_id": "550e8400-e29b-41d4-a716-446655440001",
                    "type": "SCORE_JUMP",
                    "message": "Score jumped from 45.0 to 72.0 (+27.0)",
                    "severity": "warning",
                    "old_score": 45.0,
                    "new_score": 72.0,
                    "old_tier": None,
                    "new_tier": None,
                    "created_at": "2024-03-20T15:45:00Z",
                }
            ]
        }
    }


class AlertListResponse(BaseModel):
    """Response for listing alerts."""

    items: list[AlertResponse] = Field(description="List of alerts")
    count: int = Field(description="Number of alerts returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "page_id": "550e8400-e29b-41d4-a716-446655440001",
                            "type": "SCORE_JUMP",
                            "message": "Score jumped from 45.0 to 72.0 (+27.0)",
                            "severity": "warning",
                            "old_score": 45.0,
                            "new_score": 72.0,
                            "old_tier": None,
                            "new_tier": None,
                            "created_at": "2024-03-20T15:45:00Z",
                        },
                        {
                            "id": "550e8400-e29b-41d4-a716-446655440002",
                            "page_id": "550e8400-e29b-41d4-a716-446655440001",
                            "type": "TIER_UP",
                            "message": "Tier upgraded from M to L",
                            "severity": "info",
                            "old_score": None,
                            "new_score": None,
                            "old_tier": "M",
                            "new_tier": "L",
                            "created_at": "2024-03-20T15:44:00Z",
                        },
                    ],
                    "count": 2,
                }
            ]
        }
    }


# =============================================================================
# Converter Functions
# =============================================================================


def alert_to_response(alert: Alert) -> AlertResponse:
    """Convert domain Alert to API response.

    Args:
        alert: The domain Alert entity.

    Returns:
        API response model for the alert.
    """
    return AlertResponse(
        id=alert.id,
        page_id=alert.page_id,
        type=alert.type,
        message=alert.message,
        severity=alert.severity,
        old_score=alert.old_score,
        new_score=alert.new_score,
        old_tier=alert.old_tier,
        new_tier=alert.new_tier,
        created_at=alert.created_at,
    )

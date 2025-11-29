"""Scan API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScanResultResponse(BaseModel):
    """Scan result details."""

    ads_found: int = Field(default=0, description="Number of ads found")
    new_ads: int = Field(default=0, description="Number of new ads")
    products_found: int = Field(default=0, description="Number of products found")
    is_shopify: bool | None = Field(
        default=None, description="Shopify detection result"
    )
    errors: list[str] = Field(default_factory=list, description="Error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")


class ScanResponse(BaseModel):
    """Single scan response."""

    id: str = Field(description="Scan identifier (UUID)")
    page_id: str = Field(description="Associated page identifier")
    scan_type: str = Field(description="Type of scan performed")
    status: str = Field(description="Current scan status")
    result: ScanResultResponse | None = Field(
        default=None,
        description="Scan results (if completed)",
    )
    priority: int = Field(default=0, description="Scan priority")
    retry_count: int = Field(default=0, description="Number of retries")
    error_message: str | None = Field(
        default=None,
        description="Error message (if failed)",
    )
    started_at: datetime | None = Field(default=None, description="Start time")
    completed_at: datetime | None = Field(default=None, description="Completion time")
    duration_seconds: float | None = Field(
        default=None,
        description="Duration in seconds",
    )
    created_at: datetime = Field(description="Creation timestamp")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "page_id": "page-12345",
                    "scan_type": "full",
                    "status": "completed",
                    "result": {
                        "ads_found": 10,
                        "new_ads": 3,
                        "products_found": 150,
                        "is_shopify": True,
                        "errors": [],
                        "warnings": [],
                    },
                    "priority": 0,
                    "retry_count": 0,
                    "error_message": None,
                    "started_at": "2024-03-20T15:40:00Z",
                    "completed_at": "2024-03-20T15:45:00Z",
                    "duration_seconds": 300.5,
                    "created_at": "2024-03-20T15:39:00Z",
                }
            ]
        }
    }

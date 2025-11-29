"""Common API schemas."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Service status", examples=["ok"])
    version: str = Field(description="Application version", examples=["0.1.0"])
    environment: str = Field(description="Environment name", examples=["development"])


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error type/code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    items: list[Any] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Items per page")
    has_more: bool = Field(description="Whether there are more items")

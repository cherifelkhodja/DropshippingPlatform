"""Pydantic schemas for API requests and responses."""

from .keywords import (
    KeywordSearchRequest,
    KeywordSearchResponse,
)
from .pages import (
    PageResponse,
    PageListResponse,
    PageFilters,
)
from .scans import (
    ScanResponse,
    ScanResultResponse,
)
from .common import (
    HealthResponse,
    ErrorResponse,
    PaginatedResponse,
)

__all__ = [
    "KeywordSearchRequest",
    "KeywordSearchResponse",
    "PageResponse",
    "PageListResponse",
    "PageFilters",
    "ScanResponse",
    "ScanResultResponse",
    "HealthResponse",
    "ErrorResponse",
    "PaginatedResponse",
]

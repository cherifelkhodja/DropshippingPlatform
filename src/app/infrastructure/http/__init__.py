"""HTTP Infrastructure Package.

Provides shared HTTP client utilities.
"""

from src.app.infrastructure.http.base_http_client import (
    BaseHttpClient,
    DEFAULT_HEADERS,
)

__all__ = [
    "BaseHttpClient",
    "DEFAULT_HEADERS",
]

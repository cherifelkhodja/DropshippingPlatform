"""API Routers."""

from .health import router as health_router
from .keywords import router as keywords_router
from .pages import router as pages_router
from .scans import router as scans_router

__all__ = [
    "health_router",
    "keywords_router",
    "pages_router",
    "scans_router",
]

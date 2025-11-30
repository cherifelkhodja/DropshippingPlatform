"""API Routers."""

from .admin import router as admin_router
from .alerts import router as alerts_router
from .health import router as health_router
from .keywords import router as keywords_router
from .pages import router as pages_router
from .products import router as products_router
from .scans import router as scans_router
from .watchlists import router as watchlists_router
from .creative_insights import router as creative_insights_router

__all__ = [
    "admin_router",
    "alerts_router",
    "creative_insights_router",
    "health_router",
    "keywords_router",
    "pages_router",
    "products_router",
    "scans_router",
    "watchlists_router",
]

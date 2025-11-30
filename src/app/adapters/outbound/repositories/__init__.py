"""Outbound Repositories Package.

SQLAlchemy implementations of repository ports.
"""

from src.app.adapters.outbound.repositories.ads_repository import (
    PostgresAdsRepository,
)
from src.app.adapters.outbound.repositories.keyword_run_repository import (
    PostgresKeywordRunRepository,
)
from src.app.adapters.outbound.repositories.page_repository import (
    PostgresPageRepository,
)
from src.app.adapters.outbound.repositories.scan_repository import (
    PostgresScanRepository,
)
from src.app.adapters.outbound.repositories.scoring_repository import (
    PostgresScoringRepository,
)
from src.app.adapters.outbound.repositories.watchlist_repository import (
    PostgresWatchlistRepository,
)
from src.app.adapters.outbound.repositories.product_repository import (
    PostgresProductRepository,
)
from src.app.adapters.outbound.repositories.page_metrics_repository import (
    PostgresPageMetricsRepository,
)

__all__ = [
    "PostgresPageRepository",
    "PostgresAdsRepository",
    "PostgresScanRepository",
    "PostgresKeywordRunRepository",
    "PostgresScoringRepository",
    "PostgresWatchlistRepository",
    "PostgresProductRepository",
    "PostgresPageMetricsRepository",
]

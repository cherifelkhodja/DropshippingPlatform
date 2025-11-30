"""Page Daily Metrics Mapper.

Bidirectional mapping between PageDailyMetrics domain entity and
PageDailyMetricsModel ORM. Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.page_daily_metrics import PageDailyMetrics
from src.app.infrastructure.db.models.page_daily_metrics_model import (
    PageDailyMetricsModel,
)


def to_domain(model: PageDailyMetricsModel) -> PageDailyMetrics:
    """Convert PageDailyMetricsModel ORM instance to PageDailyMetrics domain entity.

    Args:
        model: The PageDailyMetricsModel ORM instance.

    Returns:
        The corresponding PageDailyMetrics domain entity.
    """
    return PageDailyMetrics(
        id=str(model.id),
        page_id=str(model.page_id),
        date=model.date,
        ads_count=model.ads_count,
        shop_score=model.shop_score,
        tier=model.tier,
        products_count=model.products_count,
        created_at=model.created_at,
    )


def to_model(entity: PageDailyMetrics) -> PageDailyMetricsModel:
    """Convert PageDailyMetrics domain entity to PageDailyMetricsModel ORM instance.

    Args:
        entity: The PageDailyMetrics domain entity.

    Returns:
        The corresponding PageDailyMetricsModel ORM instance.
    """
    return PageDailyMetricsModel(
        id=UUID(entity.id),
        page_id=UUID(entity.page_id),
        date=entity.date,
        ads_count=entity.ads_count,
        shop_score=entity.shop_score,
        tier=entity.tier,
        products_count=entity.products_count,
        created_at=entity.created_at,
    )

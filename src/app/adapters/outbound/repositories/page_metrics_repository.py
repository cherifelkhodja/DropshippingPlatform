"""PostgreSQL Page Metrics Repository.

Implements PageMetricsRepository port with SQLAlchemy async operations.
Supports the Historisation & Time Series feature (Sprint 7).
"""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.page_daily_metrics import PageDailyMetrics
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import page_daily_metrics_mapper
from src.app.infrastructure.db.models import PageDailyMetricsModel


class PostgresPageMetricsRepository:
    """SQLAlchemy implementation of PageMetricsRepository port.

    Handles PageDailyMetrics entity persistence with PostgreSQL.
    Uses upsert (INSERT ... ON CONFLICT) for efficient daily snapshots.

    Usage:
        This repository supports time series storage for page metrics,
        enabling evolution graphs and trend analysis for the frontend.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def upsert_daily_metrics(
        self, metrics: Sequence[PageDailyMetrics]
    ) -> None:
        """Upsert daily metrics snapshots in batch.

        Uses PostgreSQL INSERT ... ON CONFLICT DO UPDATE to efficiently
        update existing snapshots or insert new ones based on (page_id, date).

        Args:
            metrics: Sequence of PageDailyMetrics entities to upsert.

        Raises:
            RepositoryError: On database errors.
        """
        if not metrics:
            return

        try:
            for metric in metrics:
                # Prepare values for upsert
                values = {
                    "id": UUID(metric.id),
                    "page_id": UUID(metric.page_id),
                    "date": metric.date,
                    "ads_count": metric.ads_count,
                    "shop_score": metric.shop_score,
                    "tier": metric.tier,
                    "products_count": metric.products_count,
                    "created_at": metric.created_at,
                }

                # Create upsert statement
                stmt = insert(PageDailyMetricsModel).values(**values)
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_page_daily_metrics_page_id_date",
                    set_={
                        "ads_count": stmt.excluded.ads_count,
                        "shop_score": stmt.excluded.shop_score,
                        "tier": stmt.excluded.tier,
                        "products_count": stmt.excluded.products_count,
                        # Note: we don't update created_at on conflict
                    },
                )
                await self._session.execute(stmt)

            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="upsert_daily_metrics",
                reason=f"Failed to upsert page daily metrics: {exc}",
            ) from exc

    async def list_page_metrics(
        self,
        page_id: str,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int | None = None,
    ) -> list[PageDailyMetrics]:
        """List daily metrics for a page with optional date filters.

        Returns metrics ordered by date ascending (oldest first) for
        easy time series visualization in graphs.

        Args:
            page_id: The page identifier to filter by.
            date_from: Optional start date (inclusive).
            date_to: Optional end date (inclusive).
            limit: Optional maximum number of snapshots to return.

        Returns:
            List of PageDailyMetrics entities ordered by date ASC.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Build base query
            stmt = select(PageDailyMetricsModel).where(
                PageDailyMetricsModel.page_id == UUID(page_id)
            )

            # Apply date filters
            if date_from is not None:
                stmt = stmt.where(PageDailyMetricsModel.date >= date_from)
            if date_to is not None:
                stmt = stmt.where(PageDailyMetricsModel.date <= date_to)

            # Order by date ASC for time series visualization
            stmt = stmt.order_by(PageDailyMetricsModel.date.asc())

            # Apply limit if specified
            if limit is not None:
                stmt = stmt.limit(limit)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [page_daily_metrics_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_page_metrics",
                reason=f"Failed to list page metrics: {exc}",
            ) from exc

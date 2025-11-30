"""Metrics Use Cases.

Use cases for page metrics historization and time series analysis.
Sprint 7: Historisation & Time Series.

This module provides:
- RecordDailyMetricsForAllPagesUseCase: Batch snapshot of all pages' metrics
- GetPageMetricsHistoryUseCase: Retrieve metrics history for a page
"""

from dataclasses import dataclass
from datetime import date, datetime
from uuid import uuid4

from ..domain.entities.page import Page
from ..domain.entities.page_daily_metrics import (
    PageDailyMetrics,
    PageMetricsHistoryResult,
)
from ..domain.errors import EntityNotFoundError
from ..domain.tiering import score_to_tier
from ..ports import (
    LoggingPort,
    PageRepository,
    ScoringRepository,
    ProductRepository,
    PageMetricsRepository,
)


@dataclass(frozen=True)
class RecordDailyMetricsResult:
    """Result of the record daily metrics use case.

    Attributes:
        snapshot_date: The date of the recorded snapshots.
        pages_processed: Number of pages processed.
        snapshots_written: Number of snapshots successfully written.
        errors_count: Number of pages that failed processing.
    """

    snapshot_date: date
    pages_processed: int
    snapshots_written: int
    errors_count: int


class RecordDailyMetricsForAllPagesUseCase:
    """Use case for recording daily metrics snapshots for all pages.

    This use case:
    1. Retrieves all active pages from the repository
    2. For each page, gathers current metrics (score, ads count, products count)
    3. Creates PageDailyMetrics snapshots
    4. Persists the snapshots via PageMetricsRepository

    Usage:
        This use case is typically called by a scheduled Celery task
        (snapshot_daily_metrics) to record daily metrics for trend analysis.
    """

    def __init__(
        self,
        page_repository: PageRepository,
        scoring_repository: ScoringRepository,
        product_repository: ProductRepository,
        page_metrics_repository: PageMetricsRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            page_repository: Repository for Page entities.
            scoring_repository: Repository for ShopScore entities.
            product_repository: Repository for Product entities.
            page_metrics_repository: Repository for PageDailyMetrics entities.
            logger: Logging port for structured logging.
        """
        self._page_repo = page_repository
        self._scoring_repo = scoring_repository
        self._product_repo = product_repository
        self._metrics_repo = page_metrics_repository
        self._logger = logger

    async def execute(
        self, snapshot_date: date | None = None
    ) -> RecordDailyMetricsResult:
        """Execute the record daily metrics use case.

        Args:
            snapshot_date: The date to record metrics for.
                           Defaults to today if not specified.

        Returns:
            RecordDailyMetricsResult with processing summary.
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        self._logger.info(
            "Starting daily metrics recording",
            snapshot_date=str(snapshot_date),
        )

        # 1. Retrieve all pages
        pages = await self._page_repo.list_all()
        pages_count = len(pages)

        self._logger.info(
            "Retrieved pages for metrics snapshot",
            pages_count=pages_count,
        )

        # 2. Build metrics for each page
        metrics_to_write: list[PageDailyMetrics] = []
        errors_count = 0

        for page in pages:
            try:
                metric = await self._build_metric_for_page(page, snapshot_date)
                if metric:
                    metrics_to_write.append(metric)
            except Exception as exc:
                errors_count += 1
                self._logger.warning(
                    "Failed to build metrics for page",
                    page_id=page.id,
                    error=str(exc),
                )

        # 3. Write all metrics in batch
        if metrics_to_write:
            await self._metrics_repo.upsert_daily_metrics(metrics_to_write)

        snapshots_written = len(metrics_to_write)

        self._logger.info(
            "Daily metrics recording completed",
            snapshot_date=str(snapshot_date),
            pages_processed=pages_count,
            snapshots_written=snapshots_written,
            errors_count=errors_count,
        )

        return RecordDailyMetricsResult(
            snapshot_date=snapshot_date,
            pages_processed=pages_count,
            snapshots_written=snapshots_written,
            errors_count=errors_count,
        )

    async def _build_metric_for_page(
        self, page: Page, snapshot_date: date
    ) -> PageDailyMetrics | None:
        """Build a PageDailyMetrics snapshot for a single page.

        Args:
            page: The Page entity to build metrics for.
            snapshot_date: The date of the snapshot.

        Returns:
            A PageDailyMetrics entity, or None if no score exists.
        """
        # Get latest shop score
        latest_score = await self._scoring_repo.get_latest_by_page_id(page.id)

        if latest_score is None:
            # No score for this page yet, skip
            self._logger.debug(
                "Skipping page without score",
                page_id=page.id,
            )
            return None

        # Get products count (optional)
        products_count: int | None = None
        try:
            products_count = await self._product_repo.count_by_page(page.id)
        except Exception:
            # Products count is optional, don't fail the whole snapshot
            pass

        # Build the metric snapshot
        metric = PageDailyMetrics.create(
            id=str(uuid4()),
            page_id=page.id,
            snapshot_date=snapshot_date,
            ads_count=page.active_ads_count,
            shop_score=latest_score.score,
            products_count=products_count,
        )

        return metric


class GetPageMetricsHistoryUseCase:
    """Use case for retrieving page metrics history.

    This use case:
    1. Validates the page exists (optional, for better error messages)
    2. Retrieves metrics history from PageMetricsRepository
    3. Returns a structured result with the metrics list

    Usage:
        Used by the API endpoint GET /pages/{page_id}/metrics/history
        to provide time series data for frontend graphs.
    """

    def __init__(
        self,
        page_repository: PageRepository,
        page_metrics_repository: PageMetricsRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            page_repository: Repository for Page entities.
            page_metrics_repository: Repository for PageDailyMetrics entities.
            logger: Logging port for structured logging.
        """
        self._page_repo = page_repository
        self._metrics_repo = page_metrics_repository
        self._logger = logger

    async def execute(
        self,
        page_id: str,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int | None = None,
    ) -> PageMetricsHistoryResult:
        """Execute the get page metrics history use case.

        Args:
            page_id: The page identifier.
            date_from: Optional start date (inclusive).
            date_to: Optional end date (inclusive).
            limit: Optional maximum number of snapshots (max 90 recommended).

        Returns:
            PageMetricsHistoryResult with the metrics history.

        Raises:
            EntityNotFoundError: If the page does not exist.
        """
        self._logger.debug(
            "Retrieving page metrics history",
            page_id=page_id,
            date_from=str(date_from) if date_from else None,
            date_to=str(date_to) if date_to else None,
            limit=limit,
        )

        # 1. Verify page exists (optional but provides better error messages)
        page = await self._page_repo.get(page_id)
        if page is None:
            self._logger.warning(
                "Page not found for metrics history",
                page_id=page_id,
            )
            raise EntityNotFoundError("Page", page_id)

        # 2. Apply default limit for safety (max 90 points for ~3 months)
        if limit is None or limit > 90:
            limit = 90

        # 3. Retrieve metrics history
        metrics = await self._metrics_repo.list_page_metrics(
            page_id=page_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        self._logger.info(
            "Page metrics history retrieved",
            page_id=page_id,
            metrics_count=len(metrics),
        )

        return PageMetricsHistoryResult(
            page_id=page_id,
            metrics=metrics,
        )

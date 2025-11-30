"""Monitoring Use Cases.

Use cases for system monitoring and status reporting.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from ..ports import (
    LoggingPort,
    PageRepository,
    ScoringRepository,
    AlertRepository,
    PageMetricsRepository,
)


@dataclass
class MonitoringSummary:
    """Summary of system status for monitoring dashboard.

    Contains aggregated information about recent system activity
    including pages, scores, alerts, and metrics snapshots.
    """

    # Pages
    total_pages: int
    pages_with_scores: int

    # Alerts
    alerts_last_24h: int
    alerts_last_7d: int

    # Metrics
    last_metrics_snapshot_date: Optional[str]
    metrics_snapshots_count: int

    # Generated at
    generated_at: datetime


class GetMonitoringSummaryUseCase:
    """Use case for retrieving system monitoring summary.

    Aggregates data from multiple repositories to provide
    a comprehensive view of system status.
    """

    def __init__(
        self,
        page_repository: PageRepository,
        scoring_repository: ScoringRepository,
        alert_repository: AlertRepository,
        metrics_repository: PageMetricsRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            page_repository: Repository for Page entities.
            scoring_repository: Repository for ShopScore entities.
            alert_repository: Repository for Alert entities.
            metrics_repository: Repository for PageDailyMetrics entities.
            logger: Logging port for structured logging.
        """
        self._page_repo = page_repository
        self._scoring_repo = scoring_repository
        self._alert_repo = alert_repository
        self._metrics_repo = metrics_repository
        self._logger = logger

    async def execute(self) -> MonitoringSummary:
        """Execute the monitoring summary use case.

        Returns:
            MonitoringSummary with aggregated system status.
        """
        self._logger.info("Generating monitoring summary")

        now = datetime.utcnow()

        # Get page counts
        all_pages = await self._page_repo.list_all()
        total_pages = len(all_pages)

        # Count pages with scores
        pages_with_scores = 0
        for page in all_pages:
            score = await self._scoring_repo.get_latest_by_page_id(page.id)
            if score:
                pages_with_scores += 1

        # Get alert counts
        recent_alerts = await self._alert_repo.list_recent(limit=1000)
        alerts_24h = 0
        alerts_7d = 0
        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)

        for alert in recent_alerts:
            if alert.created_at >= cutoff_24h:
                alerts_24h += 1
            if alert.created_at >= cutoff_7d:
                alerts_7d += 1

        # Get metrics info - check first page's metrics
        last_snapshot_date: Optional[str] = None
        metrics_count = 0

        if all_pages:
            # Get metrics for the first page to find latest date
            metrics = await self._metrics_repo.list_page_metrics(
                page_id=all_pages[0].id,
                limit=1,
            )
            if metrics:
                last_snapshot_date = metrics[0].date.isoformat()

            # Count total metrics entries (sample from first few pages)
            for page in all_pages[:10]:
                page_metrics = await self._metrics_repo.list_page_metrics(
                    page_id=page.id,
                    limit=365,
                )
                metrics_count += len(page_metrics)

        self._logger.info(
            "Monitoring summary generated",
            total_pages=total_pages,
            pages_with_scores=pages_with_scores,
            alerts_24h=alerts_24h,
        )

        return MonitoringSummary(
            total_pages=total_pages,
            pages_with_scores=pages_with_scores,
            alerts_last_24h=alerts_24h,
            alerts_last_7d=alerts_7d,
            last_metrics_snapshot_date=last_snapshot_date,
            metrics_snapshots_count=metrics_count,
            generated_at=now,
        )

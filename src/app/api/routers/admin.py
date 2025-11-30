"""Admin monitoring API router.

Provides endpoints for monitoring pages, keywords, and scans.
All endpoints are protected by API key authentication when
SECURITY_ADMIN_API_KEY is configured.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.app.api.dependencies import (
    KeywordRunRepo,
    PageRepo,
    ScanRepo,
    get_admin_auth,
)
from src.app.api.schemas.admin import (
    AdminKeywordListResponse,
    AdminKeywordRunResponse,
    AdminPageListResponse,
    AdminPageResponse,
    AdminScanListResponse,
    AdminScanResponse,
)
from src.app.api.schemas.metrics import (
    TriggerDailySnapshotRequest,
    TriggerDailySnapshotResponse,
)
from src.app.core.domain.entities.keyword_run import KeywordRun
from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.scan import Scan

# All admin routes require authentication via X-Admin-Api-Key header
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_auth)],
)


def _page_to_admin_response(page: Page) -> AdminPageResponse:
    """Convert domain Page to admin API response."""
    return AdminPageResponse(
        page_id=page.id,
        page_name=page.domain,
        country=str(page.country) if page.country else None,
        is_shopify=page.is_shopify,
        ads_count=page.active_ads_count,
        product_count=page.product_count.value if page.product_count else 0,
        state=page.state.status.value,
        last_scan_at=page.last_scanned_at,
    )


def _keyword_run_to_admin_response(run: KeywordRun) -> AdminKeywordRunResponse:
    """Convert domain KeywordRun to admin API response."""
    return AdminKeywordRunResponse(
        keyword=run.keyword,
        country=str(run.country),
        created_at=run.created_at,
        total_ads_found=run.result.total_ads_found if run.result else 0,
        total_pages_found=run.result.unique_pages_found if run.result else 0,
        scan_id=str(run.id),
    )


def _scan_to_admin_response(scan: Scan) -> AdminScanResponse:
    """Convert domain Scan to admin API response."""
    result_summary = None
    if scan.result:
        result_summary = (
            f"ads={scan.result.ads_found}, "
            f"products={scan.result.products_found}, "
            f"shopify={scan.result.is_shopify}"
        )
    return AdminScanResponse(
        id=str(scan.id),
        status=scan.status.value,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        page_id=scan.page_id,
        result_summary=result_summary,
    )


@router.get(
    "/pages/active",
    response_model=AdminPageListResponse,
    summary="List active pages",
    description="Get a paginated list of pages with optional filters.",
)
async def list_active_pages(
    page_repo: PageRepo,
    country: str | None = Query(
        default=None, min_length=2, max_length=2, description="Filter by country"
    ),
    is_shopify: bool | None = Query(default=None, description="Filter by Shopify"),
    min_ads: int | None = Query(default=None, ge=0, description="Min active ads"),
    max_ads: int | None = Query(default=None, ge=0, description="Max active ads"),
    state: str | None = Query(default=None, description="Filter by state"),
    offset: int = Query(default=0, ge=0, description="Offset"),
    limit: int = Query(default=50, ge=1, le=100, description="Limit"),
) -> AdminPageListResponse:
    """List active pages with filtering options."""
    # Get all pages and filter in memory (for simplicity)
    # In production, this should be done with database queries
    all_pages = await page_repo.list_all()

    # Apply filters
    filtered_pages = all_pages
    if country:
        filtered_pages = [
            p for p in filtered_pages if p.country and str(p.country) == country
        ]
    if is_shopify is not None:
        filtered_pages = [p for p in filtered_pages if p.is_shopify == is_shopify]
    if min_ads is not None:
        filtered_pages = [p for p in filtered_pages if p.active_ads_count >= min_ads]
    if max_ads is not None:
        filtered_pages = [p for p in filtered_pages if p.active_ads_count <= max_ads]
    if state:
        filtered_pages = [p for p in filtered_pages if p.state.status.value == state]

    total = len(filtered_pages)
    paginated = filtered_pages[offset : offset + limit]

    return AdminPageListResponse(
        items=[_page_to_admin_response(p) for p in paginated],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/keywords/recent",
    response_model=AdminKeywordListResponse,
    summary="List recent keyword runs",
    description="Get the most recent keyword search runs.",
)
async def list_recent_keywords(
    keyword_run_repo: KeywordRunRepo,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum runs to return"),
) -> AdminKeywordListResponse:
    """List recent keyword runs."""
    runs = await keyword_run_repo.list_recent(limit=limit)

    return AdminKeywordListResponse(
        items=[_keyword_run_to_admin_response(r) for r in runs],
        total=len(runs),
    )


@router.get(
    "/scans",
    response_model=AdminScanListResponse,
    summary="List scans",
    description="Get a paginated list of scans with optional filters.",
)
async def list_scans(
    scan_repo: ScanRepo,
    status: str | None = Query(default=None, description="Filter by status"),
    since: datetime | None = Query(default=None, description="Filter by start date"),
    page_id: str | None = Query(default=None, description="Filter by page ID"),
    offset: int = Query(default=0, ge=0, description="Offset"),
    limit: int = Query(default=50, ge=1, le=100, description="Limit"),
) -> AdminScanListResponse:
    """List scans with filtering options."""
    # Get scans using repository method
    scans = await scan_repo.list_scans(
        status=status,
        since=since,
        page_id=page_id,
        offset=offset,
        limit=limit,
    )

    return AdminScanListResponse(
        items=[_scan_to_admin_response(s) for s in scans],
        total=len(scans),
        offset=offset,
        limit=limit,
    )


# =============================================================================
# Metrics Admin Endpoints
# =============================================================================


@router.post(
    "/metrics/daily-snapshot",
    response_model=TriggerDailySnapshotResponse,
    summary="Trigger daily metrics snapshot",
    description="Dispatch a Celery task to record daily metrics for all pages.",
)
async def trigger_daily_snapshot(
    request: TriggerDailySnapshotRequest = TriggerDailySnapshotRequest(),
) -> TriggerDailySnapshotResponse:
    """Trigger a daily metrics snapshot task.

    This admin endpoint dispatches a Celery task to record daily metrics
    snapshots for all pages.

    The task will:
    1. Retrieve all pages with existing scores
    2. Create daily snapshots with current metrics
    3. Store them for time series analysis
    """
    from src.app.infrastructure.celery.tasks import snapshot_daily_metrics_task

    # Dispatch the task
    task_result = snapshot_daily_metrics_task.delay(
        snapshot_date=request.snapshot_date
    )

    return TriggerDailySnapshotResponse(
        status="dispatched",
        task_id=str(task_result.id),
        snapshot_date=request.snapshot_date,
    )

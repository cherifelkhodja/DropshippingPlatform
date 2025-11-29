"""Page endpoints."""

from fastapi import APIRouter, Query

from src.app.api.schemas.pages import PageResponse, PageListResponse
from src.app.api.schemas.scoring import (
    ShopScoreResponse,
    ScoreComponentsResponse,
    TopShopEntry,
    TopShopsResponse,
    RecomputeScoreResponse,
)
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import PageRepo, ScoringRepo, ComputeShopScoreUC
from src.app.core.domain.entities.page import Page
from src.app.core.domain.errors import EntityNotFoundError
from src.app.infrastructure.celery.tasks import compute_shop_score_task

router = APIRouter(prefix="/pages", tags=["Pages"])


def _page_to_response(page: Page) -> PageResponse:
    """Convert domain Page to API response."""
    return PageResponse(
        id=page.id,
        url=str(page.url),
        domain=page.domain,
        country=str(page.country) if page.country else None,
        language=str(page.language) if page.language else None,
        currency=str(page.currency) if page.currency else None,
        category=str(page.category) if page.category else None,
        is_shopify=page.is_shopify,
        product_count=int(page.product_count),
        active_ads_count=page.active_ads_count,
        total_ads_count=page.total_ads_count,
        status=page.state.status.value,
        score=page.score,
        first_seen_at=page.first_seen_at,
        last_scanned_at=page.last_scanned_at,
    )


@router.get(
    "",
    response_model=PageListResponse,
    summary="List pages",
    description="List tracked pages with optional filters.",
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_pages(
    page_repo: PageRepo,
    country: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Filter by country code",
    ),
    is_shopify: bool | None = Query(
        default=None,
        description="Filter by Shopify status",
    ),
    min_active_ads: int | None = Query(
        default=None,
        ge=0,
        description="Minimum active ads count",
    ),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
) -> PageListResponse:
    """List all tracked pages with optional filtering.

    Returns a paginated list of pages matching the specified criteria.
    """
    # Get all pages (filtering will be done in memory for simplicity)
    # In production, this should use proper database-level filtering
    all_pages = await page_repo.list_all()

    # Apply filters
    filtered = all_pages
    if country:
        filtered = [p for p in filtered if p.country and str(p.country) == country]
    if is_shopify is not None:
        filtered = [p for p in filtered if p.is_shopify == is_shopify]
    if min_active_ads is not None:
        filtered = [p for p in filtered if p.active_ads_count >= min_active_ads]

    # Sort by active_ads_count descending
    filtered.sort(key=lambda p: p.active_ads_count, reverse=True)

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    return PageListResponse(
        items=[_page_to_response(p) for p in paginated],
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@router.get(
    "/top",
    response_model=TopShopsResponse,
    summary="Get top-ranked shops",
    description="Get a list of top-ranked shops sorted by score.",
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_top_shops(
    page_repo: PageRepo,
    scoring_repo: ScoringRepo,
    limit: int = Query(default=50, ge=1, le=100, description="Number of top shops"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> TopShopsResponse:
    """Get top-ranked shops by score.

    Returns a list of shops ordered by their computed score,
    from highest to lowest.
    """
    # Get top scores from scoring repository
    top_scores = await scoring_repo.list_top(limit=limit, offset=offset)

    # Get total count for pagination
    # Note: This is a simplified approach - in production, use a count query
    all_scores = await scoring_repo.list_top(limit=10000, offset=0)
    total = len(all_scores)

    # Build response with page domain info
    items = []
    for rank, score in enumerate(top_scores, start=offset + 1):
        page = await page_repo.get(score.page_id)
        domain = page.domain if page else "unknown"

        items.append(
            TopShopEntry(
                rank=rank,
                page_id=score.page_id,
                domain=domain,
                score=score.score,
                tier=score.tier,
                computed_at=score.created_at,
            )
        )

    return TopShopsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{page_id}",
    response_model=PageResponse,
    summary="Get page details",
    description="Get detailed information about a specific page.",
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_page(
    page_id: str,
    page_repo: PageRepo,
) -> PageResponse:
    """Get details of a specific page by ID."""
    page = await page_repo.get(page_id)

    if page is None:
        raise EntityNotFoundError("Page", page_id)

    return _page_to_response(page)


@router.get(
    "/{page_id}/score",
    response_model=ShopScoreResponse,
    summary="Get page score",
    description="Get the computed score for a specific page.",
    responses={
        404: {"model": ErrorResponse, "description": "Page or score not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_page_score(
    page_id: str,
    page_repo: PageRepo,
    scoring_repo: ScoringRepo,
) -> ShopScoreResponse:
    """Get the latest computed score for a page.

    Returns the score breakdown including individual components
    (ads activity, shopify, creative quality, catalog).
    """
    # Verify page exists
    page = await page_repo.get(page_id)
    if page is None:
        raise EntityNotFoundError("Page", page_id)

    # Get latest score
    score = await scoring_repo.get_latest_by_page_id(page_id)
    if score is None:
        raise EntityNotFoundError("ShopScore", page_id)

    return ShopScoreResponse(
        page_id=score.page_id,
        score=score.score,
        tier=score.tier,
        components=ScoreComponentsResponse(
            ads_activity=score.components.get("ads_activity", 0.0),
            shopify=score.components.get("shopify", 0.0),
            creative_quality=score.components.get("creative_quality", 0.0),
            catalog=score.components.get("catalog", 0.0),
        ),
        computed_at=score.created_at,
    )


@router.post(
    "/{page_id}/score/recompute",
    response_model=RecomputeScoreResponse,
    summary="Recompute page score",
    description="Dispatch a task to recompute the score for a page.",
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Task dispatch error"},
    },
)
async def recompute_page_score(
    page_id: str,
    page_repo: PageRepo,
) -> RecomputeScoreResponse:
    """Dispatch a background task to recompute the page score.

    The task will gather current data (ads, Shopify profile, products)
    and calculate a new score. The task ID can be used to track progress.
    """
    # Verify page exists
    page = await page_repo.get(page_id)
    if page is None:
        raise EntityNotFoundError("Page", page_id)

    # Dispatch Celery task
    task = compute_shop_score_task.delay(page_id=page_id)

    return RecomputeScoreResponse(
        page_id=page_id,
        task_id=str(task.id),
        status="dispatched",
    )

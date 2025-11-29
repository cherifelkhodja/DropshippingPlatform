"""Page endpoints."""

from fastapi import APIRouter, Query

from src.app.api.schemas.pages import PageResponse, PageListResponse
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import PageRepo
from src.app.core.domain.errors import EntityNotFoundError

router = APIRouter(prefix="/pages", tags=["Pages"])


def _page_to_response(page: "Page") -> PageResponse:  # type: ignore[name-defined]
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

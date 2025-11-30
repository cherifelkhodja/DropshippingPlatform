"""Page endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Query

from src.app.api.schemas.pages import PageResponse, PageListResponse
from src.app.api.schemas.metrics import (
    PageDailyMetricsResponse,
    PageMetricsHistoryResponse,
)
from src.app.api.schemas.scoring import (
    ShopScoreResponse,
    ScoreComponentsResponse,
    TopShopEntry,
    TopShopsResponse,
    RecomputeScoreResponse,
    RankedShopsResponse,
    ranked_result_to_response,
)
from src.app.api.schemas.products import (
    ProductResponse,
    ProductListResponse,
    SyncProductsResponse,
    PageProductInsightsResponse,
    ProductInsightsEntry,
    ProductInsightsSortBy,
    product_to_response,
    product_insights_to_entry,
    product_insights_to_data,
    page_product_insights_to_response,
)
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import (
    PageRepo,
    ScoringRepo,
    TaskDispatcher,
    GetRankedShopsUC,
    ProductRepo,
    SyncProductsUC,
    BuildProductInsightsUC,
    GetPageMetricsHistoryUC,
)
from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.product import Product
from src.app.core.domain.errors import EntityNotFoundError
from src.app.core.domain.value_objects.ranking import RankingCriteria


def _product_to_response(product: Product) -> ProductResponse:
    """Convert domain Product to API response."""
    return ProductResponse(
        id=product.id,
        page_id=product.page_id,
        handle=product.handle,
        title=product.title,
        url=product.url,
        price_min=product.price_min,
        price_max=product.price_max,
        currency=product.currency,
        available=product.available,
        tags=product.tags,
        vendor=product.vendor,
        image_url=product.image_url,
        product_type=product.product_type,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )

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
    "/ranked",
    response_model=RankedShopsResponse,
    summary="Get ranked shops with filters",
    description="Get a paginated list of shops ranked by score with optional filters.",
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_ranked_shops(
    get_ranked_shops_uc: GetRankedShopsUC,
    limit: int = Query(default=50, ge=1, le=200, description="Number of shops to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    tier: str | None = Query(
        default=None,
        description="Filter by tier (XS, S, M, L, XL, XXL)",
        pattern="^(XS|S|M|L|XL|XXL)$",
    ),
    min_score: float | None = Query(
        default=None,
        ge=0,
        le=100,
        description="Minimum score filter (0-100)",
    ),
    country: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Filter by country code (ISO 3166-1 alpha-2)",
    ),
) -> RankedShopsResponse:
    """Get ranked shops with optional filters.

    Returns a paginated list of shops ordered by score (highest first),
    with optional filtering by tier, minimum score, and country.
    """
    # Build criteria from query params (RankingCriteria handles validation)
    criteria = RankingCriteria(
        limit=limit,
        offset=offset,
        tier=tier,
        min_score=min_score,
        country=country,
    )

    # Execute use case
    result = await get_ranked_shops_uc.execute(criteria)

    # Convert to API response
    return ranked_result_to_response(result)


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
    get_ranked_shops_uc: GetRankedShopsUC,
    page_repo: PageRepo,
    limit: int = Query(default=50, ge=1, le=100, description="Number of top shops"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> TopShopsResponse:
    """Get top-ranked shops by score.

    Returns a list of shops ordered by their computed score,
    from highest to lowest. Uses the ranking use case internally.

    Note: This endpoint is kept for backwards compatibility.
    For new integrations, consider using /pages/ranked which offers
    more filtering options.
    """
    # Use the ranking use case with no filters
    criteria = RankingCriteria(limit=limit, offset=offset)
    result = await get_ranked_shops_uc.execute(criteria)

    # Build response in the legacy TopShopsResponse format
    items = []
    for rank, shop in enumerate(result.items, start=offset + 1):
        # For domain, we use the name field (which contains domain) or fetch from page
        domain = shop.name
        if not domain:
            page = await page_repo.get(shop.page_id)
            domain = page.domain if page else "unknown"

        items.append(
            TopShopEntry(
                rank=rank,
                page_id=shop.page_id,
                domain=domain,
                score=shop.score,
                tier=shop.tier,
                # Note: RankedShop doesn't have computed_at timestamp.
                # Using current time as a placeholder for backwards compatibility.
                # The new /pages/ranked endpoint doesn't include this field.
                computed_at=datetime.utcnow(),
            )
        )

    return TopShopsResponse(
        items=items,
        total=result.total,
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
    task_dispatcher: TaskDispatcher,
) -> RecomputeScoreResponse:
    """Dispatch a background task to recompute the page score.

    The task will gather current data (ads, Shopify profile, products)
    and calculate a new score. The task ID can be used to track progress.
    """
    # Verify page exists
    page = await page_repo.get(page_id)
    if page is None:
        raise EntityNotFoundError("Page", page_id)

    # Dispatch task via TaskDispatcher (decoupled from Celery)
    task_id = await task_dispatcher.dispatch_compute_shop_score(page_id=page_id)

    return RecomputeScoreResponse(
        page_id=page_id,
        task_id=task_id,
        status="dispatched",
    )


# =============================================================================
# Product Endpoints
# =============================================================================


@router.get(
    "/{page_id}/products",
    response_model=ProductListResponse,
    summary="List products for a page",
    description="Get the list of products for a specific page (store).",
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_page_products(
    page_id: str,
    page_repo: PageRepo,
    product_repo: ProductRepo,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum products to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> ProductListResponse:
    """List products for a specific page.

    Returns a paginated list of products from the store's catalog.
    Products are ordered by title ascending.
    """
    # Verify page exists
    page = await page_repo.get(page_id)
    if page is None:
        raise EntityNotFoundError("Page", page_id)

    # Get products
    products = await product_repo.list_by_page(page_id, limit=limit, offset=offset)
    total = await product_repo.count_by_page(page_id)

    return ProductListResponse(
        items=[_product_to_response(p) for p in products],
        total=total,
        page_id=page_id,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{page_id}/products/sync",
    response_model=SyncProductsResponse,
    summary="Sync products for a page",
    description="Synchronize products from a Shopify store's catalog.",
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Sync error"},
    },
)
async def sync_page_products(
    page_id: str,
    sync_products_uc: SyncProductsUC,
) -> SyncProductsResponse:
    """Synchronize products for a Shopify page.

    Fetches products from the store's /products.json endpoint and
    upserts them to the database. For non-Shopify stores or stores
    without accessible products.json, returns an appropriate error.
    """
    result = await sync_products_uc.execute(page_id=page_id)

    return SyncProductsResponse(
        page_id=result.page_id,
        products_synced=result.products_synced,
        products_extracted=result.products_extracted,
        is_shopify=result.is_shopify,
        source=result.source,
        error=result.error,
    )


# =============================================================================
# Product Insights Endpoints
# =============================================================================


@router.get(
    "/{page_id}/products/insights",
    response_model=PageProductInsightsResponse,
    summary="Get product insights for a page",
    description="Get product-ad matching insights for all products in a page.",
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Error computing insights"},
    },
)
async def get_page_product_insights(
    page_id: str,
    build_insights_uc: BuildProductInsightsUC,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    sort_by: ProductInsightsSortBy = Query(
        default=ProductInsightsSortBy.ADS_COUNT,
        description="Sort by: ads_count (default), match_score, or last_seen_at",
    ),
) -> PageProductInsightsResponse:
    """Get product insights for a page.

    Returns aggregated product-ad matching insights for all products
    in the specified page. Results can be sorted by ads_count,
    match_score, or last_seen_at.

    The response includes:
    - Summary with coverage and promotion ratios
    - Paginated list of products with their matched ads
    """
    # Execute use case (handles page existence check)
    result = await build_insights_uc.execute(page_id=page_id)

    page_insights = result.insights
    all_insights = page_insights.product_insights

    # Sort insights based on sort_by parameter
    def get_last_seen(insight):
        """Extract last_seen_at from matched ads for sorting."""
        if not insight.matched_ads:
            return datetime.min
        last_seen = None
        for match in insight.matched_ads:
            ad_last = match.ad.last_seen_at
            if ad_last and (last_seen is None or ad_last > last_seen):
                last_seen = ad_last
        return last_seen or datetime.min

    if sort_by == ProductInsightsSortBy.ADS_COUNT:
        sorted_insights = sorted(
            all_insights,
            key=lambda i: len(i.matched_ads),
            reverse=True,
        )
    elif sort_by == ProductInsightsSortBy.MATCH_SCORE:
        sorted_insights = sorted(
            all_insights,
            key=lambda i: i.match_score,
            reverse=True,
        )
    else:  # LAST_SEEN_AT
        sorted_insights = sorted(
            all_insights,
            key=get_last_seen,
            reverse=True,
        )

    # Apply pagination
    paginated_insights = sorted_insights[offset : offset + limit]

    return page_product_insights_to_response(
        page_insights=page_insights,
        sorted_insights=paginated_insights,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{page_id}/products/{product_id}/insights",
    response_model=ProductInsightsEntry,
    summary="Get insights for a specific product",
    description="Get product-ad matching insights for a specific product.",
    responses={
        404: {"model": ErrorResponse, "description": "Page or product not found"},
        500: {"model": ErrorResponse, "description": "Error computing insights"},
    },
)
async def get_product_insights(
    page_id: str,
    product_id: str,
    build_insights_uc: BuildProductInsightsUC,
) -> ProductInsightsEntry:
    """Get insights for a specific product.

    Returns the product details along with its matched ads
    and computed insights (match score, promotion status, etc.).
    """
    # Execute use case for single product
    product_insight = await build_insights_uc.execute_for_product(
        page_id=page_id,
        product_id=product_id,
    )

    return product_insights_to_entry(product_insight)


# =============================================================================
# Metrics History Endpoints
# =============================================================================


@router.get(
    "/{page_id}/metrics/history",
    response_model=PageMetricsHistoryResponse,
    summary="Get page metrics history",
    description=(
        "Get historical daily metrics for a page. Returns time series data "
        "ordered by date ascending (oldest first) for graph visualization."
    ),
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_page_metrics_history(
    page_id: str,
    get_metrics_uc: GetPageMetricsHistoryUC,
    date_from: date | None = Query(
        default=None,
        description="Start date filter (inclusive, YYYY-MM-DD)",
    ),
    date_to: date | None = Query(
        default=None,
        description="End date filter (inclusive, YYYY-MM-DD)",
    ),
    limit: int | None = Query(
        default=90,
        ge=1,
        le=365,
        description="Maximum number of data points (default: 90, max: 365)",
    ),
) -> PageMetricsHistoryResponse:
    """Get page metrics history for time series analysis.

    Returns daily snapshots of key metrics (ads_count, shop_score, tier,
    products_count) for the specified page. Results are ordered by date
    ascending (oldest first) for easy time series visualization.

    Use cases:
    - Evolution graphs showing score/ads trends over time
    - Weak signal detection for early warning indicators
    - Performance tracking and analysis
    """
    result = await get_metrics_uc.execute(
        page_id=page_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )

    return PageMetricsHistoryResponse(
        page_id=result.page_id,
        metrics=[
            PageDailyMetricsResponse(
                date=m.date,
                ads_count=m.ads_count,
                shop_score=m.shop_score,
                tier=m.tier,
                products_count=m.products_count,
            )
            for m in result.metrics
        ],
    )

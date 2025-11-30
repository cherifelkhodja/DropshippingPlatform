"""Watchlist endpoints.

REST API endpoints for managing watchlists and their items.
"""

from fastapi import APIRouter, Query, Response, status

from src.app.api.schemas.common import ErrorResponse
from src.app.api.schemas.watchlists import (
    WatchlistCreateRequest,
    WatchlistResponse,
    WatchlistListResponse,
    WatchlistItemRequest,
    WatchlistItemResponse,
    WatchlistItemListResponse,
    RescoreWatchlistResponse,
    WatchlistSummaryResponse,
    WatchlistSummaryListResponse,
    WatchlistWithDetailsResponse,
    WatchlistPageInfoResponse,
    PageWatchlistsResponse,
    watchlist_to_response,
    watchlist_item_to_response,
)
from src.app.api.dependencies import (
    CreateWatchlistUC,
    GetWatchlistUC,
    ListWatchlistsUC,
    AddPageToWatchlistUC,
    RemovePageFromWatchlistUC,
    ListWatchlistItemsUC,
    RescoreWatchlistUC,
    GetWatchlistWithDetailsUC,
    ListWatchlistsWithCountsUC,
    GetPageWatchlistsUC,
)

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


@router.post(
    "",
    response_model=WatchlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a watchlist",
    description="Create a new watchlist for tracking pages.",
    responses={
        201: {"description": "Watchlist created successfully"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def create_watchlist(
    request: WatchlistCreateRequest,
    create_watchlist_uc: CreateWatchlistUC,
) -> WatchlistResponse:
    """Create a new watchlist.

    Creates a watchlist with the given name and optional description.
    """
    watchlist = await create_watchlist_uc.execute(
        name=request.name,
        description=request.description,
    )
    return watchlist_to_response(watchlist)


@router.get(
    "",
    response_model=WatchlistListResponse,
    summary="List watchlists",
    description="List all watchlists with optional pagination.",
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_watchlists(
    list_watchlists_uc: ListWatchlistsUC,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of items"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> WatchlistListResponse:
    """List all watchlists.

    Returns a list of watchlists ordered by creation date (newest first).
    """
    watchlists = await list_watchlists_uc.execute(limit=limit, offset=offset)
    return WatchlistListResponse(
        items=[watchlist_to_response(w) for w in watchlists],
        count=len(watchlists),
    )


@router.get(
    "/summary",
    response_model=WatchlistSummaryListResponse,
    summary="List watchlists with counts",
    description="List all watchlists with their page counts.",
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_watchlists_with_counts(
    list_watchlists_counts_uc: ListWatchlistsWithCountsUC,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of items"),
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
) -> WatchlistSummaryListResponse:
    """List all watchlists with page counts.

    Returns a list of watchlists with their item counts for overview displays.
    """
    summaries = await list_watchlists_counts_uc.execute(limit=limit, offset=offset)
    return WatchlistSummaryListResponse(
        items=[
            WatchlistSummaryResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                created_at=s.created_at,
                is_active=s.is_active,
                pages_count=s.pages_count,
            )
            for s in summaries
        ],
        count=len(summaries),
    )


@router.get(
    "/{watchlist_id}",
    response_model=WatchlistResponse,
    summary="Get watchlist details",
    description="Get detailed information about a specific watchlist.",
    responses={
        404: {"model": ErrorResponse, "description": "Watchlist not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_watchlist(
    watchlist_id: str,
    get_watchlist_uc: GetWatchlistUC,
) -> WatchlistResponse:
    """Get details of a specific watchlist by ID."""
    watchlist = await get_watchlist_uc.execute(watchlist_id)
    return watchlist_to_response(watchlist)


@router.get(
    "/{watchlist_id}/details",
    response_model=WatchlistWithDetailsResponse,
    summary="Get watchlist with page details",
    description="Get watchlist with full details for each page including scores.",
    responses={
        404: {"model": ErrorResponse, "description": "Watchlist not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_watchlist_with_details(
    watchlist_id: str,
    get_details_uc: GetWatchlistWithDetailsUC,
) -> WatchlistWithDetailsResponse:
    """Get a watchlist with enriched page information.

    Returns the watchlist with full details for each page including
    current scores, tiers, and active ads counts.
    """
    details = await get_details_uc.execute(watchlist_id)
    return WatchlistWithDetailsResponse(
        id=details.id,
        name=details.name,
        description=details.description,
        created_at=details.created_at,
        is_active=details.is_active,
        pages_count=details.pages_count,
        pages=[
            WatchlistPageInfoResponse(
                page_id=p.page_id,
                page_name=p.page_name,
                url=p.url,
                country=p.country,
                is_shopify=p.is_shopify,
                shop_score=p.shop_score,
                tier=p.tier,
                active_ads_count=p.active_ads_count,
                added_at=p.added_at,
            )
            for p in details.pages
        ],
    )


@router.get(
    "/{watchlist_id}/items",
    response_model=WatchlistItemListResponse,
    summary="List watchlist items",
    description="List all pages in a watchlist.",
    responses={
        404: {"model": ErrorResponse, "description": "Watchlist not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def list_watchlist_items(
    watchlist_id: str,
    list_items_uc: ListWatchlistItemsUC,
) -> WatchlistItemListResponse:
    """List all items in a watchlist.

    Returns items ordered by when they were added (oldest first).
    """
    items = await list_items_uc.execute(watchlist_id)
    return WatchlistItemListResponse(
        items=[watchlist_item_to_response(item) for item in items],
        count=len(items),
    )


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add page to watchlist",
    description="Add a page to a watchlist.",
    responses={
        201: {"description": "Page added successfully"},
        404: {"model": ErrorResponse, "description": "Watchlist not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def add_page_to_watchlist(
    watchlist_id: str,
    request: WatchlistItemRequest,
    add_page_uc: AddPageToWatchlistUC,
) -> WatchlistItemResponse:
    """Add a page to a watchlist.

    If the page is already in the watchlist, returns the existing item.
    """
    item = await add_page_uc.execute(
        watchlist_id=watchlist_id,
        page_id=request.page_id,
    )
    return watchlist_item_to_response(item)


@router.delete(
    "/{watchlist_id}/items/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove page from watchlist",
    description="Remove a page from a watchlist.",
    responses={
        204: {"description": "Page removed successfully"},
        404: {"model": ErrorResponse, "description": "Watchlist not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def remove_page_from_watchlist(
    watchlist_id: str,
    page_id: str,
    remove_page_uc: RemovePageFromWatchlistUC,
) -> Response:
    """Remove a page from a watchlist.

    Silently succeeds if the page is not in the watchlist.
    """
    await remove_page_uc.execute(
        watchlist_id=watchlist_id,
        page_id=page_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{watchlist_id}/scan_now",
    response_model=RescoreWatchlistResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger rescore for watchlist",
    description="Dispatch compute_shop_score tasks for all pages in the watchlist.",
    responses={
        202: {"description": "Rescoring tasks dispatched successfully"},
        404: {"model": ErrorResponse, "description": "Watchlist not found"},
        500: {"model": ErrorResponse, "description": "Task dispatch error"},
    },
)
async def scan_now(
    watchlist_id: str,
    rescore_uc: RescoreWatchlistUC,
) -> RescoreWatchlistResponse:
    """Trigger an immediate rescore for all pages in a watchlist.

    Dispatches compute_shop_score background tasks for each page in the
    watchlist. The actual scoring happens asynchronously.

    Returns the number of tasks dispatched (one per page in the watchlist).
    """
    tasks_dispatched = await rescore_uc.execute(watchlist_id=watchlist_id)

    return RescoreWatchlistResponse(
        watchlist_id=watchlist_id,
        tasks_dispatched=tasks_dispatched,
        message=f"Dispatched {tasks_dispatched} scoring tasks for watchlist",
    )


@router.get(
    "/by-page/{page_id}",
    response_model=PageWatchlistsResponse,
    summary="Get watchlists containing a page",
    description="Find all watchlists that contain a specific page.",
    responses={
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_page_watchlists(
    page_id: str,
    get_page_watchlists_uc: GetPageWatchlistsUC,
) -> PageWatchlistsResponse:
    """Get all watchlists that contain a specific page.

    Useful for showing watchlist badges on page detail views.
    """
    watchlists = await get_page_watchlists_uc.execute(page_id)
    return PageWatchlistsResponse(
        page_id=page_id,
        watchlists=[watchlist_to_response(w) for w in watchlists],
        count=len(watchlists),
    )

"""Keyword search endpoints."""

from fastapi import APIRouter, status

from src.app.api.schemas.keywords import KeywordSearchRequest, KeywordSearchResponse
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import SearchAdsUseCase
from src.app.core.domain.value_objects import Country, Language

router = APIRouter(prefix="/keywords", tags=["Keywords"])


@router.post(
    "/search",
    response_model=KeywordSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search ads by keyword",
    description="Search for Meta ads using a keyword and return discovered pages.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        502: {"model": ErrorResponse, "description": "External service error"},
    },
)
async def search_by_keyword(
    request: KeywordSearchRequest,
    use_case: SearchAdsUseCase,
) -> KeywordSearchResponse:
    """Search for ads by keyword.

    Calls the Meta Ads API to find ads matching the keyword,
    groups them by page, and returns aggregated results.
    """
    # Convert to domain objects
    country = Country(request.country)
    language = Language(request.language) if request.language else None

    # Execute use case
    result = await use_case.execute(
        keyword=request.keyword,
        country=country,
        language=language,
        limit=request.limit,
    )

    return KeywordSearchResponse(
        scan_id=str(result.scan_id),
        keyword=request.keyword,
        country=request.country,
        ads_found=result.count_ads,
        pages_found=len(result.pages),
        new_pages=result.new_pages,
    )

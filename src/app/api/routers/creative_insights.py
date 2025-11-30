"""Creative Insights API Endpoints.

Provides endpoints for accessing AI-powered marketing creative analysis:
- Page-level creative insights
- Individual ad analysis
- Admin endpoint to trigger creative analysis
"""

from fastapi import APIRouter, Depends, status

from src.app.api.schemas.creative_insights import (
    CreativeAnalysisResponse,
    PageCreativeInsightsResponse,
    AnalyzeCreativesResponse,
)
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import (
    PageRepo,
    BuildPageCreativeInsightsUC,
    CreativeAnalysisRepo,
    TaskDispatcher,
    get_admin_auth,
)
from src.app.core.domain.entities.creative_analysis import (
    CreativeAnalysis,
    PageCreativeInsights,
)
from src.app.core.domain.errors import EntityNotFoundError


router = APIRouter(tags=["Creative Insights"])


def _analysis_to_response(analysis: CreativeAnalysis) -> CreativeAnalysisResponse:
    """Convert domain CreativeAnalysis to API response."""
    return CreativeAnalysisResponse(
        id=analysis.id,
        ad_id=analysis.ad_id,
        creative_score=analysis.creative_score,
        style_tags=list(analysis.style_tags),
        angle_tags=list(analysis.angle_tags),
        tone_tags=list(analysis.tone_tags),
        sentiment=analysis.sentiment,
        analysis_version=analysis.analysis_version,
        created_at=analysis.created_at,
    )


def _insights_to_response(insights: PageCreativeInsights) -> PageCreativeInsightsResponse:
    """Convert domain PageCreativeInsights to API response."""
    return PageCreativeInsightsResponse(
        page_id=insights.page_id,
        avg_score=round(insights.avg_score, 1),
        best_score=round(insights.best_score, 1),
        quality_tier=insights.quality_tier,
        top_creatives=[
            _analysis_to_response(a) for a in insights.top_creatives
        ],
        total_analyzed=insights.total_analyzed,
        computed_at=insights.computed_at,
    )


@router.get(
    "/pages/{page_id}/creatives/insights",
    response_model=PageCreativeInsightsResponse,
    summary="Get page creative insights",
    description="Get aggregated creative analysis insights for all ads of a page.",
    responses={
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_page_creative_insights(
    page_id: str,
    use_case: BuildPageCreativeInsightsUC,
) -> PageCreativeInsightsResponse:
    """Get creative insights for a page.

    Returns aggregated insights including:
    - Average and best creative scores
    - Quality tier assessment
    - Top-scoring creatives with tags and sentiment

    If ads have not been analyzed yet, this will analyze them on-the-fly.
    """
    result = await use_case.execute(page_id=page_id, top_n=5)
    return _insights_to_response(result.insights)


@router.get(
    "/ads/{ad_id}/analysis",
    response_model=CreativeAnalysisResponse,
    summary="Get ad creative analysis",
    description="Get the creative analysis for a specific ad.",
    responses={
        404: {"model": ErrorResponse, "description": "Analysis not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_ad_analysis(
    ad_id: str,
    analysis_repo: CreativeAnalysisRepo,
) -> CreativeAnalysisResponse:
    """Get creative analysis for a specific ad.

    Returns the analysis if it exists, otherwise 404.
    To trigger analysis for ads without existing analysis,
    use the page-level insights endpoint or admin trigger.
    """
    analysis = await analysis_repo.get_by_ad_id(ad_id)
    if analysis is None:
        raise EntityNotFoundError("CreativeAnalysis", ad_id)
    return _analysis_to_response(analysis)


@router.post(
    "/admin/pages/{page_id}/creatives/analyze",
    response_model=AnalyzeCreativesResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger creative analysis (Admin)",
    description="Dispatch a background task to analyze all creatives for a page.",
    dependencies=[Depends(get_admin_auth)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def trigger_creative_analysis(
    page_id: str,
    page_repo: PageRepo,
    task_dispatcher: TaskDispatcher,
) -> AnalyzeCreativesResponse:
    """Trigger creative analysis for a page (Admin only).

    This dispatches a Celery task to analyze all ad creatives
    for the specified page in the background.

    Requires X-Admin-Api-Key header for authentication.
    """
    # Verify page exists
    page = await page_repo.get(page_id)
    if page is None:
        raise EntityNotFoundError("Page", page_id)

    # Dispatch Celery task
    try:
        task_result = task_dispatcher.dispatch_analyze_creatives_for_page(page_id)
        return AnalyzeCreativesResponse(
            status="dispatched",
            message=f"Creative analysis task dispatched for page {page_id}",
            task_id=task_result.id if hasattr(task_result, "id") else str(task_result),
        )
    except Exception as exc:
        return AnalyzeCreativesResponse(
            status="error",
            message=f"Failed to dispatch task: {str(exc)}",
            task_id=None,
        )

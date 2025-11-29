"""Health check endpoint."""

from fastapi import APIRouter

from src.app.api.schemas.common import HealthResponse
from src.app.api.dependencies import Settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the service is running and healthy.",
)
async def health_check(settings: Settings) -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="ok",
        version=settings.version,
        environment=settings.environment,
    )

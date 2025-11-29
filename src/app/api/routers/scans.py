"""Scan endpoints."""

from fastapi import APIRouter

from src.app.api.schemas.scans import ScanResponse, ScanResultResponse
from src.app.api.schemas.common import ErrorResponse
from src.app.api.dependencies import ScanRepo
from src.app.core.domain.entities.scan import Scan
from src.app.core.domain.errors import EntityNotFoundError, InvalidScanIdError
from src.app.core.domain.value_objects import ScanId

router = APIRouter(prefix="/scans", tags=["Scans"])


def _scan_to_response(scan: Scan) -> ScanResponse:
    """Convert domain Scan to API response."""
    result_response = None
    if scan.result:
        result_response = ScanResultResponse(
            ads_found=scan.result.ads_found,
            new_ads=scan.result.new_ads,
            products_found=scan.result.products_found,
            is_shopify=scan.result.is_shopify,
            errors=scan.result.errors,
            warnings=scan.result.warnings,
        )

    return ScanResponse(
        id=str(scan.id),
        page_id=scan.page_id,
        scan_type=scan.scan_type.value,
        status=scan.status.value,
        result=result_response,
        priority=scan.priority,
        retry_count=scan.retry_count,
        error_message=scan.error_message,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        duration_seconds=scan.get_duration_seconds(),
        created_at=scan.created_at,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    summary="Get scan details",
    description="Get the status and results of a specific scan operation.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid scan ID format"},
        404: {"model": ErrorResponse, "description": "Scan not found"},
        500: {"model": ErrorResponse, "description": "Database error"},
    },
)
async def get_scan(
    scan_id: str,
    scan_repo: ScanRepo,
) -> ScanResponse:
    """Get details of a specific scan by ID.

    Returns the current status, progress, and results (if completed)
    of the scan operation.
    """
    # Validate and convert scan_id
    try:
        validated_scan_id = ScanId(scan_id)
    except Exception:
        raise InvalidScanIdError(scan_id)

    scan = await scan_repo.get_scan(validated_scan_id)

    if scan is None:
        raise EntityNotFoundError("Scan", scan_id)

    return _scan_to_response(scan)

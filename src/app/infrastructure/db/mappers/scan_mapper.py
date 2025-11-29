"""Scan Mapper.

Bidirectional mapping between Scan domain entity and ScanModel ORM.
Pure functions, no I/O, no session dependency.
"""

from typing import Any, cast
from uuid import UUID

from src.app.core.domain.entities.scan import Scan, ScanResult, ScanStatus, ScanType
from src.app.core.domain.value_objects import ScanId
from src.app.infrastructure.db.models.scan_model import ScanModel


def _scan_type_to_string(scan_type: ScanType) -> str:
    """Convert ScanType enum to string."""
    return scan_type.value


def _string_to_scan_type(value: str) -> ScanType:
    """Convert string to ScanType enum."""
    for scan_type in ScanType:
        if scan_type.value == value:
            return scan_type
    return ScanType.FULL


def _scan_status_to_string(status: ScanStatus) -> str:
    """Convert ScanStatus enum to string."""
    return status.value


def _string_to_scan_status(value: str) -> ScanStatus:
    """Convert string to ScanStatus enum."""
    for status in ScanStatus:
        if status.value == value:
            return status
    return ScanStatus.PENDING


def _result_to_dict(result: ScanResult) -> dict[str, object]:
    """Convert ScanResult to dictionary for JSONB storage."""
    return {
        "ads_found": result.ads_found,
        "new_ads": result.new_ads,
        "products_found": result.products_found,
        "is_shopify": result.is_shopify,
        "errors": result.errors,
        "warnings": result.warnings,
        "metadata": result.metadata,
    }


def _dict_to_result(data: dict[str, Any]) -> ScanResult:
    """Convert dictionary from JSONB to ScanResult."""
    ads_found = data.get("ads_found", 0)
    new_ads = data.get("new_ads", 0)
    products_found = data.get("products_found", 0)
    is_shopify = data.get("is_shopify")
    errors = data.get("errors", [])
    warnings = data.get("warnings", [])
    metadata = data.get("metadata", {})

    return ScanResult(
        ads_found=int(ads_found) if ads_found is not None else 0,
        new_ads=int(new_ads) if new_ads is not None else 0,
        products_found=int(products_found) if products_found is not None else 0,
        is_shopify=cast(bool | None, is_shopify),
        errors=cast(list[str], errors) if errors else [],
        warnings=cast(list[str], warnings) if warnings else [],
        metadata=cast(dict[str, Any], metadata) if metadata else {},
    )


def to_domain(model: ScanModel) -> Scan:
    """Convert ScanModel ORM instance to Scan domain entity.

    Args:
        model: The ScanModel ORM instance.

    Returns:
        The corresponding Scan domain entity.
    """
    return Scan(
        id=ScanId(value=str(model.id)),
        page_id=str(model.page_id),
        scan_type=_string_to_scan_type(model.scan_type),
        status=_string_to_scan_status(model.status),
        result=_dict_to_result(model.result) if model.result else None,
        priority=model.priority,
        retry_count=model.retry_count,
        max_retries=model.max_retries,
        error_message=model.error_message,
        started_at=model.started_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: Scan) -> ScanModel:
    """Convert Scan domain entity to ScanModel ORM instance.

    Args:
        entity: The Scan domain entity.

    Returns:
        The corresponding ScanModel ORM instance.
    """
    return ScanModel(
        id=UUID(entity.id.value),
        page_id=UUID(entity.page_id),
        scan_type=_scan_type_to_string(entity.scan_type),
        status=_scan_status_to_string(entity.status),
        result=_result_to_dict(entity.result) if entity.result else None,
        priority=entity.priority,
        retry_count=entity.retry_count,
        max_retries=entity.max_retries,
        error_message=entity.error_message,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )

"""KeywordRun Mapper.

Bidirectional mapping between KeywordRun domain entity and KeywordRunModel ORM.
Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.keyword_run import (
    KeywordRun,
    KeywordRunResult,
    KeywordRunStatus,
)
from src.app.core.domain.value_objects import Country, ScanId
from src.app.infrastructure.db.models.keyword_run_model import KeywordRunModel


def _status_to_string(status: KeywordRunStatus) -> str:
    """Convert KeywordRunStatus enum to string."""
    return status.value


def _string_to_status(value: str) -> KeywordRunStatus:
    """Convert string to KeywordRunStatus enum."""
    for status in KeywordRunStatus:
        if status.value == value:
            return status
    return KeywordRunStatus.PENDING


def _result_to_dict(result: KeywordRunResult) -> dict[str, object]:
    """Convert KeywordRunResult to dictionary for JSONB storage."""
    return {
        "total_ads_found": result.total_ads_found,
        "unique_pages_found": result.unique_pages_found,
        "new_pages_found": result.new_pages_found,
        "ads_processed": result.ads_processed,
        "errors": result.errors,
    }


def _dict_to_result(data: dict[str, object]) -> KeywordRunResult:
    """Convert dictionary from JSONB to KeywordRunResult."""
    return KeywordRunResult(
        total_ads_found=int(data.get("total_ads_found", 0)),
        unique_pages_found=int(data.get("unique_pages_found", 0)),
        new_pages_found=int(data.get("new_pages_found", 0)),
        ads_processed=int(data.get("ads_processed", 0)),
        errors=list(data.get("errors", [])),
    )


def to_domain(model: KeywordRunModel) -> KeywordRun:
    """Convert KeywordRunModel ORM instance to KeywordRun domain entity.

    Args:
        model: The KeywordRunModel ORM instance.

    Returns:
        The corresponding KeywordRun domain entity.
    """
    return KeywordRun(
        id=ScanId(value=str(model.id)),
        keyword=model.keyword,
        country=Country(code=model.country),
        status=_string_to_status(model.status),
        result=_dict_to_result(model.result) if model.result else None,
        page_limit=model.page_limit,
        pages_fetched=model.pages_fetched,
        priority=model.priority,
        retry_count=model.retry_count,
        max_retries=model.max_retries,
        error_message=model.error_message,
        started_at=model.started_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: KeywordRun) -> KeywordRunModel:
    """Convert KeywordRun domain entity to KeywordRunModel ORM instance.

    Args:
        entity: The KeywordRun domain entity.

    Returns:
        The corresponding KeywordRunModel ORM instance.
    """
    return KeywordRunModel(
        id=UUID(entity.id.value),
        keyword=entity.keyword,
        country=entity.country.code,
        language=None,  # Domain entity doesn't track language separately
        status=_status_to_string(entity.status),
        result=_result_to_dict(entity.result) if entity.result else None,
        page_limit=entity.page_limit,
        pages_fetched=entity.pages_fetched,
        priority=entity.priority,
        retry_count=entity.retry_count,
        max_retries=entity.max_retries,
        error_message=entity.error_message,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )

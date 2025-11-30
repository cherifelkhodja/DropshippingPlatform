"""Creative Analysis Mapper.

Bidirectional mapping between CreativeAnalysis domain entity and
CreativeAnalysisModel ORM. Pure functions, no I/O, no session dependency.
"""

from typing import cast
from uuid import UUID

from src.app.core.domain.entities.creative_analysis import (
    CreativeAnalysis,
    SentimentType,
)
from src.app.infrastructure.db.models.creative_analysis_model import (
    CreativeAnalysisModel,
)


def _ensure_string_list(value: list | None) -> list[str]:
    """Ensure value is a list of strings.

    Args:
        value: The value to convert (may be None or list of any).

    Returns:
        A list of strings.
    """
    if value is None:
        return []
    return [str(v) for v in value]


def _ensure_sentiment(value: str) -> SentimentType:
    """Ensure value is a valid sentiment type.

    Args:
        value: The sentiment string.

    Returns:
        A valid SentimentType literal.
    """
    if value in ("positive", "neutral", "negative"):
        return cast(SentimentType, value)
    return "neutral"


def to_domain(model: CreativeAnalysisModel) -> CreativeAnalysis:
    """Convert CreativeAnalysisModel ORM instance to domain entity.

    Args:
        model: The CreativeAnalysisModel ORM instance.

    Returns:
        The corresponding CreativeAnalysis domain entity.
    """
    return CreativeAnalysis(
        id=str(model.id),
        ad_id=str(model.ad_id),
        creative_score=model.creative_score,
        style_tags=_ensure_string_list(model.style_tags),
        angle_tags=_ensure_string_list(model.angle_tags),
        tone_tags=_ensure_string_list(model.tone_tags),
        sentiment=_ensure_sentiment(model.sentiment),
        analysis_version=model.analysis_version,
        created_at=model.created_at,
    )


def to_model(entity: CreativeAnalysis) -> CreativeAnalysisModel:
    """Convert CreativeAnalysis domain entity to ORM instance.

    Args:
        entity: The CreativeAnalysis domain entity.

    Returns:
        The corresponding CreativeAnalysisModel ORM instance.
    """
    return CreativeAnalysisModel(
        id=UUID(entity.id),
        ad_id=UUID(entity.ad_id),
        creative_score=entity.creative_score,
        style_tags=list(entity.style_tags),
        angle_tags=list(entity.angle_tags),
        tone_tags=list(entity.tone_tags),
        sentiment=entity.sentiment,
        analysis_version=entity.analysis_version,
        created_at=entity.created_at,
    )

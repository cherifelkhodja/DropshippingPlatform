"""Alert Mapper.

Bidirectional mapping between Alert domain entity and AlertModel ORM.
Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.alert import Alert
from src.app.infrastructure.db.models.alert_model import AlertModel


def alert_to_domain(model: AlertModel) -> Alert:
    """Convert AlertModel ORM instance to Alert domain entity.

    Args:
        model: The AlertModel ORM instance.

    Returns:
        The corresponding Alert domain entity.
    """
    return Alert(
        id=str(model.id),
        page_id=str(model.page_id),
        type=model.type,
        message=model.message,
        severity=model.severity,
        old_score=model.old_score,
        new_score=model.new_score,
        old_tier=model.old_tier,
        new_tier=model.new_tier,
        created_at=model.created_at,
    )


def alert_to_model(entity: Alert) -> AlertModel:
    """Convert Alert domain entity to AlertModel ORM instance.

    Args:
        entity: The Alert domain entity.

    Returns:
        The corresponding AlertModel ORM instance.
    """
    return AlertModel(
        id=UUID(entity.id),
        page_id=UUID(entity.page_id),
        type=entity.type,
        message=entity.message,
        severity=entity.severity,
        old_score=entity.old_score,
        new_score=entity.new_score,
        old_tier=entity.old_tier,
        new_tier=entity.new_tier,
        created_at=entity.created_at,
    )

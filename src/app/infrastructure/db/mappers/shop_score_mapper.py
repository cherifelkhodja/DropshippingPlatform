"""Shop Score Mapper.

Bidirectional mapping between ShopScore domain entity and ShopScoreModel ORM.
Pure functions, no I/O, no session dependency.
"""

from typing import Any
from uuid import UUID

from src.app.core.domain.entities.shop_score import ShopScore
from src.app.infrastructure.db.models.shop_score_model import ShopScoreModel


def to_domain(model: ShopScoreModel) -> ShopScore:
    """Convert ShopScoreModel ORM instance to ShopScore domain entity.

    Args:
        model: The ShopScoreModel ORM instance.

    Returns:
        The corresponding ShopScore domain entity.
    """
    # Ensure components is a dict[str, float]
    components: dict[str, float] = {}
    if model.components:
        for key, value in model.components.items():
            if isinstance(value, (int, float)):
                components[str(key)] = float(value)

    return ShopScore(
        id=str(model.id),
        page_id=str(model.page_id),
        score=model.score,
        components=components,
        created_at=model.created_at,
    )


def to_model(entity: ShopScore) -> ShopScoreModel:
    """Convert ShopScore domain entity to ShopScoreModel ORM instance.

    Args:
        entity: The ShopScore domain entity.

    Returns:
        The corresponding ShopScoreModel ORM instance.
    """
    # Convert components to JSON-serializable dict
    components: dict[str, Any] = {
        str(k): float(v) for k, v in entity.components.items()
    }

    return ShopScoreModel(
        id=UUID(entity.id),
        page_id=UUID(entity.page_id),
        score=entity.score,
        components=components,
        created_at=entity.created_at,
    )

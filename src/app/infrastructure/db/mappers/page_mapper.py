"""Page Mapper.

Bidirectional mapping between Page domain entity and PageModel ORM.
Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.page import Page
from src.app.core.domain.value_objects import (
    Category,
    Country,
    Currency,
    Language,
    PageState,
    ProductCount,
    Url,
)
from src.app.infrastructure.db.models.page_model import PageModel


def to_domain(model: PageModel) -> Page:
    """Convert PageModel ORM instance to Page domain entity.

    Args:
        model: The PageModel ORM instance.

    Returns:
        The corresponding Page domain entity.
    """
    return Page(
        id=str(model.id),
        url=Url(value=model.url),
        domain=model.domain,
        state=PageState.from_string(model.state),
        country=Country(code=model.country) if model.country else None,
        language=Language(code=model.language) if model.language else None,
        currency=Currency(code=model.currency) if model.currency else None,
        category=Category(value=model.category) if model.category else None,
        product_count=ProductCount(value=model.product_count),
        is_shopify=model.is_shopify,
        shopify_profile_id=model.shopify_profile_id,
        active_ads_count=model.active_ads_count,
        total_ads_count=model.total_ads_count,
        score=model.score,
        first_seen_at=model.first_seen_at,
        last_scanned_at=model.last_scanned_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def to_model(entity: Page) -> PageModel:
    """Convert Page domain entity to PageModel ORM instance.

    Args:
        entity: The Page domain entity.

    Returns:
        The corresponding PageModel ORM instance.
    """
    return PageModel(
        id=UUID(entity.id),
        url=entity.url.value,
        domain=entity.domain,
        state=str(entity.state),
        country=entity.country.code if entity.country else None,
        language=entity.language.code if entity.language else None,
        currency=entity.currency.code if entity.currency else None,
        category=entity.category.value if entity.category else None,
        product_count=entity.product_count.value,
        is_shopify=entity.is_shopify,
        shopify_profile_id=entity.shopify_profile_id,
        active_ads_count=entity.active_ads_count,
        total_ads_count=entity.total_ads_count,
        score=entity.score,
        first_seen_at=entity.first_seen_at,
        last_scanned_at=entity.last_scanned_at,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )

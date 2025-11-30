"""Product Mapper.

Bidirectional mapping between Product domain entity and ProductModel ORM.
Pure functions, no I/O, no session dependency.
"""

from uuid import UUID

from src.app.core.domain.entities.product import Product
from src.app.infrastructure.db.models.product_model import ProductModel


def to_domain(model: ProductModel) -> Product:
    """Convert ProductModel ORM instance to Product domain entity.

    Args:
        model: The ProductModel ORM instance.

    Returns:
        The corresponding Product domain entity.
    """
    return Product(
        id=str(model.id),
        page_id=str(model.page_id),
        handle=model.handle,
        title=model.title,
        url=model.url,
        price_min=model.price_min,
        price_max=model.price_max,
        currency=model.currency,
        available=model.available,
        tags=list(model.tags) if model.tags else [],
        vendor=model.vendor,
        image_url=model.image_url,
        product_type=model.product_type,
        created_at=model.created_at,
        updated_at=model.updated_at,
        raw_data=dict(model.raw_data) if model.raw_data else None,
    )


def to_model(entity: Product) -> ProductModel:
    """Convert Product domain entity to ProductModel ORM instance.

    Args:
        entity: The Product domain entity.

    Returns:
        The corresponding ProductModel ORM instance.
    """
    return ProductModel(
        id=UUID(entity.id),
        page_id=UUID(entity.page_id),
        handle=entity.handle,
        title=entity.title,
        url=entity.url,
        price_min=entity.price_min,
        price_max=entity.price_max,
        currency=entity.currency,
        available=entity.available,
        tags=entity.tags,
        vendor=entity.vendor,
        image_url=entity.image_url,
        product_type=entity.product_type,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
        raw_data=entity.raw_data,
    )

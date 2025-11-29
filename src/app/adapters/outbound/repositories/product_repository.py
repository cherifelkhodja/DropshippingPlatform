"""PostgreSQL Product Repository.

Implements ProductRepository port with SQLAlchemy async operations.
"""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.product import Product
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import product_mapper
from src.app.infrastructure.db.models import ProductModel


class PostgresProductRepository:
    """SQLAlchemy implementation of ProductRepository port.

    Handles Product entity persistence with PostgreSQL.
    Uses upsert (INSERT ... ON CONFLICT) for efficient catalog sync.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def upsert_many(self, products: Sequence[Product]) -> None:
        """Upsert multiple products in batch.

        Uses PostgreSQL INSERT ... ON CONFLICT DO UPDATE to efficiently
        update existing products or insert new ones based on (page_id, handle).

        Args:
            products: Sequence of Product entities to upsert.

        Raises:
            RepositoryError: On database errors.
        """
        if not products:
            return

        try:
            for product in products:
                # Prepare values for upsert
                values = {
                    "id": UUID(product.id),
                    "page_id": UUID(product.page_id),
                    "handle": product.handle,
                    "title": product.title,
                    "url": product.url,
                    "price_min": product.price_min,
                    "price_max": product.price_max,
                    "currency": product.currency,
                    "available": product.available,
                    "tags": product.tags,
                    "vendor": product.vendor,
                    "image_url": product.image_url,
                    "product_type": product.product_type,
                    "created_at": product.created_at,
                    "updated_at": datetime.utcnow(),
                    "raw_data": product.raw_data,
                }

                # Create upsert statement
                stmt = insert(ProductModel).values(**values)
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_products_page_id_handle",
                    set_={
                        "title": stmt.excluded.title,
                        "url": stmt.excluded.url,
                        "price_min": stmt.excluded.price_min,
                        "price_max": stmt.excluded.price_max,
                        "currency": stmt.excluded.currency,
                        "available": stmt.excluded.available,
                        "tags": stmt.excluded.tags,
                        "vendor": stmt.excluded.vendor,
                        "image_url": stmt.excluded.image_url,
                        "product_type": stmt.excluded.product_type,
                        "updated_at": stmt.excluded.updated_at,
                        "raw_data": stmt.excluded.raw_data,
                    },
                )
                await self._session.execute(stmt)

            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="upsert_many_products",
                reason=f"Failed to upsert products: {exc}",
            ) from exc

    async def list_by_page(
        self, page_id: str, limit: int = 50, offset: int = 0
    ) -> list[Product]:
        """List all products for a specific page (store).

        Returns products ordered by title ascending.

        Args:
            page_id: The page identifier to filter by.
            limit: Maximum number of products to return.
            offset: Number of products to skip.

        Returns:
            List of Product entities for the page.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(ProductModel)
                .where(ProductModel.page_id == UUID(page_id))
                .order_by(ProductModel.title.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [product_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_products_by_page",
                reason=f"Failed to list products: {exc}",
            ) from exc

    async def get_by_id(self, product_id: str) -> Product | None:
        """Retrieve a product by its ID.

        Args:
            product_id: The unique product identifier.

        Returns:
            The Product entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(ProductModel).where(ProductModel.id == UUID(product_id))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return product_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_product",
                reason=f"Failed to get product: {exc}",
            ) from exc

    async def delete_by_page(self, page_id: str) -> int:
        """Delete all products for a page.

        Used for full catalog resync operations.

        Args:
            page_id: The page identifier whose products to delete.

        Returns:
            Number of products deleted.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = delete(ProductModel).where(
                ProductModel.page_id == UUID(page_id)
            )
            result = await self._session.execute(stmt)
            await self._session.commit()

            return result.rowcount
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="delete_products_by_page",
                reason=f"Failed to delete products: {exc}",
            ) from exc

    async def count_by_page(self, page_id: str) -> int:
        """Count products for a specific page.

        Args:
            page_id: The page identifier to count products for.

        Returns:
            Total count of products for the page.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(func.count()).where(
                ProductModel.page_id == UUID(page_id)
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="count_products_by_page",
                reason=f"Failed to count products: {exc}",
            ) from exc

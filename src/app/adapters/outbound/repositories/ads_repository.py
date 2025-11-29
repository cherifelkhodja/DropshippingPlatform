"""PostgreSQL Ads Repository.

Implements AdsRepository port with SQLAlchemy async operations.
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.ad import Ad
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import ad_mapper
from src.app.infrastructure.db.models import AdModel


class PostgresAdsRepository:
    """SQLAlchemy implementation of AdsRepository port.

    Handles Ad entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save_many(self, ads: Sequence[Ad]) -> None:
        """Save multiple ads in batch.

        Args:
            ads: Sequence of Ad entities to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            for ad in ads:
                model = ad_mapper.to_model(ad)
                merged = await self._session.merge(model)
                self._session.add(merged)

            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_many_ads",
                reason=f"Failed to save ads: {exc}",
            ) from exc

    async def list_by_page(self, page_id: str) -> list[Ad]:
        """List all ads for a specific page.

        Args:
            page_id: The page identifier to filter by.

        Returns:
            List of Ad entities for the page.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(AdModel)
                .where(AdModel.page_id == UUID(page_id))
                .order_by(AdModel.created_at.desc())
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [ad_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_ads_by_page",
                reason=f"Failed to list ads: {exc}",
            ) from exc

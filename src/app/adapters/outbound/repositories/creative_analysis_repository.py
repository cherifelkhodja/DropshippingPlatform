"""PostgreSQL Creative Analysis Repository.

Implements CreativeAnalysisRepository port with SQLAlchemy async operations.
"""

from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.creative_analysis import CreativeAnalysis
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import creative_analysis_mapper
from src.app.infrastructure.db.models.creative_analysis_model import (
    CreativeAnalysisModel,
)
from src.app.infrastructure.db.models.ad_model import AdModel


class PostgresCreativeAnalysisRepository:
    """SQLAlchemy implementation of CreativeAnalysisRepository port.

    Handles CreativeAnalysis entity persistence with PostgreSQL.
    Supports one analysis per ad (upsert pattern via merge).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def get_by_ad_id(self, ad_id: str) -> CreativeAnalysis | None:
        """Retrieve a creative analysis by its associated ad ID.

        Args:
            ad_id: The unique ad identifier.

        Returns:
            The CreativeAnalysis entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(CreativeAnalysisModel).where(
                CreativeAnalysisModel.ad_id == UUID(ad_id)
            )
            result = await self._session.execute(stmt)
            model = result.scalars().first()

            if model is None:
                return None

            return creative_analysis_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_creative_analysis_by_ad_id",
                reason=f"Failed to get analysis for ad {ad_id}: {exc}",
            ) from exc

    async def save(self, analysis: CreativeAnalysis) -> None:
        """Save a new creative analysis (upsert pattern).

        If an analysis already exists for the ad_id, it will be replaced.

        Args:
            analysis: The CreativeAnalysis entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = creative_analysis_mapper.to_model(analysis)
            merged = await self._session.merge(model)
            self._session.add(merged)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_creative_analysis",
                reason=f"Failed to save analysis: {exc}",
            ) from exc

    async def list_for_page(self, page_id: str) -> Sequence[CreativeAnalysis]:
        """List all creative analyses for ads belonging to a page.

        Returns analyses ordered by creative_score descending (best first).

        Args:
            page_id: The page identifier to filter ads by.

        Returns:
            Sequence of CreativeAnalysis entities for the page's ads.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Join with ads to filter by page_id
            stmt = (
                select(CreativeAnalysisModel)
                .join(AdModel, CreativeAnalysisModel.ad_id == AdModel.id)
                .where(AdModel.page_id == UUID(page_id))
                .order_by(CreativeAnalysisModel.creative_score.desc())
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [creative_analysis_mapper.to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_creative_analyses_for_page",
                reason=f"Failed to list analyses for page {page_id}: {exc}",
            ) from exc

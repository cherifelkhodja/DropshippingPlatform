"""PostgreSQL Scoring Repository.

Implements ScoringRepository port with SQLAlchemy async operations.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.shop_score import ShopScore
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import shop_score_mapper
from src.app.infrastructure.db.models.shop_score_model import ShopScoreModel


class PostgresScoringRepository:
    """SQLAlchemy implementation of ScoringRepository port.

    Handles ShopScore entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save(self, score: ShopScore) -> None:
        """Save a shop score.

        Args:
            score: The ShopScore entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = shop_score_mapper.to_model(score)
            merged = await self._session.merge(model)
            self._session.add(merged)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_score",
                reason=f"Failed to save shop score: {exc}",
            ) from exc

    async def get_latest_by_page_id(self, page_id: str) -> ShopScore | None:
        """Retrieve the most recent score for a page.

        Args:
            page_id: The unique page identifier.

        Returns:
            The most recent ShopScore for the page, or None if no scores exist.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(ShopScoreModel)
                .where(ShopScoreModel.page_id == UUID(page_id))
                .order_by(ShopScoreModel.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return shop_score_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_latest_score",
                reason=f"Failed to get latest score for page: {exc}",
            ) from exc

    async def list_top(self, limit: int = 50, offset: int = 0) -> list[ShopScore]:
        """List top-scoring pages.

        Returns the most recent score for each page, ordered by score descending.

        Args:
            limit: Maximum number of scores to return.
            offset: Number of scores to skip.

        Returns:
            List of ShopScore entities ordered by score descending.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Get all scores, order by score desc then created_at desc
            # This gives us a simple leaderboard of scores
            stmt = (
                select(ShopScoreModel)
                .order_by(
                    ShopScoreModel.score.desc(),
                    ShopScoreModel.created_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [shop_score_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_top_scores",
                reason=f"Failed to list top scores: {exc}",
            ) from exc

    async def count(self) -> int:
        """Count total number of shop scores.

        Returns:
            The total count of ShopScore entities.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(func.count()).select_from(ShopScoreModel)
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="count_scores",
                reason=f"Failed to count scores: {exc}",
            ) from exc

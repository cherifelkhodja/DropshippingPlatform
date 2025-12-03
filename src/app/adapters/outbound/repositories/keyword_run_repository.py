"""PostgreSQL KeywordRun Repository.

Implements KeywordRunRepository port with SQLAlchemy async operations.
"""

import logging
import traceback

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.keyword_run import KeywordRun
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import keyword_run_mapper
from src.app.infrastructure.db.models import KeywordRunModel

logger = logging.getLogger(__name__)


class PostgresKeywordRunRepository:
    """SQLAlchemy implementation of KeywordRunRepository port.

    Handles KeywordRun entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save(self, run: KeywordRun) -> None:
        """Save or update a keyword run.

        Args:
            run: The KeywordRun entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            logger.debug("Saving KeywordRun: %s", run.id)
            model = keyword_run_mapper.to_model(run)
            # merge() returns an attached object, add() is not needed
            await self._session.merge(model)
            await self._session.commit()
            logger.debug("KeywordRun saved successfully")
        except Exception as exc:
            logger.error(
                "Failed to save keyword run: %s\n%s",
                str(exc),
                traceback.format_exc(),
            )
            await self._session.rollback()
            raise RepositoryError(
                operation="save_keyword_run",
                reason=f"Failed to save keyword run: {exc}",
            ) from exc

    async def list_recent(self, limit: int = 50) -> list[KeywordRun]:
        """List recent keyword runs.

        Args:
            limit: Maximum number of runs to return.

        Returns:
            List of recent KeywordRun entities, ordered by creation date desc.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(KeywordRunModel)
                .order_by(KeywordRunModel.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [keyword_run_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_recent_keyword_runs",
                reason=f"Failed to list keyword runs: {exc}",
            ) from exc

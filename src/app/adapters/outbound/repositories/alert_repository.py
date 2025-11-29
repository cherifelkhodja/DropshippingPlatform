"""PostgreSQL Alert Repository.

Implements AlertRepository port with SQLAlchemy async operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.alert import Alert
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import alert_mapper
from src.app.infrastructure.db.models.alert_model import AlertModel


class PostgresAlertRepository:
    """SQLAlchemy implementation of AlertRepository port.

    Handles Alert entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save(self, alert: Alert) -> Alert:
        """Save a new alert.

        Args:
            alert: The Alert entity to save.

        Returns:
            The saved Alert entity.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = alert_mapper.alert_to_model(alert)
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return alert_mapper.alert_to_domain(model)
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_alert",
                reason=f"Failed to save alert: {exc}",
            ) from exc

    async def list_by_page(
        self, page_id: str, limit: int = 50, offset: int = 0
    ) -> list[Alert]:
        """List all alerts for a specific page.

        Returns alerts ordered by created_at descending (newest first).

        Args:
            page_id: The page identifier to filter by.
            limit: Maximum number of alerts to return.
            offset: Number of alerts to skip.

        Returns:
            List of Alert entities for the page.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(AlertModel)
                .where(AlertModel.page_id == UUID(page_id))
                .order_by(AlertModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [alert_mapper.alert_to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_alerts_by_page",
                reason=f"Failed to list alerts for page: {exc}",
            ) from exc

    async def list_recent(self, limit: int = 100) -> list[Alert]:
        """List recent alerts across all pages.

        Returns alerts ordered by created_at descending (newest first).

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            List of recent Alert entities.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(AlertModel)
                .order_by(AlertModel.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [alert_mapper.alert_to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_recent_alerts",
                reason=f"Failed to list recent alerts: {exc}",
            ) from exc

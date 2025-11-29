"""PostgreSQL Scan Repository.

Implements ScanRepository port with SQLAlchemy async operations.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.scan import Scan
from src.app.core.domain.errors import RepositoryError
from src.app.core.domain.value_objects import ScanId
from src.app.infrastructure.db.mappers import scan_mapper
from src.app.infrastructure.db.models import ScanModel


class PostgresScanRepository:
    """SQLAlchemy implementation of ScanRepository port.

    Handles Scan entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save_scan(self, scan: Scan) -> None:
        """Save or update a scan.

        Args:
            scan: The Scan entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = scan_mapper.to_model(scan)
            merged = await self._session.merge(model)
            self._session.add(merged)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_scan",
                reason=f"Failed to save scan: {exc}",
            ) from exc

    async def get_scan(self, scan_id: ScanId) -> Scan | None:
        """Retrieve a scan by its ID.

        Args:
            scan_id: The unique scan identifier.

        Returns:
            The Scan entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(ScanModel).where(ScanModel.id == UUID(scan_id.value))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return scan_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_scan",
                reason=f"Failed to get scan: {exc}",
            ) from exc

    async def list_scans(
        self,
        status: str | None = None,
        since: datetime | None = None,
        page_id: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Scan]:
        """List scans with optional filtering.

        Args:
            status: Filter by scan status.
            since: Filter scans created after this datetime.
            page_id: Filter by associated page ID.
            offset: Number of items to skip.
            limit: Maximum number of items to return.

        Returns:
            List of Scan entities matching the filters.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(ScanModel).order_by(ScanModel.created_at.desc())

            if status:
                stmt = stmt.where(ScanModel.status == status)
            if since:
                stmt = stmt.where(ScanModel.created_at >= since)
            if page_id:
                stmt = stmt.where(ScanModel.page_id == page_id)

            stmt = stmt.offset(offset).limit(limit)

            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [scan_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_scans",
                reason=f"Failed to list scans: {exc}",
            ) from exc

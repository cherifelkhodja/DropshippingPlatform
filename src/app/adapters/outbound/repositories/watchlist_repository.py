"""PostgreSQL Watchlist Repository.

Implements WatchlistRepository port with SQLAlchemy async operations.
"""

from uuid import UUID

from sqlalchemy import delete, exists, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.watchlist import Watchlist, WatchlistItem
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import watchlist_mapper
from src.app.infrastructure.db.models.watchlist_model import (
    WatchlistModel,
    WatchlistItemModel,
)


class PostgresWatchlistRepository:
    """SQLAlchemy implementation of WatchlistRepository port.

    Handles Watchlist and WatchlistItem entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def create_watchlist(self, watchlist: Watchlist) -> Watchlist:
        """Create a new watchlist.

        Args:
            watchlist: The Watchlist entity to create.

        Returns:
            The created Watchlist entity.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = watchlist_mapper.watchlist_to_model(watchlist)
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return watchlist_mapper.watchlist_to_domain(model)
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="create_watchlist",
                reason=f"Failed to create watchlist: {exc}",
            ) from exc

    async def get_watchlist(self, watchlist_id: str) -> Watchlist | None:
        """Retrieve a watchlist by its ID.

        Args:
            watchlist_id: The unique watchlist identifier.

        Returns:
            The Watchlist entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(WatchlistModel).where(
                WatchlistModel.id == UUID(watchlist_id)
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return watchlist_mapper.watchlist_to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_watchlist",
                reason=f"Failed to get watchlist: {exc}",
            ) from exc

    async def list_watchlists(
        self, limit: int = 50, offset: int = 0
    ) -> list[Watchlist]:
        """List all watchlists.

        Returns watchlists ordered by created_at descending (newest first).

        Args:
            limit: Maximum number of watchlists to return.
            offset: Number of watchlists to skip.

        Returns:
            List of Watchlist entities.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(WatchlistModel)
                .where(WatchlistModel.is_active == True)  # noqa: E712
                .order_by(WatchlistModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [watchlist_mapper.watchlist_to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_watchlists",
                reason=f"Failed to list watchlists: {exc}",
            ) from exc

    async def add_item(self, item: WatchlistItem) -> WatchlistItem:
        """Add a page to a watchlist.

        Args:
            item: The WatchlistItem entity to add.

        Returns:
            The created WatchlistItem entity.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = watchlist_mapper.watchlist_item_to_model(item)
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
            return watchlist_mapper.watchlist_item_to_domain(model)
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="add_watchlist_item",
                reason=f"Failed to add item to watchlist: {exc}",
            ) from exc

    async def remove_item(self, watchlist_id: str, page_id: str) -> None:
        """Remove a page from a watchlist.

        Args:
            watchlist_id: The watchlist identifier.
            page_id: The page identifier to remove.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = delete(WatchlistItemModel).where(
                WatchlistItemModel.watchlist_id == UUID(watchlist_id),
                WatchlistItemModel.page_id == UUID(page_id),
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="remove_watchlist_item",
                reason=f"Failed to remove item from watchlist: {exc}",
            ) from exc

    async def list_items(self, watchlist_id: str) -> list[WatchlistItem]:
        """List all items in a watchlist.

        Returns items ordered by created_at ascending (oldest first).

        Args:
            watchlist_id: The watchlist identifier.

        Returns:
            List of WatchlistItem entities.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(WatchlistItemModel)
                .where(WatchlistItemModel.watchlist_id == UUID(watchlist_id))
                .order_by(WatchlistItemModel.created_at.asc())
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [watchlist_mapper.watchlist_item_to_domain(m) for m in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_watchlist_items",
                reason=f"Failed to list watchlist items: {exc}",
            ) from exc

    async def is_page_in_watchlist(self, watchlist_id: str, page_id: str) -> bool:
        """Check if a page is already in a watchlist.

        Args:
            watchlist_id: The watchlist identifier.
            page_id: The page identifier.

        Returns:
            True if the page is in the watchlist, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(
                exists().where(
                    WatchlistItemModel.watchlist_id == UUID(watchlist_id),
                    WatchlistItemModel.page_id == UUID(page_id),
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar() or False
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="is_page_in_watchlist",
                reason=f"Failed to check if page is in watchlist: {exc}",
            ) from exc

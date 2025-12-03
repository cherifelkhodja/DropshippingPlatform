"""PostgreSQL Page Repository.

Implements PageRepository port with SQLAlchemy async operations.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.page import Page
from src.app.core.domain.errors import RepositoryError
from src.app.infrastructure.db.mappers import page_mapper
from src.app.infrastructure.db.models import BlacklistedPageModel, PageModel


class PostgresPageRepository:
    """SQLAlchemy implementation of PageRepository port.

    Handles Page entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save(self, page: Page) -> None:
        """Save or update a page.

        Args:
            page: The Page entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = page_mapper.to_model(page)
            merged = await self._session.merge(model)
            self._session.add(merged)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_page",
                reason=f"Failed to save page: {exc}",
            ) from exc

    async def get(self, page_id: str) -> Page | None:
        """Retrieve a page by its ID.

        Args:
            page_id: The unique page identifier.

        Returns:
            The Page entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(PageModel).where(PageModel.id == UUID(page_id))
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return page_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_page",
                reason=f"Failed to get page: {exc}",
            ) from exc

    async def exists(self, page_id: str) -> bool:
        """Check if a page exists.

        Args:
            page_id: The unique page identifier (can be UUID or Meta page ID).

        Returns:
            True if the page exists, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Try to parse as UUID - Meta page IDs are numeric and won't parse
            page_uuid = UUID(page_id)
        except ValueError:
            # Not a valid UUID (e.g., Meta page ID like "123456789")
            # These can't exist in our UUID-based pages table
            return False

        try:
            stmt = select(PageModel.id).where(PageModel.id == page_uuid)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="exists_page",
                reason=f"Failed to check page existence: {exc}",
            ) from exc

    async def list_all(self) -> list[Page]:
        """List all pages.

        Returns:
            List of all Page entities.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(PageModel).order_by(PageModel.created_at.desc())
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [page_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_all_pages",
                reason=f"Failed to list pages: {exc}",
            ) from exc

    async def is_blacklisted(self, page_id: str) -> bool:
        """Check if a page is blacklisted.

        Args:
            page_id: The unique page identifier (can be UUID or Meta page ID).

        Returns:
            True if the page is blacklisted, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Try to parse as UUID - Meta page IDs are numeric and won't parse
            page_uuid = UUID(page_id)
        except ValueError:
            # Not a valid UUID (e.g., Meta page ID like "123456789")
            # These can't be in our UUID-based blacklist, so return False
            return False

        try:
            stmt = select(BlacklistedPageModel.page_id).where(
                BlacklistedPageModel.page_id == page_uuid
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="is_blacklisted",
                reason=f"Failed to check blacklist: {exc}",
            ) from exc

    async def blacklist(self, page_id: str) -> None:
        """Add a page to the blacklist.

        Args:
            page_id: The unique page identifier.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            blacklisted = BlacklistedPageModel(page_id=UUID(page_id))
            merged = await self._session.merge(blacklisted)
            self._session.add(merged)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="blacklist_page",
                reason=f"Failed to blacklist page: {exc}",
            ) from exc

    async def get_by_meta_page_id(self, meta_page_id: str) -> Page | None:
        """Retrieve a page by its Meta page ID.

        Args:
            meta_page_id: The Meta/Facebook page identifier.

        Returns:
            The Page entity if found, None otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(PageModel).where(PageModel.meta_page_id == meta_page_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return page_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_by_meta_page_id",
                reason=f"Failed to get page by meta_page_id: {exc}",
            ) from exc

    async def exists_by_meta_page_id(self, meta_page_id: str) -> bool:
        """Check if a page with given Meta page ID exists.

        Args:
            meta_page_id: The Meta/Facebook page identifier.

        Returns:
            True if the page exists, False otherwise.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(PageModel.id).where(PageModel.meta_page_id == meta_page_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="exists_by_meta_page_id",
                reason=f"Failed to check page existence: {exc}",
            ) from exc

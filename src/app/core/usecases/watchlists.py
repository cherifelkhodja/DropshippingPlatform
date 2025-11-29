"""Watchlist Use Cases.

CRUD operations for managing watchlists and their items.
"""

from uuid import uuid4

from ..domain.entities import Watchlist, WatchlistItem
from ..domain.errors import EntityNotFoundError
from ..ports import LoggingPort, WatchlistRepository


class CreateWatchlistUseCase:
    """Use case for creating a new watchlist.

    Creates a watchlist with a given name and optional description.
    """

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(
        self,
        name: str,
        description: str | None = None,
    ) -> Watchlist:
        """Execute the create watchlist use case.

        Args:
            name: Human-readable name for the watchlist.
            description: Optional description of the watchlist.

        Returns:
            The created Watchlist entity.
        """
        self._logger.info(
            "Creating watchlist",
            name=name,
            has_description=description is not None,
        )

        watchlist = Watchlist.create(
            id=str(uuid4()),
            name=name,
            description=description,
        )

        created = await self._watchlist_repo.create_watchlist(watchlist)

        self._logger.info(
            "Watchlist created successfully",
            watchlist_id=created.id,
            name=created.name,
        )

        return created


class GetWatchlistUseCase:
    """Use case for retrieving a watchlist by ID."""

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(self, watchlist_id: str) -> Watchlist:
        """Execute the get watchlist use case.

        Args:
            watchlist_id: The unique watchlist identifier.

        Returns:
            The Watchlist entity.

        Raises:
            EntityNotFoundError: If the watchlist does not exist.
        """
        self._logger.debug("Getting watchlist", watchlist_id=watchlist_id)

        watchlist = await self._watchlist_repo.get_watchlist(watchlist_id)

        if watchlist is None:
            self._logger.warning("Watchlist not found", watchlist_id=watchlist_id)
            raise EntityNotFoundError("Watchlist", watchlist_id)

        return watchlist


class ListWatchlistsUseCase:
    """Use case for listing all watchlists."""

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Watchlist]:
        """Execute the list watchlists use case.

        Args:
            limit: Maximum number of watchlists to return.
            offset: Number of watchlists to skip.

        Returns:
            List of Watchlist entities.
        """
        self._logger.debug(
            "Listing watchlists",
            limit=limit,
            offset=offset,
        )

        watchlists = await self._watchlist_repo.list_watchlists(
            limit=limit,
            offset=offset,
        )

        self._logger.debug(
            "Listed watchlists",
            count=len(watchlists),
        )

        return watchlists


class AddPageToWatchlistUseCase:
    """Use case for adding a page to a watchlist."""

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(
        self,
        watchlist_id: str,
        page_id: str,
    ) -> WatchlistItem:
        """Execute the add page to watchlist use case.

        If the page is already in the watchlist, the existing item is
        returned without creating a duplicate.

        Args:
            watchlist_id: The watchlist identifier.
            page_id: The page identifier to add.

        Returns:
            The created or existing WatchlistItem entity.

        Raises:
            EntityNotFoundError: If the watchlist does not exist.
        """
        self._logger.info(
            "Adding page to watchlist",
            watchlist_id=watchlist_id,
            page_id=page_id,
        )

        # Verify watchlist exists
        watchlist = await self._watchlist_repo.get_watchlist(watchlist_id)
        if watchlist is None:
            self._logger.warning(
                "Watchlist not found for adding page",
                watchlist_id=watchlist_id,
            )
            raise EntityNotFoundError("Watchlist", watchlist_id)

        # Check if page is already in watchlist
        is_already_in = await self._watchlist_repo.is_page_in_watchlist(
            watchlist_id=watchlist_id,
            page_id=page_id,
        )

        if is_already_in:
            self._logger.info(
                "Page already in watchlist",
                watchlist_id=watchlist_id,
                page_id=page_id,
            )
            # Retrieve and return the existing item
            items = await self._watchlist_repo.list_items(watchlist_id)
            for item in items:
                if item.page_id == page_id:
                    return item
            # Should not reach here, but create a new item if it does
            self._logger.warning(
                "Page marked as in watchlist but not found in items",
                watchlist_id=watchlist_id,
                page_id=page_id,
            )

        # Create new item
        item = WatchlistItem.create(
            id=str(uuid4()),
            watchlist_id=watchlist_id,
            page_id=page_id,
        )

        created = await self._watchlist_repo.add_item(item)

        self._logger.info(
            "Page added to watchlist successfully",
            watchlist_id=watchlist_id,
            page_id=page_id,
            item_id=created.id,
        )

        return created


class RemovePageFromWatchlistUseCase:
    """Use case for removing a page from a watchlist."""

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(
        self,
        watchlist_id: str,
        page_id: str,
    ) -> None:
        """Execute the remove page from watchlist use case.

        Args:
            watchlist_id: The watchlist identifier.
            page_id: The page identifier to remove.

        Raises:
            EntityNotFoundError: If the watchlist does not exist.
        """
        self._logger.info(
            "Removing page from watchlist",
            watchlist_id=watchlist_id,
            page_id=page_id,
        )

        # Verify watchlist exists
        watchlist = await self._watchlist_repo.get_watchlist(watchlist_id)
        if watchlist is None:
            self._logger.warning(
                "Watchlist not found for removing page",
                watchlist_id=watchlist_id,
            )
            raise EntityNotFoundError("Watchlist", watchlist_id)

        await self._watchlist_repo.remove_item(
            watchlist_id=watchlist_id,
            page_id=page_id,
        )

        self._logger.info(
            "Page removed from watchlist successfully",
            watchlist_id=watchlist_id,
            page_id=page_id,
        )


class ListWatchlistItemsUseCase:
    """Use case for listing all items in a watchlist."""

    def __init__(
        self,
        watchlist_repository: WatchlistRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            watchlist_repository: Repository for Watchlist entities.
            logger: Logging port for structured logging.
        """
        self._watchlist_repo = watchlist_repository
        self._logger = logger

    async def execute(self, watchlist_id: str) -> list[WatchlistItem]:
        """Execute the list watchlist items use case.

        Args:
            watchlist_id: The watchlist identifier.

        Returns:
            List of WatchlistItem entities.

        Raises:
            EntityNotFoundError: If the watchlist does not exist.
        """
        self._logger.debug(
            "Listing watchlist items",
            watchlist_id=watchlist_id,
        )

        # Verify watchlist exists
        watchlist = await self._watchlist_repo.get_watchlist(watchlist_id)
        if watchlist is None:
            self._logger.warning(
                "Watchlist not found for listing items",
                watchlist_id=watchlist_id,
            )
            raise EntityNotFoundError("Watchlist", watchlist_id)

        items = await self._watchlist_repo.list_items(watchlist_id)

        self._logger.debug(
            "Listed watchlist items",
            watchlist_id=watchlist_id,
            count=len(items),
        )

        return items

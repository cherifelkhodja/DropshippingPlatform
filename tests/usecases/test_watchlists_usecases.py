"""Unit tests for watchlist use cases.

Tests the CRUD operations for watchlists and their items.
"""

import pytest

from src.app.core.domain import EntityNotFoundError
from src.app.core.usecases.watchlists import (
    CreateWatchlistUseCase,
    GetWatchlistUseCase,
    ListWatchlistsUseCase,
    AddPageToWatchlistUseCase,
    RemovePageFromWatchlistUseCase,
    ListWatchlistItemsUseCase,
    RescoreWatchlistUseCase,
)
from tests.conftest import FakeLoggingPort, FakeWatchlistRepository, FakeTaskDispatcher


class TestCreateWatchlistUseCase:
    """Tests for CreateWatchlistUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> CreateWatchlistUseCase:
        """Create use case instance with fake dependencies."""
        return CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_create_watchlist_with_name(
        self,
        use_case: CreateWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
    ) -> None:
        """Should create a watchlist with the given name."""
        result = await use_case.execute(name="Top FR Winners")

        assert result.name == "Top FR Winners"
        assert result.description is None
        assert result.is_active is True
        assert result.id in fake_watchlist_repo.watchlists

    @pytest.mark.asyncio
    async def test_create_watchlist_with_description(
        self,
        use_case: CreateWatchlistUseCase,
    ) -> None:
        """Should create a watchlist with name and description."""
        result = await use_case.execute(
            name="Top FR Winners",
            description="French stores with high scores",
        )

        assert result.name == "Top FR Winners"
        assert result.description == "French stores with high scores"

    @pytest.mark.asyncio
    async def test_create_watchlist_generates_unique_id(
        self,
        use_case: CreateWatchlistUseCase,
    ) -> None:
        """Should generate a unique ID for each watchlist."""
        result1 = await use_case.execute(name="Watchlist 1")
        result2 = await use_case.execute(name="Watchlist 2")

        assert result1.id != result2.id


class TestGetWatchlistUseCase:
    """Tests for GetWatchlistUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> GetWatchlistUseCase:
        """Create use case instance with fake dependencies."""
        return GetWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_get_existing_watchlist(
        self,
        use_case: GetWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return watchlist when it exists."""
        # Create a watchlist first
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        created = await create_uc.execute(name="Test Watchlist")

        # Get the watchlist
        result = await use_case.execute(created.id)

        assert result.id == created.id
        assert result.name == "Test Watchlist"

    @pytest.mark.asyncio
    async def test_get_nonexistent_watchlist_raises_error(
        self,
        use_case: GetWatchlistUseCase,
    ) -> None:
        """Should raise EntityNotFoundError for nonexistent watchlist."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute("nonexistent-id")

        assert "Watchlist" in str(exc_info.value)


class TestListWatchlistsUseCase:
    """Tests for ListWatchlistsUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> ListWatchlistsUseCase:
        """Create use case instance with fake dependencies."""
        return ListWatchlistsUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_list_empty_watchlists(
        self,
        use_case: ListWatchlistsUseCase,
    ) -> None:
        """Should return empty list when no watchlists exist."""
        result = await use_case.execute()

        assert result == []

    @pytest.mark.asyncio
    async def test_list_multiple_watchlists(
        self,
        use_case: ListWatchlistsUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return all watchlists."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        await create_uc.execute(name="Watchlist 1")
        await create_uc.execute(name="Watchlist 2")
        await create_uc.execute(name="Watchlist 3")

        result = await use_case.execute()

        assert len(result) == 3
        names = {w.name for w in result}
        assert names == {"Watchlist 1", "Watchlist 2", "Watchlist 3"}

    @pytest.mark.asyncio
    async def test_list_watchlists_with_limit(
        self,
        use_case: ListWatchlistsUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should respect limit parameter."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        for i in range(5):
            await create_uc.execute(name=f"Watchlist {i}")

        result = await use_case.execute(limit=3)

        assert len(result) == 3


class TestAddPageToWatchlistUseCase:
    """Tests for AddPageToWatchlistUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> AddPageToWatchlistUseCase:
        """Create use case instance with fake dependencies."""
        return AddPageToWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_add_page_to_watchlist(
        self,
        use_case: AddPageToWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should add a page to the watchlist."""
        # Create a watchlist first
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        # Add a page
        result = await use_case.execute(
            watchlist_id=watchlist.id,
            page_id="page-123",
        )

        assert result.watchlist_id == watchlist.id
        assert result.page_id == "page-123"
        assert len(fake_watchlist_repo.items) == 1

    @pytest.mark.asyncio
    async def test_add_duplicate_page_returns_existing(
        self,
        use_case: AddPageToWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return existing item when adding duplicate."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        # Add page twice
        result1 = await use_case.execute(
            watchlist_id=watchlist.id,
            page_id="page-123",
        )
        result2 = await use_case.execute(
            watchlist_id=watchlist.id,
            page_id="page-123",
        )

        # Should return existing item, not create duplicate
        assert result1.id == result2.id
        assert len(fake_watchlist_repo.items) == 1

    @pytest.mark.asyncio
    async def test_add_page_to_nonexistent_watchlist_raises_error(
        self,
        use_case: AddPageToWatchlistUseCase,
    ) -> None:
        """Should raise EntityNotFoundError for nonexistent watchlist."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(
                watchlist_id="nonexistent-id",
                page_id="page-123",
            )

        assert "Watchlist" in str(exc_info.value)


class TestRemovePageFromWatchlistUseCase:
    """Tests for RemovePageFromWatchlistUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> RemovePageFromWatchlistUseCase:
        """Create use case instance with fake dependencies."""
        return RemovePageFromWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_remove_page_from_watchlist(
        self,
        use_case: RemovePageFromWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should remove page from watchlist."""
        # Setup: create watchlist and add page
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        add_uc = AddPageToWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-123")

        # Remove the page
        await use_case.execute(watchlist_id=watchlist.id, page_id="page-123")

        # Verify removal
        assert len(fake_watchlist_repo.items) == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent_page_succeeds_silently(
        self,
        use_case: RemovePageFromWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should succeed silently when removing nonexistent page."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        # This should not raise an error
        await use_case.execute(
            watchlist_id=watchlist.id,
            page_id="nonexistent-page",
        )

    @pytest.mark.asyncio
    async def test_remove_from_nonexistent_watchlist_raises_error(
        self,
        use_case: RemovePageFromWatchlistUseCase,
    ) -> None:
        """Should raise EntityNotFoundError for nonexistent watchlist."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(
                watchlist_id="nonexistent-id",
                page_id="page-123",
            )

        assert "Watchlist" in str(exc_info.value)


class TestListWatchlistItemsUseCase:
    """Tests for ListWatchlistItemsUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> ListWatchlistItemsUseCase:
        """Create use case instance with fake dependencies."""
        return ListWatchlistItemsUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_list_empty_items(
        self,
        use_case: ListWatchlistItemsUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return empty list when watchlist has no items."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Empty Watchlist")

        result = await use_case.execute(watchlist.id)

        assert result == []

    @pytest.mark.asyncio
    async def test_list_multiple_items(
        self,
        use_case: ListWatchlistItemsUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return all items in the watchlist."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        add_uc = AddPageToWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-1")
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-2")
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-3")

        result = await use_case.execute(watchlist.id)

        assert len(result) == 3
        page_ids = {item.page_id for item in result}
        assert page_ids == {"page-1", "page-2", "page-3"}

    @pytest.mark.asyncio
    async def test_list_items_for_nonexistent_watchlist_raises_error(
        self,
        use_case: ListWatchlistItemsUseCase,
    ) -> None:
        """Should raise EntityNotFoundError for nonexistent watchlist."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute("nonexistent-id")

        assert "Watchlist" in str(exc_info.value)


class TestRescoreWatchlistUseCase:
    """Tests for RescoreWatchlistUseCase."""

    @pytest.fixture
    def fake_task_dispatcher(self) -> FakeTaskDispatcher:
        """Create a fake task dispatcher for testing."""
        return FakeTaskDispatcher()

    @pytest.fixture
    def use_case(
        self,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
        fake_logger: FakeLoggingPort,
    ) -> RescoreWatchlistUseCase:
        """Create use case instance with fake dependencies."""
        return RescoreWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            task_dispatcher=fake_task_dispatcher,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_rescore_empty_watchlist(
        self,
        use_case: RescoreWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return 0 when watchlist is empty."""
        # Create an empty watchlist
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Empty Watchlist")

        result = await use_case.execute(watchlist.id)

        assert result == 0
        assert len(fake_task_dispatcher.dispatched_tasks) == 0

    @pytest.mark.asyncio
    async def test_rescore_watchlist_with_items(
        self,
        use_case: RescoreWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should dispatch tasks for all pages in the watchlist."""
        # Setup: create watchlist with items
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        add_uc = AddPageToWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-1")
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-2")
        await add_uc.execute(watchlist_id=watchlist.id, page_id="page-3")

        result = await use_case.execute(watchlist.id)

        assert result == 3
        assert len(fake_task_dispatcher.dispatched_tasks) == 3

        # Verify all tasks are compute_shop_score type
        for task in fake_task_dispatcher.dispatched_tasks:
            assert task["type"] == "compute_shop_score"

        # Verify all page IDs were dispatched
        dispatched_page_ids = {task["page_id"] for task in fake_task_dispatcher.dispatched_tasks}
        assert dispatched_page_ids == {"page-1", "page-2", "page-3"}

    @pytest.mark.asyncio
    async def test_rescore_nonexistent_watchlist_raises_error(
        self,
        use_case: RescoreWatchlistUseCase,
    ) -> None:
        """Should raise EntityNotFoundError for nonexistent watchlist."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute("nonexistent-id")

        assert "Watchlist" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rescore_returns_dispatched_count(
        self,
        use_case: RescoreWatchlistUseCase,
        fake_watchlist_repo: FakeWatchlistRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should return exact count of dispatched tasks."""
        create_uc = CreateWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        watchlist = await create_uc.execute(name="Test Watchlist")

        add_uc = AddPageToWatchlistUseCase(
            watchlist_repository=fake_watchlist_repo,
            logger=fake_logger,
        )
        for i in range(5):
            await add_uc.execute(watchlist_id=watchlist.id, page_id=f"page-{i}")

        result = await use_case.execute(watchlist.id)

        assert result == 5
        assert len(fake_task_dispatcher.dispatched_tasks) == 5

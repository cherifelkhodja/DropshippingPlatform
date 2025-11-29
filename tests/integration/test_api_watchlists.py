"""Integration tests for /watchlists API endpoints.

Tests for the watchlist API endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.app.core.domain.entities.watchlist import Watchlist, WatchlistItem


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    with patch("src.app.api.dependencies.get_database") as mock_get_db:
        mock_db = MagicMock()
        mock_session = AsyncMock()
        mock_db.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db.session.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_get_db.return_value = mock_db
        yield mock_session


class TestWatchlistEndpoints:
    """Tests for watchlist CRUD endpoints."""

    @pytest.fixture
    def sample_watchlist(self) -> Watchlist:
        """Create a sample watchlist for testing."""
        return Watchlist(
            id="watchlist-001",
            name="Top FR Winners",
            description="French stores with high scores",
            created_at=datetime(2024, 3, 20, 15, 45, 0),
            is_active=True,
        )

    @pytest.fixture
    def sample_watchlist_item(self) -> WatchlistItem:
        """Create a sample watchlist item for testing."""
        return WatchlistItem(
            id="item-001",
            watchlist_id="watchlist-001",
            page_id="page-001",
            created_at=datetime(2024, 3, 20, 16, 0, 0),
        )

    def test_create_watchlist(self, mock_database) -> None:
        """POST /watchlists creates a new watchlist."""
        mock_watchlist_repo = AsyncMock()
        created_watchlist = Watchlist(
            id="new-watchlist-id",
            name="My Watchlist",
            description="Test description",
            created_at=datetime.utcnow(),
            is_active=True,
        )
        mock_watchlist_repo.create_watchlist.return_value = created_watchlist

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/watchlists",
                json={
                    "name": "My Watchlist",
                    "description": "Test description",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "My Watchlist"
            assert data["description"] == "Test description"
            assert data["is_active"] is True
            assert "id" in data
            assert "created_at" in data

    def test_create_watchlist_without_description(self, mock_database) -> None:
        """POST /watchlists creates a watchlist without description."""
        mock_watchlist_repo = AsyncMock()
        created_watchlist = Watchlist(
            id="new-watchlist-id",
            name="Simple Watchlist",
            description=None,
            created_at=datetime.utcnow(),
            is_active=True,
        )
        mock_watchlist_repo.create_watchlist.return_value = created_watchlist

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/watchlists",
                json={"name": "Simple Watchlist"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Simple Watchlist"
            assert data["description"] is None

    def test_create_watchlist_validation_error(self, mock_database) -> None:
        """POST /watchlists returns 422 for invalid request."""
        from src.app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/watchlists",
            json={"name": ""},  # Empty name should fail validation
        )

        assert response.status_code == 422

    def test_list_watchlists(
        self, mock_database, sample_watchlist: Watchlist
    ) -> None:
        """GET /watchlists returns list of watchlists."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.list_watchlists.return_value = [sample_watchlist]

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert data["count"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["name"] == "Top FR Winners"

    def test_list_watchlists_empty(self, mock_database) -> None:
        """GET /watchlists returns empty list when no watchlists exist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.list_watchlists.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["count"] == 0

    def test_list_watchlists_with_pagination(self, mock_database) -> None:
        """GET /watchlists respects pagination parameters."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.list_watchlists.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists?limit=25&offset=10")

            assert response.status_code == 200
            mock_watchlist_repo.list_watchlists.assert_called_once_with(
                limit=25, offset=10
            )

    def test_get_watchlist(
        self, mock_database, sample_watchlist: Watchlist
    ) -> None:
        """GET /watchlists/{id} returns watchlist details."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists/watchlist-001")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "watchlist-001"
            assert data["name"] == "Top FR Winners"
            assert data["description"] == "French stores with high scores"

    def test_get_watchlist_not_found(self, mock_database) -> None:
        """GET /watchlists/{id} returns 404 for nonexistent watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists/nonexistent")

            assert response.status_code == 404

    def test_list_watchlist_items(
        self,
        mock_database,
        sample_watchlist: Watchlist,
        sample_watchlist_item: WatchlistItem,
    ) -> None:
        """GET /watchlists/{id}/items returns list of items."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist
        mock_watchlist_repo.list_items.return_value = [sample_watchlist_item]

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists/watchlist-001/items")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert data["count"] == 1
            assert data["items"][0]["page_id"] == "page-001"

    def test_list_watchlist_items_not_found(self, mock_database) -> None:
        """GET /watchlists/{id}/items returns 404 for nonexistent watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists/nonexistent/items")

            assert response.status_code == 404

    def test_add_page_to_watchlist(
        self,
        mock_database,
        sample_watchlist: Watchlist,
        sample_watchlist_item: WatchlistItem,
    ) -> None:
        """POST /watchlists/{id}/items adds a page to the watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist
        mock_watchlist_repo.is_page_in_watchlist.return_value = False
        mock_watchlist_repo.add_item.return_value = sample_watchlist_item

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/watchlists/watchlist-001/items",
                json={"page_id": "page-001"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["watchlist_id"] == "watchlist-001"
            assert data["page_id"] == "page-001"

    def test_add_page_to_watchlist_not_found(self, mock_database) -> None:
        """POST /watchlists/{id}/items returns 404 for nonexistent watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post(
                "/api/v1/watchlists/nonexistent/items",
                json={"page_id": "page-001"},
            )

            assert response.status_code == 404

    def test_remove_page_from_watchlist(
        self, mock_database, sample_watchlist: Watchlist
    ) -> None:
        """DELETE /watchlists/{id}/items/{page_id} removes page from watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist
        mock_watchlist_repo.remove_item.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.delete(
                "/api/v1/watchlists/watchlist-001/items/page-001"
            )

            assert response.status_code == 204
            mock_watchlist_repo.remove_item.assert_called_once_with(
                watchlist_id="watchlist-001",
                page_id="page-001",
            )

    def test_remove_page_from_watchlist_not_found(self, mock_database) -> None:
        """DELETE /watchlists/{id}/items/{page_id} returns 404 for nonexistent watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.delete(
                "/api/v1/watchlists/nonexistent/items/page-001"
            )

            assert response.status_code == 404


class TestWatchlistResponseSchema:
    """Tests for watchlist API response schemas."""

    @pytest.fixture
    def sample_watchlist(self) -> Watchlist:
        """Create a sample watchlist for testing."""
        return Watchlist(
            id="watchlist-001",
            name="Top FR Winners",
            description="French stores with high scores",
            created_at=datetime(2024, 3, 20, 15, 45, 0),
            is_active=True,
        )

    def test_watchlist_response_structure(
        self, mock_database, sample_watchlist: Watchlist
    ) -> None:
        """Watchlist response contains all expected fields."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/watchlists/watchlist-001")

            assert response.status_code == 200
            data = response.json()

            # Verify all expected fields are present
            assert "id" in data
            assert "name" in data
            assert "description" in data
            assert "created_at" in data
            assert "is_active" in data

            # Verify field types
            assert isinstance(data["id"], str)
            assert isinstance(data["name"], str)
            assert data["description"] is None or isinstance(data["description"], str)
            assert isinstance(data["created_at"], str)  # ISO format datetime
            assert isinstance(data["is_active"], bool)


class TestScanNowEndpoint:
    """Tests for POST /watchlists/{id}/scan_now endpoint."""

    @pytest.fixture
    def sample_watchlist(self) -> Watchlist:
        """Create a sample watchlist for testing."""
        return Watchlist(
            id="watchlist-001",
            name="Top FR Winners",
            description="French stores with high scores",
            created_at=datetime(2024, 3, 20, 15, 45, 0),
            is_active=True,
        )

    @pytest.fixture
    def sample_watchlist_items(self) -> list[WatchlistItem]:
        """Create sample watchlist items for testing."""
        return [
            WatchlistItem(
                id=f"item-00{i}",
                watchlist_id="watchlist-001",
                page_id=f"page-00{i}",
                created_at=datetime(2024, 3, 20, 16, i, 0),
            )
            for i in range(1, 4)
        ]

    def test_scan_now_success(
        self,
        mock_database,
        sample_watchlist: Watchlist,
        sample_watchlist_items: list[WatchlistItem],
    ) -> None:
        """POST /watchlists/{id}/scan_now dispatches scoring tasks."""
        from src.app.api import dependencies

        # Clear the lru_cache for get_task_dispatcher
        dependencies.get_task_dispatcher.cache_clear()

        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist
        mock_watchlist_repo.list_items.return_value = sample_watchlist_items

        mock_task_dispatcher = AsyncMock()
        mock_task_dispatcher.dispatch_compute_shop_score.return_value = "task-id-123"

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ), patch(
            "src.app.api.dependencies.CeleryTaskDispatcher",
            return_value=mock_task_dispatcher,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post("/api/v1/watchlists/watchlist-001/scan_now")

            assert response.status_code == 202
            data = response.json()
            assert data["watchlist_id"] == "watchlist-001"
            assert data["tasks_dispatched"] == 3
            assert "message" in data

    def test_scan_now_empty_watchlist(
        self,
        mock_database,
        sample_watchlist: Watchlist,
    ) -> None:
        """POST /watchlists/{id}/scan_now returns 0 for empty watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist
        mock_watchlist_repo.list_items.return_value = []

        mock_task_dispatcher = AsyncMock()

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ), patch(
            "src.app.api.dependencies.get_task_dispatcher",
            return_value=mock_task_dispatcher,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post("/api/v1/watchlists/watchlist-001/scan_now")

            assert response.status_code == 202
            data = response.json()
            assert data["tasks_dispatched"] == 0
            mock_task_dispatcher.dispatch_compute_shop_score.assert_not_called()

    def test_scan_now_not_found(self, mock_database) -> None:
        """POST /watchlists/{id}/scan_now returns 404 for nonexistent watchlist."""
        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post("/api/v1/watchlists/nonexistent/scan_now")

            assert response.status_code == 404

    def test_scan_now_response_structure(
        self,
        mock_database,
        sample_watchlist: Watchlist,
        sample_watchlist_items: list[WatchlistItem],
    ) -> None:
        """Scan now response contains all expected fields."""
        from src.app.api import dependencies

        # Clear the lru_cache for get_task_dispatcher
        dependencies.get_task_dispatcher.cache_clear()

        mock_watchlist_repo = AsyncMock()
        mock_watchlist_repo.get_watchlist.return_value = sample_watchlist
        mock_watchlist_repo.list_items.return_value = sample_watchlist_items

        mock_task_dispatcher = AsyncMock()
        mock_task_dispatcher.dispatch_compute_shop_score.return_value = "task-id"

        with patch(
            "src.app.api.dependencies.PostgresWatchlistRepository",
            return_value=mock_watchlist_repo,
        ), patch(
            "src.app.api.dependencies.CeleryTaskDispatcher",
            return_value=mock_task_dispatcher,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post("/api/v1/watchlists/watchlist-001/scan_now")

            assert response.status_code == 202
            data = response.json()

            # Verify all expected fields
            assert "watchlist_id" in data
            assert "tasks_dispatched" in data
            assert "message" in data

            # Verify field types
            assert isinstance(data["watchlist_id"], str)
            assert isinstance(data["tasks_dispatched"], int)
            assert isinstance(data["message"], str)

"""Integration tests for API endpoints.

Tests the FastAPI application with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.app.core.domain.entities import Page, Scan, ScanType, ScanStatus, ScanResult
from src.app.core.domain.value_objects import Url, Country, ScanId, PageState


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


@pytest.fixture
def client(mock_database):
    """Create test client with mocked dependencies."""
    from src.app.main import create_app
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        """Health endpoint returns ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data


class TestPagesEndpoint:
    """Tests for /api/v1/pages endpoints."""

    @pytest.fixture
    def mock_page(self) -> Page:
        """Create a mock page for testing."""
        return Page(
            id="page-123",
            url=Url("https://example-store.com"),
            domain="example-store.com",
            state=PageState.initial(),
            country=Country("US"),
            is_shopify=True,
            active_ads_count=5,
            total_ads_count=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    def test_list_pages_empty(self, mock_database) -> None:
        """List pages returns empty list when no pages exist."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["page"] == 1
            assert data["has_more"] is False

    def test_list_pages_with_data(self, mock_page: Page, mock_database) -> None:
        """List pages returns pages when data exists."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = [mock_page]

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages")

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["id"] == "page-123"
            assert data["items"][0]["is_shopify"] is True
            assert data["total"] == 1

    def test_list_pages_filter_by_shopify(self, mock_page: Page, mock_database) -> None:
        """List pages filters by Shopify status."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = [mock_page]

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            # Filter for Shopify pages
            response = client.get("/api/v1/pages?is_shopify=true")
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1

            # Filter for non-Shopify pages
            response = client.get("/api/v1/pages?is_shopify=false")
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 0

    def test_get_page_not_found(self, mock_database) -> None:
        """Get page returns 404 when page doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo.get.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/nonexistent")

            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "EntityNotFound"

    def test_get_page_success(self, mock_page: Page, mock_database) -> None:
        """Get page returns page details when found."""
        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_page

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/page-123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "page-123"
            assert data["url"] == "https://example-store.com"
            assert data["is_shopify"] is True


class TestScansEndpoint:
    """Tests for /api/v1/scans endpoints."""

    @pytest.fixture
    def mock_scan(self) -> Scan:
        """Create a mock scan for testing."""
        return Scan(
            id=ScanId.generate(),
            page_id="page-123",
            scan_type=ScanType.FULL,
            status=ScanStatus.COMPLETED,
            result=ScanResult(ads_found=5, new_ads=2, products_found=100),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )

    def test_get_scan_invalid_id(self, mock_database) -> None:
        """Get scan returns 400 for invalid scan ID."""
        from src.app.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/scans/invalid-id")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid" in data["message"]

    def test_get_scan_not_found(self, mock_database) -> None:
        """Get scan returns 404 when scan doesn't exist."""
        mock_repo = AsyncMock()
        mock_repo.get_scan.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresScanRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            scan_id = str(ScanId.generate())
            response = client.get(f"/api/v1/scans/{scan_id}")

            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "EntityNotFound"

    def test_get_scan_success(self, mock_scan: Scan, mock_database) -> None:
        """Get scan returns scan details when found."""
        mock_repo = AsyncMock()
        mock_repo.get_scan.return_value = mock_scan

        with patch(
            "src.app.api.dependencies.PostgresScanRepository",
            return_value=mock_repo,
        ):
            from src.app.main import create_app
            app = create_app()
            client = TestClient(app)

            response = client.get(f"/api/v1/scans/{mock_scan.id}")

            assert response.status_code == 200
            data = response.json()
            assert data["page_id"] == "page-123"
            assert data["scan_type"] == "full"
            assert data["status"] == "completed"
            assert data["result"]["ads_found"] == 5


class TestKeywordsEndpoint:
    """Tests for /api/v1/keywords endpoints."""

    def test_search_invalid_country(self, mock_database) -> None:
        """Search returns 422 for invalid country code."""
        from src.app.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/keywords/search",
            json={"keyword": "test", "country": "INVALID"},
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_search_empty_keyword(self, mock_database) -> None:
        """Search returns 422 for empty keyword."""
        from src.app.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/keywords/search",
            json={"keyword": "", "country": "US"},
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_search_valid_request_format(self, mock_database) -> None:
        """Search endpoint accepts valid request format."""
        # This test verifies the endpoint exists and validates input
        # Full integration would require mocking the Meta Ads client
        from src.app.main import create_app
        app = create_app()
        client = TestClient(app)

        # Valid request should not return 422 (validation error)
        response = client.post(
            "/api/v1/keywords/search",
            json={"keyword": "dropshipping", "country": "US"},
        )

        # Should either succeed (200) or fail with domain error (400/500)
        # but not with validation error (422)
        assert response.status_code != 422

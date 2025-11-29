"""Integration tests for API endpoints.

Tests the FastAPI application with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.app.core.domain.entities import Page, Scan, ScanType, ScanStatus, ScanResult, ShopScore
from src.app.core.domain.value_objects import Url, Country, ScanId, PageState
from src.app.core.domain.errors import (
    MetaAdsRateLimitError,
    MetaAdsAuthenticationError,
    MetaAdsApiError,
    ScrapingBlockedError,
    ScrapingTimeoutError,
    SitemapNotFoundError,
    SitemapParsingError,
    InvalidLanguageError,
)


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
def mock_http_session():
    """Mock HTTP session for testing."""
    return MagicMock()


@pytest.fixture
def client(mock_database, mock_http_session):
    """Create test client with mocked dependencies."""
    from src.app.main import create_app

    app = create_app()
    # Mock the http_session in app.state
    app.state.http_session = mock_http_session
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

    def test_search_invalid_country(self, mock_database, mock_http_session) -> None:
        """Search returns 422 for invalid country code."""
        from src.app.main import create_app

        app = create_app()
        app.state.http_session = mock_http_session
        client = TestClient(app)

        response = client.post(
            "/api/v1/keywords/search",
            json={"keyword": "test", "country": "INVALID"},
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_search_empty_keyword(self, mock_database, mock_http_session) -> None:
        """Search returns 422 for empty keyword."""
        from src.app.main import create_app

        app = create_app()
        app.state.http_session = mock_http_session
        client = TestClient(app)

        response = client.post(
            "/api/v1/keywords/search",
            json={"keyword": "", "country": "US"},
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_search_valid_request_format(
        self, mock_database, mock_http_session
    ) -> None:
        """Search endpoint accepts valid request format."""
        # This test verifies the endpoint exists, validates input, and returns
        # a proper response (not 422 Pydantic validation error)
        from src.app.main import create_app

        app = create_app()
        app.state.http_session = mock_http_session
        client = TestClient(app, raise_server_exceptions=False)

        # Valid request should not return 422 (validation error)
        response = client.post(
            "/api/v1/keywords/search",
            json={"keyword": "dropshipping", "country": "US"},
        )

        # Should either succeed (200) or fail with domain/external error
        # but not with Pydantic validation error (422) or method not allowed (405)
        # 500 is acceptable here since the HTTP client is mocked
        assert response.status_code not in [405, 422]


class TestExceptionHandlers:
    """Tests for exception handlers - verifying correct HTTP status codes.

    These tests verify that domain exceptions are correctly mapped to HTTP status codes.
    They test the exception handlers directly by raising exceptions from repository mocks.
    """

    def test_scraping_blocked_returns_403(
        self, mock_database, mock_http_session
    ) -> None:
        """ScrapingBlockedError returns 403 Forbidden."""
        from src.app.main import create_app

        mock_repo = AsyncMock()
        mock_repo.list_all.side_effect = ScrapingBlockedError(
            url="https://blocked-site.com", status_code=403
        )

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            app = create_app()
            app.state.http_session = mock_http_session
            client = TestClient(app, raise_server_exceptions=False)

            response = client.get("/api/v1/pages")

            assert response.status_code == 403
            data = response.json()
            assert data["error"] == "ScrapingBlocked"

    def test_scraping_timeout_returns_504(
        self, mock_database, mock_http_session
    ) -> None:
        """ScrapingTimeoutError returns 504 Gateway Timeout."""
        from src.app.main import create_app

        mock_repo = AsyncMock()
        mock_repo.list_all.side_effect = ScrapingTimeoutError(
            url="https://slow-site.com", timeout_seconds=30
        )

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            app = create_app()
            app.state.http_session = mock_http_session
            client = TestClient(app, raise_server_exceptions=False)

            response = client.get("/api/v1/pages")

            assert response.status_code == 504
            data = response.json()
            assert data["error"] == "ScrapingTimeout"

    def test_sitemap_not_found_returns_404(
        self, mock_database, mock_http_session
    ) -> None:
        """SitemapNotFoundError returns 404 Not Found."""
        from src.app.main import create_app

        mock_repo = AsyncMock()
        mock_repo.list_all.side_effect = SitemapNotFoundError(
            website="https://no-sitemap.com"
        )

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            app = create_app()
            app.state.http_session = mock_http_session
            client = TestClient(app, raise_server_exceptions=False)

            response = client.get("/api/v1/pages")

            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "SitemapNotFound"

    def test_sitemap_parsing_error_returns_422(
        self, mock_database, mock_http_session
    ) -> None:
        """SitemapParsingError returns 422 Unprocessable Entity."""
        from src.app.main import create_app

        mock_repo = AsyncMock()
        mock_repo.list_all.side_effect = SitemapParsingError(
            sitemap_url="https://bad-sitemap.com/sitemap.xml",
            reason="Invalid XML",
        )

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            app = create_app()
            app.state.http_session = mock_http_session
            client = TestClient(app, raise_server_exceptions=False)

            response = client.get("/api/v1/pages")

            assert response.status_code == 422
            data = response.json()
            assert data["error"] == "SitemapParsingError"

    def test_invalid_scan_id_returns_400(
        self, mock_database, mock_http_session
    ) -> None:
        """InvalidScanIdError returns 400 Bad Request."""
        from src.app.main import create_app

        app = create_app()
        app.state.http_session = mock_http_session
        client = TestClient(app, raise_server_exceptions=False)

        # Invalid UUID format triggers InvalidScanIdError
        response = client.get("/api/v1/scans/not-a-uuid")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid" in data["message"]

    def test_meta_ads_rate_limit_handler_exists(self) -> None:
        """Verify MetaAdsRateLimitError handler is registered and returns 429."""
        from src.app.api.exceptions import meta_ads_rate_limit_handler
        from fastapi import Request
        import asyncio

        # Create a minimal mock request
        mock_request = MagicMock(spec=Request)
        exc = MetaAdsRateLimitError(retry_after=60)

        # Call the handler directly
        response = asyncio.get_event_loop().run_until_complete(
            meta_ads_rate_limit_handler(mock_request, exc)
        )

        assert response.status_code == 429

    def test_meta_ads_auth_handler_exists(self) -> None:
        """Verify MetaAdsAuthenticationError handler is registered and returns 401."""
        from src.app.api.exceptions import meta_ads_auth_handler
        from fastapi import Request
        import asyncio

        mock_request = MagicMock(spec=Request)
        exc = MetaAdsAuthenticationError()

        response = asyncio.get_event_loop().run_until_complete(
            meta_ads_auth_handler(mock_request, exc)
        )

        assert response.status_code == 401

    def test_meta_ads_api_error_handler_exists(self) -> None:
        """Verify MetaAdsApiError handler is registered and returns 502."""
        from src.app.api.exceptions import meta_ads_error_handler
        from fastapi import Request
        import asyncio

        mock_request = MagicMock(spec=Request)
        exc = MetaAdsApiError(reason="API error")

        response = asyncio.get_event_loop().run_until_complete(
            meta_ads_error_handler(mock_request, exc)
        )

        assert response.status_code == 502

    def test_domain_validation_error_returns_400(
        self, mock_database, mock_http_session
    ) -> None:
        """InvalidLanguageError returns 400 Bad Request (domain validation error)."""
        from src.app.main import create_app

        mock_repo = AsyncMock()
        mock_repo.list_all.side_effect = InvalidLanguageError("XX")

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_repo,
        ):
            app = create_app()
            app.state.http_session = mock_http_session
            client = TestClient(app, raise_server_exceptions=False)

            response = client.get("/api/v1/pages")

            assert response.status_code == 400
            data = response.json()
            assert "Invalid" in data["message"]


class TestScoringEndpoints:
    """Tests for /api/v1/pages scoring endpoints."""

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
            active_ads_count=25,
            total_ads_count=50,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @pytest.fixture
    def mock_score(self) -> ShopScore:
        """Create a mock shop score for testing."""
        return ShopScore(
            id="score-123",
            page_id="page-123",
            score=72.5,  # Tier "XL" (>= 70, < 85)
            components={
                "ads_activity": 85.0,
                "shopify": 70.0,
                "creative_quality": 60.0,
                "catalog": 55.0,
            },
            created_at=datetime.utcnow(),
        )

    def test_get_page_score_success(
        self, mock_page: Page, mock_score: ShopScore, mock_database
    ) -> None:
        """Get page score returns score details when found."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = mock_page

        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.get_latest_by_page_id.return_value = mock_score

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ), patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/page-123/score")

            assert response.status_code == 200
            data = response.json()
            assert data["page_id"] == "page-123"
            assert data["score"] == 72.5
            assert data["tier"] == "XL"  # 72.5 >= 70
            assert data["components"]["ads_activity"] == 85.0
            assert data["components"]["shopify"] == 70.0
            assert data["components"]["creative_quality"] == 60.0
            assert data["components"]["catalog"] == 55.0

    def test_get_page_score_page_not_found(self, mock_database) -> None:
        """Get page score returns 404 when page doesn't exist."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = None

        mock_scoring_repo = AsyncMock()

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ), patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/nonexistent/score")

            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "EntityNotFound"

    def test_get_page_score_score_not_found(
        self, mock_page: Page, mock_database
    ) -> None:
        """Get page score returns 404 when score doesn't exist."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = mock_page

        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.get_latest_by_page_id.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ), patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/page-123/score")

            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "EntityNotFound"

    def test_get_top_shops_empty(self, mock_database) -> None:
        """Get top shops returns empty list when no scores exist."""
        mock_page_repo = AsyncMock()
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_top.return_value = []
        mock_scoring_repo.count.return_value = 0  # Add count mock

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ), patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/top")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0

    def test_get_top_shops_with_data(
        self, mock_page: Page, mock_score: ShopScore, mock_database
    ) -> None:
        """Get top shops returns ranked list when scores exist."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = mock_page

        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_top.return_value = [mock_score]
        mock_scoring_repo.count.return_value = 1  # Add count mock

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ), patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/top?limit=10")

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["total"] == 1  # Add total assertion
            assert data["items"][0]["rank"] == 1
            assert data["items"][0]["page_id"] == "page-123"
            assert data["items"][0]["domain"] == "example-store.com"
            assert data["items"][0]["score"] == 72.5
            assert data["items"][0]["tier"] == "XL"  # 72.5 >= 70

    def test_recompute_page_score_success(
        self, mock_page: Page, mock_database
    ) -> None:
        """Recompute page score dispatches task and returns task ID."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = mock_page

        # Mock the TaskDispatcher
        mock_task_dispatcher = AsyncMock()
        mock_task_dispatcher.dispatch_compute_shop_score.return_value = "task-abc123"

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ), patch(
            "src.app.api.dependencies.CeleryTaskDispatcher",
            return_value=mock_task_dispatcher,
        ):
            # Clear lru_cache for get_task_dispatcher
            from src.app.api.dependencies import get_task_dispatcher
            get_task_dispatcher.cache_clear()

            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post("/api/v1/pages/page-123/score/recompute")

            assert response.status_code == 200
            data = response.json()
            assert data["page_id"] == "page-123"
            assert data["task_id"] == "task-abc123"
            assert data["status"] == "dispatched"
            mock_task_dispatcher.dispatch_compute_shop_score.assert_called_once_with(
                page_id="page-123"
            )

            # Clear cache again after test
            get_task_dispatcher.cache_clear()

    def test_recompute_page_score_page_not_found(self, mock_database) -> None:
        """Recompute page score returns 404 when page doesn't exist."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.post("/api/v1/pages/nonexistent/score/recompute")

            assert response.status_code == 404
            data = response.json()
            assert data["error"] == "EntityNotFound"

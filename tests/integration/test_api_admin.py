"""Integration tests for admin API endpoints.

Tests include authentication handling via X-Admin-Api-Key header.
"""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.app.api.dependencies import (
    get_app_settings,
    get_keyword_run_repository,
    get_page_repository,
    get_scan_repository,
)
from src.app.core.domain.entities.keyword_run import KeywordRun
from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.scan import Scan, ScanType
from src.app.core.domain.value_objects import Country, Url
from src.app.main import app


@pytest.fixture
def mock_page_repo() -> AsyncMock:
    """Create a mock page repository."""
    return AsyncMock()


@pytest.fixture
def mock_keyword_run_repo() -> AsyncMock:
    """Create a mock keyword run repository."""
    return AsyncMock()


@pytest.fixture
def mock_scan_repo() -> AsyncMock:
    """Create a mock scan repository."""
    return AsyncMock()


@pytest.fixture
def mock_settings_no_auth() -> MagicMock:
    """Create mock settings with no admin auth configured."""
    settings = MagicMock()
    settings.security.admin_api_key = None
    return settings


@pytest.fixture
def mock_settings_with_auth() -> MagicMock:
    """Create mock settings with admin auth configured."""
    settings = MagicMock()
    settings.security.admin_api_key = "test-admin-key"
    return settings


@pytest.fixture
def client(
    mock_page_repo: AsyncMock,
    mock_keyword_run_repo: AsyncMock,
    mock_scan_repo: AsyncMock,
    mock_settings_no_auth: MagicMock,
) -> Generator[TestClient, None, None]:
    """Create a test client with mocked dependencies (no auth required)."""
    app.dependency_overrides[get_page_repository] = lambda: mock_page_repo
    app.dependency_overrides[get_keyword_run_repository] = lambda: mock_keyword_run_repo
    app.dependency_overrides[get_scan_repository] = lambda: mock_scan_repo
    app.dependency_overrides[get_app_settings] = lambda: mock_settings_no_auth

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def client_with_auth(
    mock_page_repo: AsyncMock,
    mock_keyword_run_repo: AsyncMock,
    mock_scan_repo: AsyncMock,
    mock_settings_with_auth: MagicMock,
) -> Generator[TestClient, None, None]:
    """Create a test client with admin auth required."""
    app.dependency_overrides[get_page_repository] = lambda: mock_page_repo
    app.dependency_overrides[get_keyword_run_repository] = lambda: mock_keyword_run_repo
    app.dependency_overrides[get_scan_repository] = lambda: mock_scan_repo
    app.dependency_overrides[get_app_settings] = lambda: mock_settings_with_auth

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def sample_page() -> Page:
    """Create a sample page entity."""
    return Page.create(
        id="test-page-id",
        url=Url("https://test-store.myshopify.com"),
        country=Country("US"),
    )


@pytest.fixture
def sample_keyword_run() -> KeywordRun:
    """Create a sample keyword run entity."""
    return KeywordRun.create(
        keyword="dropshipping",
        country=Country("US"),
    )


@pytest.fixture
def sample_scan() -> Scan:
    """Create a sample scan entity."""
    return Scan.create(
        page_id="test-page-id",
        scan_type=ScanType.FULL,
    )


class TestAdminPagesEndpoint:
    """Tests for GET /api/v1/admin/pages/active endpoint."""

    def test_list_active_pages_empty(
        self, client: TestClient, mock_page_repo: AsyncMock
    ) -> None:
        """Returns empty list when no pages exist."""
        mock_page_repo.list_all.return_value = []

        response = client.get("/api/v1/admin/pages/active")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_active_pages_with_data(
        self, client: TestClient, mock_page_repo: AsyncMock, sample_page: Page
    ) -> None:
        """Returns pages when data exists."""
        mock_page_repo.list_all.return_value = [sample_page]

        response = client.get("/api/v1/admin/pages/active")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["page_id"] == sample_page.id

    def test_list_active_pages_with_country_filter(
        self, client: TestClient, mock_page_repo: AsyncMock, sample_page: Page
    ) -> None:
        """Filters pages by country."""
        mock_page_repo.list_all.return_value = [sample_page]

        response = client.get("/api/v1/admin/pages/active?country=US")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_list_active_pages_filter_excludes_non_matching(
        self, client: TestClient, mock_page_repo: AsyncMock, sample_page: Page
    ) -> None:
        """Filters out pages that don't match country."""
        mock_page_repo.list_all.return_value = [sample_page]

        response = client.get("/api/v1/admin/pages/active?country=FR")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    def test_list_active_pages_with_pagination(
        self, client: TestClient, mock_page_repo: AsyncMock
    ) -> None:
        """Respects pagination parameters."""
        mock_page_repo.list_all.return_value = []

        response = client.get("/api/v1/admin/pages/active?offset=10&limit=25")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 10
        assert data["limit"] == 25


class TestAdminKeywordsEndpoint:
    """Tests for GET /api/v1/admin/keywords/recent endpoint."""

    def test_list_recent_keywords_empty(
        self, client: TestClient, mock_keyword_run_repo: AsyncMock
    ) -> None:
        """Returns empty list when no keyword runs exist."""
        mock_keyword_run_repo.list_recent.return_value = []

        response = client.get("/api/v1/admin/keywords/recent")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_recent_keywords_with_data(
        self,
        client: TestClient,
        mock_keyword_run_repo: AsyncMock,
        sample_keyword_run: KeywordRun,
    ) -> None:
        """Returns keyword runs when data exists."""
        mock_keyword_run_repo.list_recent.return_value = [sample_keyword_run]

        response = client.get("/api/v1/admin/keywords/recent")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["keyword"] == sample_keyword_run.keyword

    def test_list_recent_keywords_with_limit(
        self, client: TestClient, mock_keyword_run_repo: AsyncMock
    ) -> None:
        """Respects limit parameter."""
        mock_keyword_run_repo.list_recent.return_value = []

        response = client.get("/api/v1/admin/keywords/recent?limit=10")

        assert response.status_code == 200
        mock_keyword_run_repo.list_recent.assert_called_once_with(limit=10)


class TestAdminScansEndpoint:
    """Tests for GET /api/v1/admin/scans endpoint."""

    def test_list_scans_empty(
        self, client: TestClient, mock_scan_repo: AsyncMock
    ) -> None:
        """Returns empty list when no scans exist."""
        mock_scan_repo.list_scans.return_value = []

        response = client.get("/api/v1/admin/scans")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_scans_with_data(
        self, client: TestClient, mock_scan_repo: AsyncMock, sample_scan: Scan
    ) -> None:
        """Returns scans when data exists."""
        mock_scan_repo.list_scans.return_value = [sample_scan]

        response = client.get("/api/v1/admin/scans")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(sample_scan.id)

    def test_list_scans_with_status_filter(
        self, client: TestClient, mock_scan_repo: AsyncMock
    ) -> None:
        """Filters scans by status."""
        mock_scan_repo.list_scans.return_value = []

        response = client.get("/api/v1/admin/scans?status=completed")

        assert response.status_code == 200
        mock_scan_repo.list_scans.assert_called_once()

    def test_list_scans_with_pagination(
        self, client: TestClient, mock_scan_repo: AsyncMock
    ) -> None:
        """Respects pagination parameters."""
        mock_scan_repo.list_scans.return_value = []

        response = client.get("/api/v1/admin/scans?offset=10&limit=25")

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 10
        assert data["limit"] == 25


class TestAdminAuthentication:
    """Tests for admin API authentication."""

    def test_access_without_header_when_auth_required(
        self, client_with_auth: TestClient, mock_page_repo: AsyncMock
    ) -> None:
        """Returns 401 when no API key header is provided and auth is required."""
        mock_page_repo.list_all.return_value = []

        response = client_with_auth.get("/api/v1/admin/pages/active")

        assert response.status_code == 401
        assert "Missing" in response.json()["detail"]

    def test_access_with_wrong_key(
        self, client_with_auth: TestClient, mock_page_repo: AsyncMock
    ) -> None:
        """Returns 401 when wrong API key is provided."""
        mock_page_repo.list_all.return_value = []

        response = client_with_auth.get(
            "/api/v1/admin/pages/active",
            headers={"X-Admin-Api-Key": "wrong-key"},
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    def test_access_with_correct_key(
        self, client_with_auth: TestClient, mock_page_repo: AsyncMock
    ) -> None:
        """Returns 200 when correct API key is provided."""
        mock_page_repo.list_all.return_value = []

        response = client_with_auth.get(
            "/api/v1/admin/pages/active",
            headers={"X-Admin-Api-Key": "test-admin-key"},
        )

        assert response.status_code == 200

    def test_access_without_header_when_no_auth_configured(
        self, client: TestClient, mock_page_repo: AsyncMock
    ) -> None:
        """Returns 200 when no auth is configured (dev mode)."""
        mock_page_repo.list_all.return_value = []

        response = client.get("/api/v1/admin/pages/active")

        assert response.status_code == 200

    def test_keywords_endpoint_requires_auth(
        self, client_with_auth: TestClient, mock_keyword_run_repo: AsyncMock
    ) -> None:
        """Keywords endpoint also requires auth."""
        mock_keyword_run_repo.list_recent.return_value = []

        # Without header
        response = client_with_auth.get("/api/v1/admin/keywords/recent")
        assert response.status_code == 401

        # With correct header
        response = client_with_auth.get(
            "/api/v1/admin/keywords/recent",
            headers={"X-Admin-Api-Key": "test-admin-key"},
        )
        assert response.status_code == 200

    def test_scans_endpoint_requires_auth(
        self, client_with_auth: TestClient, mock_scan_repo: AsyncMock
    ) -> None:
        """Scans endpoint also requires auth."""
        mock_scan_repo.list_scans.return_value = []

        # Without header
        response = client_with_auth.get("/api/v1/admin/scans")
        assert response.status_code == 401

        # With correct header
        response = client_with_auth.get(
            "/api/v1/admin/scans",
            headers={"X-Admin-Api-Key": "test-admin-key"},
        )
        assert response.status_code == 200

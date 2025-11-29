"""Integration tests for /alerts API endpoints.

Tests for the alerts API endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.app.core.domain.entities.alert import Alert


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


class TestAlertEndpoints:
    """Tests for alert API endpoints."""

    @pytest.fixture
    def sample_alerts(self) -> list[Alert]:
        """Create sample alerts for testing."""
        return [
            Alert(
                id="alert-001",
                page_id="page-001",
                type="SCORE_JUMP",
                message="Score jumped from 45.0 to 72.0 (+27.0)",
                severity="warning",
                old_score=45.0,
                new_score=72.0,
                old_tier=None,
                new_tier=None,
                created_at=datetime(2024, 3, 20, 15, 45, 0),
            ),
            Alert(
                id="alert-002",
                page_id="page-001",
                type="TIER_UP",
                message="Tier upgraded from M to L",
                severity="info",
                old_score=None,
                new_score=None,
                old_tier="M",
                new_tier="L",
                created_at=datetime(2024, 3, 20, 15, 44, 0),
            ),
            Alert(
                id="alert-003",
                page_id="page-001",
                type="NEW_ADS_BOOST",
                message="Ads count increased from 10 to 25 (+15)",
                severity="warning",
                old_score=None,
                new_score=None,
                old_tier=None,
                new_tier=None,
                created_at=datetime(2024, 3, 20, 15, 43, 0),
            ),
        ]

    def test_list_alerts_for_page(
        self, mock_database, sample_alerts: list[Alert]
    ) -> None:
        """GET /alerts/{page_id} returns alerts for the page."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = sample_alerts

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert data["count"] == 3
            assert len(data["items"]) == 3

            # Verify first alert structure
            first_alert = data["items"][0]
            assert first_alert["id"] == "alert-001"
            assert first_alert["page_id"] == "page-001"
            assert first_alert["type"] == "SCORE_JUMP"
            assert first_alert["message"] == "Score jumped from 45.0 to 72.0 (+27.0)"
            assert first_alert["severity"] == "warning"
            assert first_alert["old_score"] == 45.0
            assert first_alert["new_score"] == 72.0

    def test_list_alerts_for_page_empty(self, mock_database) -> None:
        """GET /alerts/{page_id} returns empty list when no alerts exist."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-nonexistent")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["count"] == 0

    def test_list_alerts_for_page_with_pagination(self, mock_database) -> None:
        """GET /alerts/{page_id} respects pagination parameters."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001?limit=25&offset=10")

            assert response.status_code == 200
            mock_alert_repo.list_by_page.assert_called_once_with(
                page_id="page-001",
                limit=25,
                offset=10,
            )

    def test_list_alerts_for_page_validation_limit(self, mock_database) -> None:
        """GET /alerts/{page_id} validates limit parameter."""
        from src.app.main import create_app

        app = create_app()
        client = TestClient(app)

        # Limit too high
        response = client.get("/api/v1/alerts/page-001?limit=500")
        assert response.status_code == 422

        # Limit too low
        response = client.get("/api/v1/alerts/page-001?limit=0")
        assert response.status_code == 422

    def test_list_recent_alerts(
        self, mock_database, sample_alerts: list[Alert]
    ) -> None:
        """GET /alerts returns recent alerts across all pages."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_recent.return_value = sample_alerts

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts")

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "count" in data
            assert data["count"] == 3
            assert len(data["items"]) == 3

    def test_list_recent_alerts_empty(self, mock_database) -> None:
        """GET /alerts returns empty list when no alerts exist."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_recent.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["count"] == 0

    def test_list_recent_alerts_with_limit(self, mock_database) -> None:
        """GET /alerts respects limit parameter."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_recent.return_value = []

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts?limit=50")

            assert response.status_code == 200
            mock_alert_repo.list_recent.assert_called_once_with(limit=50)


class TestAlertResponseSchema:
    """Tests for alert API response schemas."""

    @pytest.fixture
    def sample_alert_score_change(self) -> Alert:
        """Create a sample score change alert for testing."""
        return Alert(
            id="alert-001",
            page_id="page-001",
            type="SCORE_JUMP",
            message="Score jumped from 45.0 to 72.0 (+27.0)",
            severity="warning",
            old_score=45.0,
            new_score=72.0,
            old_tier=None,
            new_tier=None,
            created_at=datetime(2024, 3, 20, 15, 45, 0),
        )

    @pytest.fixture
    def sample_alert_tier_change(self) -> Alert:
        """Create a sample tier change alert for testing."""
        return Alert(
            id="alert-002",
            page_id="page-001",
            type="TIER_UP",
            message="Tier upgraded from M to L",
            severity="info",
            old_score=None,
            new_score=None,
            old_tier="M",
            new_tier="L",
            created_at=datetime(2024, 3, 20, 15, 44, 0),
        )

    def test_alert_response_structure(
        self, mock_database, sample_alert_score_change: Alert
    ) -> None:
        """Alert response contains all expected fields."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = [sample_alert_score_change]

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001")

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1

            alert = data["items"][0]

            # Verify all expected fields are present
            assert "id" in alert
            assert "page_id" in alert
            assert "type" in alert
            assert "message" in alert
            assert "severity" in alert
            assert "old_score" in alert
            assert "new_score" in alert
            assert "old_tier" in alert
            assert "new_tier" in alert
            assert "created_at" in alert

            # Verify field types
            assert isinstance(alert["id"], str)
            assert isinstance(alert["page_id"], str)
            assert isinstance(alert["type"], str)
            assert isinstance(alert["message"], str)
            assert isinstance(alert["severity"], str)
            assert alert["old_score"] is None or isinstance(alert["old_score"], float)
            assert alert["new_score"] is None or isinstance(alert["new_score"], float)
            assert alert["old_tier"] is None or isinstance(alert["old_tier"], str)
            assert alert["new_tier"] is None or isinstance(alert["new_tier"], str)
            assert isinstance(alert["created_at"], str)  # ISO format datetime

    def test_alert_score_change_fields(
        self, mock_database, sample_alert_score_change: Alert
    ) -> None:
        """Score change alerts have score fields populated."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = [sample_alert_score_change]

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001")

            assert response.status_code == 200
            alert = response.json()["items"][0]

            assert alert["type"] == "SCORE_JUMP"
            assert alert["old_score"] == 45.0
            assert alert["new_score"] == 72.0
            assert alert["old_tier"] is None
            assert alert["new_tier"] is None

    def test_alert_tier_change_fields(
        self, mock_database, sample_alert_tier_change: Alert
    ) -> None:
        """Tier change alerts have tier fields populated."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = [sample_alert_tier_change]

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001")

            assert response.status_code == 200
            alert = response.json()["items"][0]

            assert alert["type"] == "TIER_UP"
            assert alert["old_score"] is None
            assert alert["new_score"] is None
            assert alert["old_tier"] == "M"
            assert alert["new_tier"] == "L"


class TestAlertListResponseSchema:
    """Tests for alert list response schema."""

    @pytest.fixture
    def multiple_alerts(self) -> list[Alert]:
        """Create multiple alerts for testing."""
        return [
            Alert(
                id=f"alert-{i:03d}",
                page_id="page-001",
                type="SCORE_JUMP" if i % 2 == 0 else "TIER_UP",
                message=f"Alert message {i}",
                severity="warning" if i % 2 == 0 else "info",
                old_score=float(i * 10) if i % 2 == 0 else None,
                new_score=float(i * 10 + 15) if i % 2 == 0 else None,
                old_tier="S" if i % 2 != 0 else None,
                new_tier="M" if i % 2 != 0 else None,
                created_at=datetime(2024, 3, 20, 15, 45, i),
            )
            for i in range(5)
        ]

    def test_alert_list_response_structure(
        self, mock_database, multiple_alerts: list[Alert]
    ) -> None:
        """Alert list response contains items and count."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = multiple_alerts

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "items" in data
            assert "count" in data
            assert isinstance(data["items"], list)
            assert isinstance(data["count"], int)
            assert data["count"] == len(multiple_alerts)
            assert len(data["items"]) == len(multiple_alerts)

    def test_alert_list_count_matches_items(
        self, mock_database, multiple_alerts: list[Alert]
    ) -> None:
        """Alert list count matches number of items."""
        mock_alert_repo = AsyncMock()
        mock_alert_repo.list_by_page.return_value = multiple_alerts[:3]

        with patch(
            "src.app.api.dependencies.PostgresAlertRepository",
            return_value=mock_alert_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/alerts/page-001")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 3
            assert len(data["items"]) == 3

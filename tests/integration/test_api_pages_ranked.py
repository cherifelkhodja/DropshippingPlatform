"""Integration tests for /pages/ranked API endpoint.

Tests for the ranking API endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.app.core.domain.entities import Page, ShopScore, RankedShop, RankedShopsResult
from src.app.core.domain.value_objects import Url, Country, PageState, RankingCriteria


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


class TestRankedShopsEndpoint:
    """Tests for GET /api/v1/pages/ranked endpoint."""

    @pytest.fixture
    def mock_ranked_shops(self) -> list[RankedShop]:
        """Create mock ranked shops for testing."""
        return [
            RankedShop(
                page_id="page-001",
                score=92.0,
                tier="XXL",
                url="https://top-store.com",
                country="US",
                name="Top Store",
            ),
            RankedShop(
                page_id="page-002",
                score=78.5,
                tier="XL",
                url="https://great-shop.com",
                country="FR",
                name="Great Shop",
            ),
            RankedShop(
                page_id="page-003",
                score=55.0,
                tier="L",
                url="https://good-shop.com",
                country="US",
                name="Good Shop",
            ),
        ]

    def test_get_ranked_basic(
        self, mock_ranked_shops: list[RankedShop], mock_database
    ) -> None:
        """GET /pages/ranked returns items ordered by score with pagination info."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = mock_ranked_shops
        mock_scoring_repo.count_ranked.return_value = 3

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked")

            assert response.status_code == 200
            data = response.json()

            # Verify structure
            assert "items" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data

            # Verify items
            assert len(data["items"]) == 3
            assert data["total"] == 3
            assert data["limit"] == 50  # Default limit
            assert data["offset"] == 0

            # Verify ordering (highest score first)
            assert data["items"][0]["score"] == 92.0
            assert data["items"][0]["tier"] == "XXL"
            assert data["items"][1]["score"] == 78.5
            assert data["items"][2]["score"] == 55.0

            # Verify item structure
            item = data["items"][0]
            assert item["page_id"] == "page-001"
            assert item["url"] == "https://top-store.com"
            assert item["country"] == "US"
            assert item["name"] == "Top Store"

    def test_get_ranked_with_tier_filter(self, mock_database) -> None:
        """GET /pages/ranked with tier filter passes criteria correctly."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = [
            RankedShop(
                page_id="page-xxl",
                score=90.0,
                tier="XXL",
                url="https://xxl-shop.com",
                country="FR",
                name="XXL Shop",
            )
        ]
        mock_scoring_repo.count_ranked.return_value = 1

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked?tier=XXL")

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["tier"] == "XXL"

            # Verify the criteria was passed to the repository
            call_args = mock_scoring_repo.list_ranked.call_args[0][0]
            assert isinstance(call_args, RankingCriteria)
            assert call_args.tier == "XXL"

    def test_get_ranked_with_min_score_filter(self, mock_database) -> None:
        """GET /pages/ranked with min_score filter passes criteria correctly."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 0

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked?min_score=80")

            assert response.status_code == 200

            # Verify the criteria was passed to the repository
            call_args = mock_scoring_repo.list_ranked.call_args[0][0]
            assert isinstance(call_args, RankingCriteria)
            assert call_args.min_score == 80.0

    def test_get_ranked_with_country_filter(self, mock_database) -> None:
        """GET /pages/ranked with country filter passes criteria correctly."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 0

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked?country=FR")

            assert response.status_code == 200

            # Verify the criteria was passed to the repository
            call_args = mock_scoring_repo.list_ranked.call_args[0][0]
            assert isinstance(call_args, RankingCriteria)
            assert call_args.country == "FR"

    def test_get_ranked_with_all_filters(self, mock_database) -> None:
        """GET /pages/ranked with all filters combined."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 0

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/ranked?tier=XL&min_score=70&country=US&limit=25&offset=10"
            )

            assert response.status_code == 200

            # Verify all criteria were passed
            call_args = mock_scoring_repo.list_ranked.call_args[0][0]
            assert call_args.tier == "XL"
            assert call_args.min_score == 70.0
            assert call_args.country == "US"
            assert call_args.limit == 25
            assert call_args.offset == 10

    def test_get_ranked_empty_result(self, mock_database) -> None:
        """GET /pages/ranked returns empty list with correct structure."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 0

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0

    def test_get_ranked_pagination(self, mock_database) -> None:
        """GET /pages/ranked pagination parameters work correctly."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 100  # Total count

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked?limit=20&offset=40")

            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 20
            assert data["offset"] == 40
            assert data["total"] == 100

    def test_get_ranked_invalid_tier_rejected(self, mock_database) -> None:
        """GET /pages/ranked rejects invalid tier values."""
        from src.app.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/pages/ranked?tier=INVALID")

        assert response.status_code == 422  # Validation error

    def test_get_ranked_response_schema(
        self, mock_ranked_shops: list[RankedShop], mock_database
    ) -> None:
        """GET /pages/ranked response conforms to expected schema."""
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = mock_ranked_shops[:1]
        mock_scoring_repo.count_ranked.return_value = 1

        with patch(
            "src.app.api.dependencies.PostgresScoringRepository",
            return_value=mock_scoring_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/ranked")

            assert response.status_code == 200
            data = response.json()

            # Verify top-level structure
            assert isinstance(data["items"], list)
            assert isinstance(data["total"], int)
            assert isinstance(data["limit"], int)
            assert isinstance(data["offset"], int)

            # Verify item structure
            item = data["items"][0]
            assert isinstance(item["page_id"], str)
            assert isinstance(item["score"], (int, float))
            assert isinstance(item["tier"], str)
            # These can be None
            assert item["url"] is None or isinstance(item["url"], str)
            assert item["country"] is None or isinstance(item["country"], str)
            assert item["name"] is None or isinstance(item["name"], str)


class TestTopShopsEndpointRefactored:
    """Tests for GET /api/v1/pages/top endpoint (refactored to use ranking use case)."""

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

    def test_top_uses_ranking_usecase(self, mock_page: Page, mock_database) -> None:
        """GET /pages/top uses the ranking use case internally."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = mock_page

        mock_scoring_repo = AsyncMock()
        # list_ranked is now called by the use case
        mock_scoring_repo.list_ranked.return_value = [
            RankedShop(
                page_id="page-123",
                score=75.0,
                tier="XL",
                url="https://example-store.com",
                country="US",
                name="example-store.com",
            )
        ]
        mock_scoring_repo.count_ranked.return_value = 1

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

            # Verify the ranking repository methods were called
            mock_scoring_repo.list_ranked.assert_called_once()
            mock_scoring_repo.count_ranked.assert_called_once()

            # Verify response structure (TopShopsResponse format)
            assert "items" in data
            assert "total" in data
            assert len(data["items"]) == 1
            assert data["items"][0]["rank"] == 1
            assert data["items"][0]["page_id"] == "page-123"
            assert data["items"][0]["domain"] == "example-store.com"
            assert data["items"][0]["score"] == 75.0
            assert data["items"][0]["tier"] == "XL"

    def test_top_returns_empty_list(self, mock_database) -> None:
        """GET /pages/top returns empty list when no scores exist."""
        mock_page_repo = AsyncMock()
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 0

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

    def test_top_respects_limit_offset(self, mock_database) -> None:
        """GET /pages/top passes limit and offset correctly."""
        mock_page_repo = AsyncMock()
        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = []
        mock_scoring_repo.count_ranked.return_value = 0

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

            response = client.get("/api/v1/pages/top?limit=25&offset=10")

            assert response.status_code == 200

            # Verify criteria passed to list_ranked
            call_args = mock_scoring_repo.list_ranked.call_args[0][0]
            assert call_args.limit == 25
            assert call_args.offset == 10
            # top endpoint doesn't use filters
            assert call_args.tier is None
            assert call_args.min_score is None
            assert call_args.country is None

    def test_top_and_ranked_consistency(self, mock_page: Page, mock_database) -> None:
        """GET /pages/top and /pages/ranked return consistent data."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = mock_page

        ranked_shop = RankedShop(
            page_id="page-123",
            score=85.0,
            tier="XXL",
            url="https://example-store.com",
            country="US",
            name="example-store.com",
        )

        mock_scoring_repo = AsyncMock()
        mock_scoring_repo.list_ranked.return_value = [ranked_shop]
        mock_scoring_repo.count_ranked.return_value = 1

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

            # Get data from both endpoints
            top_response = client.get("/api/v1/pages/top")
            ranked_response = client.get("/api/v1/pages/ranked")

            assert top_response.status_code == 200
            assert ranked_response.status_code == 200

            top_data = top_response.json()
            ranked_data = ranked_response.json()

            # Both should have same total and item count
            assert top_data["total"] == ranked_data["total"]
            assert len(top_data["items"]) == len(ranked_data["items"])

            # Same page_id and score
            assert top_data["items"][0]["page_id"] == ranked_data["items"][0]["page_id"]
            assert top_data["items"][0]["score"] == ranked_data["items"][0]["score"]
            assert top_data["items"][0]["tier"] == ranked_data["items"][0]["tier"]

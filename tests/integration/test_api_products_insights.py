"""Integration tests for product and product insights API endpoints.

Tests for the products API endpoints with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient

from src.app.core.domain.entities.product import Product
from src.app.core.domain.entities.ad import Ad, AdStatus
from src.app.core.domain.entities.product_insights import (
    ProductInsights,
    PageProductInsights,
    AdMatch,
    MatchStrength,
)
from src.app.core.domain import Url, Page, PageState, PageStatus
from src.app.core.usecases.build_product_insights import BuildProductInsightsResult


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


class TestProductEndpoints:
    """Tests for product API endpoints."""

    @pytest.fixture
    def sample_products(self) -> list[Product]:
        """Create sample products for testing."""
        return [
            Product.create(
                id="prod-001",
                page_id="page-001",
                handle="awesome-t-shirt",
                title="Awesome T-Shirt",
                url="https://store.com/products/awesome-t-shirt",
                price_min=29.99,
                price_max=34.99,
                currency="USD",
                available=True,
                tags=["clothing", "t-shirt"],
                vendor="TestBrand",
            ),
            Product.create(
                id="prod-002",
                page_id="page-001",
                handle="cool-hoodie",
                title="Cool Hoodie",
                url="https://store.com/products/cool-hoodie",
                price_min=59.99,
                available=True,
                tags=["clothing", "hoodie"],
                vendor="TestBrand",
            ),
        ]

    @pytest.fixture
    def sample_page(self) -> Page:
        """Create a sample page for testing."""
        page = Page.create(id="page-001", url=Url("https://store.com"))
        return Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.VERIFIED_SHOPIFY),
            is_shopify=True,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

    def test_get_product_by_id(
        self, mock_database, sample_products: list[Product]
    ) -> None:
        """GET /products/{product_id} returns product details."""
        mock_product_repo = AsyncMock()
        mock_product_repo.get_by_id.return_value = sample_products[0]

        with patch(
            "src.app.api.dependencies.PostgresProductRepository",
            return_value=mock_product_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/products/prod-001")

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == "prod-001"
            assert data["page_id"] == "page-001"
            assert data["handle"] == "awesome-t-shirt"
            assert data["title"] == "Awesome T-Shirt"
            assert data["price_min"] == 29.99
            assert data["price_max"] == 34.99
            assert data["available"] is True
            assert "clothing" in data["tags"]

    def test_get_product_not_found(self, mock_database) -> None:
        """GET /products/{product_id} returns 404 for non-existent product."""
        mock_product_repo = AsyncMock()
        mock_product_repo.get_by_id.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresProductRepository",
            return_value=mock_product_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/products/nonexistent")

            assert response.status_code == 404

    def test_list_page_products(
        self, mock_database, sample_products: list[Product], sample_page: Page
    ) -> None:
        """GET /pages/{page_id}/products returns paginated products."""
        mock_product_repo = AsyncMock()
        mock_product_repo.list_by_page.return_value = sample_products
        mock_product_repo.count_by_page.return_value = 2

        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = sample_page

        with patch(
            "src.app.api.dependencies.PostgresProductRepository",
            return_value=mock_product_repo,
        ), patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/page-001/products")

            assert response.status_code == 200
            data = response.json()

            assert "items" in data
            assert "total" in data
            assert data["total"] == 2
            assert len(data["items"]) == 2
            assert data["page_id"] == "page-001"

    def test_list_page_products_page_not_found(self, mock_database) -> None:
        """GET /pages/{page_id}/products returns 404 for non-existent page."""
        mock_page_repo = AsyncMock()
        mock_page_repo.get.return_value = None

        with patch(
            "src.app.api.dependencies.PostgresPageRepository",
            return_value=mock_page_repo,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/nonexistent/products")

            assert response.status_code == 404


class TestProductInsightsEndpoints:
    """Tests for product insights API endpoints."""

    @pytest.fixture
    def sample_products(self) -> list[Product]:
        """Create sample products for testing."""
        return [
            Product.create(
                id="prod-001",
                page_id="page-001",
                handle="awesome-t-shirt",
                title="Awesome T-Shirt",
                url="https://store.com/products/awesome-t-shirt",
                price_min=29.99,
                available=True,
            ),
            Product.create(
                id="prod-002",
                page_id="page-001",
                handle="cool-hoodie",
                title="Cool Hoodie",
                url="https://store.com/products/cool-hoodie",
                price_min=59.99,
                available=True,
            ),
        ]

    @pytest.fixture
    def sample_ads(self) -> list[Ad]:
        """Create sample ads for testing."""
        return [
            Ad(
                id="ad-001",
                page_id="page-001",
                meta_page_id="meta-1",
                meta_ad_id="meta-ad-1",
                title="Shop our T-Shirts!",
                body="Amazing quality",
                link_url=Url("https://store.com/products/awesome-t-shirt"),
                status=AdStatus.ACTIVE,
                first_seen_at=datetime(2024, 1, 1),
                last_seen_at=datetime(2024, 3, 15),
            ),
            Ad(
                id="ad-002",
                page_id="page-001",
                meta_page_id="meta-1",
                meta_ad_id="meta-ad-2",
                title="Hoodie Collection",
                body="Check out our cool-hoodie!",
                link_url=Url("https://store.com/collections/hoodies"),
                status=AdStatus.ACTIVE,
                first_seen_at=datetime(2024, 2, 1),
                last_seen_at=datetime(2024, 3, 20),
            ),
        ]

    @pytest.fixture
    def sample_page_insights(
        self, sample_products: list[Product], sample_ads: list[Ad]
    ) -> PageProductInsights:
        """Create sample page product insights for testing."""
        # Create ad matches
        ad_match_1 = AdMatch(
            ad=sample_ads[0],
            score=1.0,
            strength=MatchStrength.STRONG,
            reasons=["URL direct match"],
        )
        ad_match_2 = AdMatch(
            ad=sample_ads[1],
            score=0.7,
            strength=MatchStrength.MEDIUM,
            reasons=["Product handle in ad text"],
        )

        product_insights = [
            ProductInsights(
                product=sample_products[0],
                matched_ads=[ad_match_1],
                total_ads_analyzed=2,
                computed_at=datetime.utcnow(),
            ),
            ProductInsights(
                product=sample_products[1],
                matched_ads=[ad_match_2],
                total_ads_analyzed=2,
                computed_at=datetime.utcnow(),
            ),
        ]

        return PageProductInsights(
            page_id="page-001",
            product_insights=product_insights,
            total_products=2,
            total_ads=2,
            computed_at=datetime.utcnow(),
        )

    def test_get_page_product_insights(
        self, mock_database, sample_page_insights: PageProductInsights
    ) -> None:
        """GET /pages/{page_id}/products/insights returns insights."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = BuildProductInsightsResult(
            page_id="page-001",
            insights=sample_page_insights,
            products_analyzed=2,
            ads_analyzed=2,
            matches_found=2,
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/page-001/products/insights")

            assert response.status_code == 200
            data = response.json()

            # Verify summary
            assert "summary" in data
            summary = data["summary"]
            assert summary["page_id"] == "page-001"
            assert summary["products_count"] == 2
            assert summary["products_with_ads_count"] == 2
            assert "coverage_ratio" in summary
            assert "promotion_ratio" in summary

            # Verify items
            assert "items" in data
            assert len(data["items"]) == 2

            # Verify pagination fields
            assert "total" in data
            assert "limit" in data
            assert "offset" in data

    def test_get_page_product_insights_structure(
        self, mock_database, sample_page_insights: PageProductInsights
    ) -> None:
        """GET /pages/{page_id}/products/insights returns correct structure."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = BuildProductInsightsResult(
            page_id="page-001",
            insights=sample_page_insights,
            products_analyzed=2,
            ads_analyzed=2,
            matches_found=2,
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get("/api/v1/pages/page-001/products/insights")

            assert response.status_code == 200
            data = response.json()

            # Verify item structure
            item = data["items"][0]
            assert "product" in item
            assert "insights" in item

            # Verify product fields
            product = item["product"]
            assert "id" in product
            assert "handle" in product
            assert "title" in product

            # Verify insights fields
            insights = item["insights"]
            assert "ads_count" in insights
            assert "match_score" in insights
            assert "has_strong_match" in insights
            assert "is_promoted" in insights
            assert "matched_ads" in insights

    def test_get_page_product_insights_sort_by_ads_count(
        self, mock_database, sample_page_insights: PageProductInsights
    ) -> None:
        """GET /pages/{page_id}/products/insights sorts by ads_count."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = BuildProductInsightsResult(
            page_id="page-001",
            insights=sample_page_insights,
            products_analyzed=2,
            ads_analyzed=2,
            matches_found=2,
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/insights?sort_by=ads_count"
            )

            assert response.status_code == 200
            # Both products have 1 ad, so order may vary
            assert len(response.json()["items"]) == 2

    def test_get_page_product_insights_sort_by_match_score(
        self, mock_database, sample_page_insights: PageProductInsights
    ) -> None:
        """GET /pages/{page_id}/products/insights sorts by match_score."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = BuildProductInsightsResult(
            page_id="page-001",
            insights=sample_page_insights,
            products_analyzed=2,
            ads_analyzed=2,
            matches_found=2,
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/insights?sort_by=match_score"
            )

            assert response.status_code == 200
            items = response.json()["items"]
            assert len(items) == 2
            # First product should have higher score (1.0 vs 0.7)
            assert items[0]["insights"]["match_score"] >= items[1]["insights"]["match_score"]

    def test_get_page_product_insights_sort_by_last_seen_at(
        self, mock_database, sample_page_insights: PageProductInsights
    ) -> None:
        """GET /pages/{page_id}/products/insights sorts by last_seen_at."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = BuildProductInsightsResult(
            page_id="page-001",
            insights=sample_page_insights,
            products_analyzed=2,
            ads_analyzed=2,
            matches_found=2,
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/insights?sort_by=last_seen_at"
            )

            assert response.status_code == 200
            items = response.json()["items"]
            assert len(items) == 2

    def test_get_page_product_insights_pagination(
        self, mock_database, sample_page_insights: PageProductInsights
    ) -> None:
        """GET /pages/{page_id}/products/insights respects pagination."""
        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = BuildProductInsightsResult(
            page_id="page-001",
            insights=sample_page_insights,
            products_analyzed=2,
            ads_analyzed=2,
            matches_found=2,
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/insights?limit=1&offset=0"
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["limit"] == 1
            assert data["offset"] == 0
            assert data["total"] == 2

    def test_get_single_product_insights(
        self, mock_database, sample_products: list[Product], sample_ads: list[Ad]
    ) -> None:
        """GET /pages/{page_id}/products/{product_id}/insights returns single product insights."""
        ad_match = AdMatch(
            ad=sample_ads[0],
            score=1.0,
            strength=MatchStrength.STRONG,
            reasons=["URL direct match"],
        )
        product_insight = ProductInsights(
            product=sample_products[0],
            matched_ads=[ad_match],
            total_ads_analyzed=2,
            computed_at=datetime.utcnow(),
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute_for_product.return_value = product_insight

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/prod-001/insights"
            )

            assert response.status_code == 200
            data = response.json()

            # Verify structure
            assert "product" in data
            assert "insights" in data

            # Verify product
            assert data["product"]["id"] == "prod-001"
            assert data["product"]["handle"] == "awesome-t-shirt"

            # Verify insights
            assert data["insights"]["ads_count"] == 1
            assert data["insights"]["match_score"] == 1.0
            assert data["insights"]["has_strong_match"] is True

    def test_get_single_product_insights_not_found(self, mock_database) -> None:
        """GET /pages/{page_id}/products/{product_id}/insights returns 404."""
        from src.app.core.domain.errors import EntityNotFoundError

        mock_use_case = AsyncMock()
        mock_use_case.execute_for_product.side_effect = EntityNotFoundError(
            "Product not found", "prod-nonexistent"
        )

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/prod-nonexistent/insights"
            )

            assert response.status_code == 404


class TestProductInsightsResponseSchema:
    """Tests for product insights response schema validation."""

    @pytest.fixture
    def sample_product(self) -> Product:
        """Create a sample product."""
        return Product.create(
            id="prod-001",
            page_id="page-001",
            handle="test-product",
            title="Test Product",
            url="https://store.com/products/test-product",
            price_min=25.0,
            available=True,
        )

    @pytest.fixture
    def sample_ad(self) -> Ad:
        """Create a sample ad."""
        return Ad(
            id="ad-001",
            page_id="page-001",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            title="Ad Title",
            body="Ad Body",
            link_url=Url("https://store.com/products/test-product"),
            image_url=Url("https://cdn.example.com/ad-image.jpg"),
            status=AdStatus.ACTIVE,
            first_seen_at=datetime(2024, 1, 1),
            last_seen_at=datetime(2024, 3, 15),
        )

    def test_matched_ads_response_structure(
        self, mock_database, sample_product: Product, sample_ad: Ad
    ) -> None:
        """Matched ads in response have correct structure."""
        ad_match = AdMatch(
            ad=sample_ad,
            score=1.0,
            strength=MatchStrength.STRONG,
            reasons=["URL direct match", "Handle in URL"],
        )
        product_insight = ProductInsights(
            product=sample_product,
            matched_ads=[ad_match],
            total_ads_analyzed=1,
            computed_at=datetime.utcnow(),
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute_for_product.return_value = product_insight

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/prod-001/insights"
            )

            assert response.status_code == 200
            data = response.json()

            matched_ads = data["insights"]["matched_ads"]
            assert len(matched_ads) == 1

            ad_response = matched_ads[0]
            assert "ad_id" in ad_response
            assert "score" in ad_response
            assert "strength" in ad_response
            assert "reasons" in ad_response
            assert "ad_title" in ad_response
            assert "ad_link_url" in ad_response
            assert "ad_is_active" in ad_response

            assert ad_response["ad_id"] == "ad-001"
            assert ad_response["score"] == 1.0
            assert ad_response["strength"] == "strong"
            assert "URL direct match" in ad_response["reasons"]
            assert ad_response["ad_is_active"] is True

    def test_insights_data_fields(
        self, mock_database, sample_product: Product, sample_ad: Ad
    ) -> None:
        """ProductInsightsData contains all expected fields."""
        ad_match = AdMatch(
            ad=sample_ad,
            score=0.85,
            strength=MatchStrength.STRONG,
            reasons=["URL direct match"],
        )
        product_insight = ProductInsights(
            product=sample_product,
            matched_ads=[ad_match],
            total_ads_analyzed=5,
            computed_at=datetime.utcnow(),
        )

        mock_use_case = AsyncMock()
        mock_use_case.execute_for_product.return_value = product_insight

        with patch(
            "src.app.api.dependencies.get_build_product_insights_use_case",
            return_value=mock_use_case,
        ):
            from src.app.main import create_app

            app = create_app()
            client = TestClient(app)

            response = client.get(
                "/api/v1/pages/page-001/products/prod-001/insights"
            )

            assert response.status_code == 200
            insights = response.json()["insights"]

            # Verify all expected fields
            assert insights["ads_count"] == 1
            assert insights["distinct_creatives_count"] >= 1
            assert insights["match_score"] == 0.85
            assert insights["has_strong_match"] is True
            assert insights["is_promoted"] is True
            assert "strong_matches_count" in insights
            assert "medium_matches_count" in insights
            assert "weak_matches_count" in insights
            assert "first_seen_at" in insights
            assert "last_seen_at" in insights
            assert "match_reasons" in insights

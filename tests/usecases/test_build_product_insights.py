"""Tests for BuildProductInsightsForPageUseCase.

Tests the product-ad matching and insights building functionality.
"""

import pytest

from src.app.core.domain import (
    Page,
    Ad,
    AdStatus,
    Url,
    PageState,
    PageStatus,
    EntityNotFoundError,
)
from src.app.core.domain.entities.product import Product
from src.app.core.domain.entities.product_insights import MatchStrength
from src.app.core.usecases import BuildProductInsightsForPageUseCase
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeProductRepository,
    FakeAdsRepository,
)


class TestBuildProductInsightsForPageUseCase:
    """Tests for BuildProductInsightsForPageUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_logger: FakeLoggingPort,
    ) -> BuildProductInsightsForPageUseCase:
        """Create use case with mocked dependencies."""
        return BuildProductInsightsForPageUseCase(
            page_repository=fake_page_repo,
            product_repository=fake_product_repo,
            ads_repository=fake_ads_repo,
            logger=fake_logger,
        )

    @pytest.fixture
    def shopify_page(self) -> Page:
        """Create a Shopify page for testing."""
        page = Page.create(id="page-1", url=Url("https://test-store.myshopify.com"))
        return Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.VERIFIED_SHOPIFY),
            is_shopify=True,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

    @pytest.fixture
    def sample_products(self) -> list[Product]:
        """Create sample products for testing."""
        return [
            Product.create(
                id="prod-1",
                page_id="page-1",
                handle="awesome-t-shirt",
                title="Awesome T-Shirt",
                url="https://test-store.myshopify.com/products/awesome-t-shirt",
                price_min=29.99,
                available=True,
                tags=["clothing", "t-shirt"],
                vendor="TestBrand",
            ),
            Product.create(
                id="prod-2",
                page_id="page-1",
                handle="cool-hoodie",
                title="Cool Hoodie",
                url="https://test-store.myshopify.com/products/cool-hoodie",
                price_min=59.99,
                available=True,
                tags=["clothing", "hoodie"],
                vendor="TestBrand",
            ),
            Product.create(
                id="prod-3",
                page_id="page-1",
                handle="trendy-cap",
                title="Trendy Cap",
                url="https://test-store.myshopify.com/products/trendy-cap",
                price_min=19.99,
                available=False,
                tags=["accessories", "cap"],
                vendor="TestBrand",
            ),
        ]

    @pytest.fixture
    def sample_ads_with_matches(self) -> list[Ad]:
        """Create sample ads that match products."""
        ads = []

        # Ad with URL match to awesome-t-shirt
        ad1 = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            status=AdStatus.ACTIVE,
        )
        ad1 = Ad(
            id=ad1.id,
            page_id=ad1.page_id,
            meta_page_id=ad1.meta_page_id,
            meta_ad_id=ad1.meta_ad_id,
            title="Shop our amazing T-Shirts!",
            body="Check out our awesome t-shirt collection",
            link_url=Url("https://test-store.myshopify.com/products/awesome-t-shirt"),
            status=AdStatus.ACTIVE,
            created_at=ad1.created_at,
            updated_at=ad1.updated_at,
        )
        ads.append(ad1)

        # Ad with handle in text (matches cool-hoodie)
        ad2 = Ad.create(
            id="ad-2",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-2",
            status=AdStatus.ACTIVE,
        )
        ad2 = Ad(
            id=ad2.id,
            page_id=ad2.page_id,
            meta_page_id=ad2.meta_page_id,
            meta_ad_id=ad2.meta_ad_id,
            title="Warm up with our cool-hoodie!",
            body="The best hoodie for cold days",
            link_url=Url("https://test-store.myshopify.com/collections/hoodies"),
            status=AdStatus.ACTIVE,
            created_at=ad2.created_at,
            updated_at=ad2.updated_at,
        )
        ads.append(ad2)

        # Ad with no specific product match
        ad3 = Ad.create(
            id="ad-3",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-3",
            status=AdStatus.ACTIVE,
        )
        ad3 = Ad(
            id=ad3.id,
            page_id=ad3.page_id,
            meta_page_id=ad3.meta_page_id,
            meta_ad_id=ad3.meta_ad_id,
            title="Visit our store today!",
            body="Amazing products at amazing prices",
            link_url=Url("https://test-store.myshopify.com"),
            status=AdStatus.ACTIVE,
            created_at=ad3.created_at,
            updated_at=ad3.updated_at,
        )
        ads.append(ad3)

        return ads

    @pytest.mark.asyncio
    async def test_build_insights_happy_path(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        shopify_page: Page,
        sample_products: list[Product],
        sample_ads_with_matches: list[Ad],
    ) -> None:
        """Test successful insights building with matches."""
        # Setup
        await fake_page_repo.save(shopify_page)
        await fake_product_repo.upsert_many(sample_products)
        await fake_ads_repo.save_many(sample_ads_with_matches)

        # Execute
        result = await use_case.execute(page_id="page-1")

        # Verify result
        assert result.page_id == "page-1"
        assert result.products_analyzed == 3
        assert result.ads_analyzed == 3
        assert result.matches_found >= 2  # At least URL and handle matches
        assert result.error is None

        # Verify insights structure
        insights = result.insights
        assert insights.page_id == "page-1"
        assert insights.total_products == 3
        assert insights.total_ads == 3
        assert insights.products_with_ads >= 2

    @pytest.mark.asyncio
    async def test_build_insights_page_not_found(
        self,
        use_case: BuildProductInsightsForPageUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(page_id="nonexistent")

        assert "Page not found" in str(exc_info.value)
        assert exc_info.value.value == "nonexistent"

    @pytest.mark.asyncio
    async def test_build_insights_no_products(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        shopify_page: Page,
    ) -> None:
        """Test handling when no products exist."""
        await fake_page_repo.save(shopify_page)

        result = await use_case.execute(page_id="page-1")

        assert result.page_id == "page-1"
        assert result.products_analyzed == 0
        assert result.ads_analyzed == 0
        assert result.matches_found == 0
        assert "No products found" in (result.error or "")

    @pytest.mark.asyncio
    async def test_build_insights_no_ads(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        shopify_page: Page,
        sample_products: list[Product],
    ) -> None:
        """Test handling when no ads exist."""
        await fake_page_repo.save(shopify_page)
        await fake_product_repo.upsert_many(sample_products)

        result = await use_case.execute(page_id="page-1")

        assert result.page_id == "page-1"
        assert result.products_analyzed == 3
        assert result.ads_analyzed == 0
        assert result.matches_found == 0
        assert "No ads found" in (result.error or "")

        # Products should still be in insights
        assert result.insights.total_products == 3
        assert result.insights.products_with_ads == 0

    @pytest.mark.asyncio
    async def test_url_match_creates_strong_match(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        shopify_page: Page,
    ) -> None:
        """Test that URL matching creates strong matches."""
        await fake_page_repo.save(shopify_page)

        # Create product
        product = Product.create(
            id="prod-url-test",
            page_id="page-1",
            handle="special-product",
            title="Special Product",
            url="https://test-store.myshopify.com/products/special-product",
        )
        await fake_product_repo.upsert_many([product])

        # Create ad with matching URL
        ad = Ad(
            id="ad-url-test",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-url",
            title="Buy our Special Product",
            body="Limited time offer",
            link_url=Url("https://test-store.myshopify.com/products/special-product"),
            status=AdStatus.ACTIVE,
        )
        await fake_ads_repo.save_many([ad])

        result = await use_case.execute(page_id="page-1")

        assert result.matches_found == 1

        # Get the product insight
        product_insight = result.insights.product_insights[0]
        assert len(product_insight.matched_ads) == 1
        assert product_insight.matched_ads[0].strength == MatchStrength.STRONG
        assert product_insight.has_strong_match is True

    @pytest.mark.asyncio
    async def test_handle_match_creates_medium_match(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        shopify_page: Page,
    ) -> None:
        """Test that handle in ad text creates medium matches."""
        await fake_page_repo.save(shopify_page)

        # Create product
        product = Product.create(
            id="prod-handle-test",
            page_id="page-1",
            handle="unique-watch",
            title="Unique Watch",
            url="https://test-store.myshopify.com/products/unique-watch",
        )
        await fake_product_repo.upsert_many([product])

        # Create ad with handle in text but different URL
        ad = Ad(
            id="ad-handle-test",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-handle",
            title="Check out our unique-watch collection!",
            body="The best watches in town",
            link_url=Url("https://test-store.myshopify.com/collections/watches"),
            status=AdStatus.ACTIVE,
        )
        await fake_ads_repo.save_many([ad])

        result = await use_case.execute(page_id="page-1")

        assert result.matches_found == 1

        product_insight = result.insights.product_insights[0]
        assert len(product_insight.matched_ads) == 1
        # Handle in text is a MEDIUM match (not STRONG because URL doesn't match)
        assert product_insight.matched_ads[0].strength == MatchStrength.MEDIUM

    @pytest.mark.asyncio
    async def test_no_match_when_no_similarity(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        shopify_page: Page,
    ) -> None:
        """Test that unrelated products and ads don't match."""
        await fake_page_repo.save(shopify_page)

        # Create product
        product = Product.create(
            id="prod-no-match",
            page_id="page-1",
            handle="blue-sneakers",
            title="Blue Running Sneakers",
            url="https://test-store.myshopify.com/products/blue-sneakers",
        )
        await fake_product_repo.upsert_many([product])

        # Create completely unrelated ad
        ad = Ad(
            id="ad-no-match",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-unrelated",
            title="Winter Jackets Sale!",
            body="Keep warm this season",
            link_url=Url("https://test-store.myshopify.com/collections/jackets"),
            status=AdStatus.ACTIVE,
        )
        await fake_ads_repo.save_many([ad])

        result = await use_case.execute(page_id="page-1")

        assert result.matches_found == 0

        product_insight = result.insights.product_insights[0]
        assert len(product_insight.matched_ads) == 0
        assert product_insight.is_promoted is False

    @pytest.mark.asyncio
    async def test_single_product_insights(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        shopify_page: Page,
        sample_products: list[Product],
        sample_ads_with_matches: list[Ad],
    ) -> None:
        """Test getting insights for a single product."""
        await fake_page_repo.save(shopify_page)
        await fake_product_repo.upsert_many(sample_products)
        await fake_ads_repo.save_many(sample_ads_with_matches)

        # Get insights for specific product
        product_insight = await use_case.execute_for_product(
            page_id="page-1",
            product_id="prod-1",  # awesome-t-shirt
        )

        assert product_insight.product.id == "prod-1"
        assert product_insight.total_ads_analyzed == 3
        # Should have at least the URL match from ad-1
        assert len(product_insight.matched_ads) >= 1

    @pytest.mark.asyncio
    async def test_single_product_not_found(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        shopify_page: Page,
    ) -> None:
        """Test error when single product not found."""
        await fake_page_repo.save(shopify_page)

        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute_for_product(
                page_id="page-1",
                product_id="nonexistent",
            )

        assert "Product not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_insights_aggregation(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        shopify_page: Page,
        sample_products: list[Product],
        sample_ads_with_matches: list[Ad],
    ) -> None:
        """Test that page-level aggregation is correct."""
        await fake_page_repo.save(shopify_page)
        await fake_product_repo.upsert_many(sample_products)
        await fake_ads_repo.save_many(sample_ads_with_matches)

        result = await use_case.execute(page_id="page-1")
        insights = result.insights

        # Test aggregation properties
        assert insights.coverage_ratio == insights.products_with_ads / insights.total_products

        # Get promoted products
        promoted = insights.get_promoted_products()
        assert insights.promoted_products_count == len(promoted)

        # Get top products by score
        top_products = insights.get_top_products_by_score(limit=2)
        assert len(top_products) <= 2

    @pytest.mark.asyncio
    async def test_logs_operations(
        self,
        use_case: BuildProductInsightsForPageUseCase,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_logger: FakeLoggingPort,
        shopify_page: Page,
        sample_products: list[Product],
        sample_ads_with_matches: list[Ad],
    ) -> None:
        """Test that operations are properly logged."""
        await fake_page_repo.save(shopify_page)
        await fake_product_repo.upsert_many(sample_products)
        await fake_ads_repo.save_many(sample_ads_with_matches)

        await use_case.execute(page_id="page-1")

        # Verify logs
        log_messages = [log["msg"] for log in fake_logger.logs]
        assert "Building product insights" in log_messages
        assert "Matching products to ads" in log_messages
        assert "Product insights built" in log_messages


class TestProductAdMatcher:
    """Tests for the product-ad matching service."""

    def test_normalize_text(self) -> None:
        """Test text normalization."""
        from src.app.core.domain.services.product_ad_matcher import normalize_text

        assert normalize_text("Hello World!") == "hello world"
        assert normalize_text("  Multiple   Spaces  ") == "multiple spaces"
        assert normalize_text("URL: https://example.com here") == "url here"
        assert normalize_text("") == ""

    def test_extract_handle_from_url(self) -> None:
        """Test handle extraction from URLs."""
        from src.app.core.domain.services.product_ad_matcher import extract_handle_from_url

        assert extract_handle_from_url(
            "https://store.com/products/awesome-product"
        ) == "awesome-product"
        assert extract_handle_from_url(
            "https://store.com/products/my-item?variant=123"
        ) == "my-item"
        assert extract_handle_from_url("") is None
        assert extract_handle_from_url(
            "https://store.com/collections/all"
        ) == "all"

    def test_text_similarity(self) -> None:
        """Test text similarity calculation."""
        from src.app.core.domain.services.product_ad_matcher import calculate_text_similarity

        # Identical strings
        assert calculate_text_similarity("hello", "hello") == 1.0

        # Empty strings
        assert calculate_text_similarity("", "") == 0.0
        assert calculate_text_similarity("hello", "") == 0.0

        # Similar strings
        similarity = calculate_text_similarity(
            "Awesome T-Shirt",
            "Amazing T-Shirt"
        )
        assert 0.5 < similarity < 1.0

    def test_url_match(self) -> None:
        """Test URL matching."""
        from src.app.core.domain.services.product_ad_matcher import check_url_match

        product = Product.create(
            id="p1",
            page_id="page-1",
            handle="test-product",
            title="Test Product",
            url="https://store.com/products/test-product",
        )

        # Matching URL
        ad_match = Ad(
            id="a1",
            page_id="page-1",
            meta_page_id="m1",
            meta_ad_id="ma1",
            link_url=Url("https://store.com/products/test-product"),
            status=AdStatus.ACTIVE,
        )
        is_match, score, reason = check_url_match(product, ad_match)
        assert is_match is True
        assert score >= 0.9
        assert "URL" in reason or "handle" in reason

        # Non-matching URL
        ad_no_match = Ad(
            id="a2",
            page_id="page-1",
            meta_page_id="m1",
            meta_ad_id="ma2",
            link_url=Url("https://store.com/collections/all"),
            status=AdStatus.ACTIVE,
        )
        is_match, score, reason = check_url_match(product, ad_no_match)
        assert is_match is False
        assert score == 0.0

    def test_handle_match(self) -> None:
        """Test handle matching in ad text."""
        from src.app.core.domain.services.product_ad_matcher import check_handle_match

        product = Product.create(
            id="p1",
            page_id="page-1",
            handle="cool-sneakers",
            title="Cool Sneakers",
            url="https://store.com/products/cool-sneakers",
        )

        # Handle in title
        ad_match = Ad(
            id="a1",
            page_id="page-1",
            meta_page_id="m1",
            meta_ad_id="ma1",
            title="Get our cool-sneakers today!",
            body="Best footwear",
            status=AdStatus.ACTIVE,
        )
        is_match, score, reason = check_handle_match(product, ad_match)
        assert is_match is True
        assert score > 0
        assert "handle" in reason.lower()

        # No handle match
        ad_no_match = Ad(
            id="a2",
            page_id="page-1",
            meta_page_id="m1",
            meta_ad_id="ma2",
            title="Winter coats sale",
            body="Stay warm",
            status=AdStatus.ACTIVE,
        )
        is_match, score, reason = check_handle_match(product, ad_no_match)
        assert is_match is False

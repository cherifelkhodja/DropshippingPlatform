"""Tests for SyncProductsForPageUseCase.

Tests the product synchronization use case with mocked ports.
"""

import pytest
from unittest.mock import AsyncMock

from src.app.core.domain import (
    Page,
    Url,
    Country,
    PageState,
    PageStatus,
    EntityNotFoundError,
)
from src.app.core.domain.entities.product import Product
from src.app.core.ports.product_extractor_port import ProductExtractionResult
from src.app.core.usecases import SyncProductsForPageUseCase, SyncProductsResult
from tests.conftest import FakeLoggingPort, FakePageRepository, FakeProductRepository


class TestSyncProductsForPageUseCase:
    """Tests for SyncProductsForPageUseCase."""

    @pytest.fixture
    def use_case(
        self,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        fake_logger: FakeLoggingPort,
    ) -> SyncProductsForPageUseCase:
        """Create use case with mocked dependencies."""
        return SyncProductsForPageUseCase(
            page_repository=fake_page_repo,
            product_repository=fake_product_repo,
            product_extractor=mock_product_extractor_port,
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
    def non_shopify_page(self) -> Page:
        """Create a non-Shopify page for testing."""
        return Page.create(id="page-2", url=Url("https://example.com"))

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
                price_max=34.99,
                currency="USD",
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
                price_max=59.99,
                currency="USD",
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

    @pytest.mark.asyncio
    async def test_sync_products_happy_path(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        shopify_page: Page,
        sample_products: list[Product],
    ) -> None:
        """Test successful product synchronization."""
        # Setup
        await fake_page_repo.save(shopify_page)
        mock_product_extractor_port.extract_products.return_value = ProductExtractionResult(
            products=sample_products,
            total_found=3,
            source="products.json",
            error=None,
        )

        # Execute
        result = await use_case.execute(page_id="page-1")

        # Verify result
        assert isinstance(result, SyncProductsResult)
        assert result.page_id == "page-1"
        assert result.products_synced == 3
        assert result.products_extracted == 3
        assert result.is_shopify is True
        assert result.source == "products.json"
        assert result.error is None

        # Verify ports were called
        mock_product_extractor_port.is_supported.assert_called_once_with(
            "https://test-store.myshopify.com"
        )
        mock_product_extractor_port.extract_products.assert_called_once_with(
            page_id="page-1",
            store_url="https://test-store.myshopify.com",
        )

        # Verify products were stored
        assert len(fake_product_repo.upsert_calls) == 1
        assert len(fake_product_repo.upsert_calls[0]) == 3
        stored_count = await fake_product_repo.count_by_page("page-1")
        assert stored_count == 3

    @pytest.mark.asyncio
    async def test_sync_products_page_not_found(
        self,
        use_case: SyncProductsForPageUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(page_id="nonexistent")

        # Check that error message contains expected information
        assert "Page not found" in str(exc_info.value)
        assert exc_info.value.value == "nonexistent"

    @pytest.mark.asyncio
    async def test_sync_products_non_shopify_page(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        non_shopify_page: Page,
    ) -> None:
        """Test that non-Shopify pages are skipped."""
        await fake_page_repo.save(non_shopify_page)

        result = await use_case.execute(page_id="page-2")

        # Should return early without calling extractor
        assert result.page_id == "page-2"
        assert result.products_synced == 0
        assert result.products_extracted == 0
        assert result.is_shopify is False
        assert "not a Shopify store" in (result.error or "")

        mock_product_extractor_port.is_supported.assert_not_called()
        mock_product_extractor_port.extract_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_products_extraction_not_supported(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        shopify_page: Page,
    ) -> None:
        """Test handling when product extraction is not supported."""
        await fake_page_repo.save(shopify_page)
        mock_product_extractor_port.is_supported.return_value = False

        result = await use_case.execute(page_id="page-1")

        assert result.page_id == "page-1"
        assert result.products_synced == 0
        assert result.is_shopify is True
        assert "not supported" in (result.error or "")

        mock_product_extractor_port.extract_products.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_products_no_products_found(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        shopify_page: Page,
    ) -> None:
        """Test handling when no products are found."""
        await fake_page_repo.save(shopify_page)
        mock_product_extractor_port.extract_products.return_value = ProductExtractionResult(
            products=[],
            total_found=0,
            source="products.json",
            error=None,
        )

        result = await use_case.execute(page_id="page-1")

        assert result.page_id == "page-1"
        assert result.products_synced == 0
        assert result.products_extracted == 0
        assert result.is_shopify is True
        assert "No products found" in (result.error or "")

        # Verify no upsert was called
        assert len(fake_product_repo.upsert_calls) == 0

    @pytest.mark.asyncio
    async def test_sync_products_with_partial_error(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        shopify_page: Page,
        sample_products: list[Product],
    ) -> None:
        """Test handling of partial extraction errors."""
        await fake_page_repo.save(shopify_page)

        # Only 2 products extracted due to pagination error
        mock_product_extractor_port.extract_products.return_value = ProductExtractionResult(
            products=sample_products[:2],
            total_found=2,
            source="products.json",
            error="Pagination stopped at page 2: timeout",
        )

        result = await use_case.execute(page_id="page-1")

        # Should still succeed with partial data
        assert result.products_synced == 2
        assert result.error == "Pagination stopped at page 2: timeout"

    @pytest.mark.asyncio
    async def test_sync_products_multiple_syncs(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_product_repo: FakeProductRepository,
        shopify_page: Page,
        sample_products: list[Product],
    ) -> None:
        """Test that multiple syncs properly upsert products."""
        await fake_page_repo.save(shopify_page)

        # First sync with 3 products
        mock_product_extractor_port.extract_products.return_value = ProductExtractionResult(
            products=sample_products,
            total_found=3,
            source="products.json",
        )

        result1 = await use_case.execute(page_id="page-1")
        assert result1.products_synced == 3

        # Second sync with updated products (1 new, 2 existing)
        new_product = Product.create(
            id="prod-4",
            page_id="page-1",
            handle="new-product",
            title="New Product",
            url="https://test-store.myshopify.com/products/new-product",
            price_min=99.99,
        )
        mock_product_extractor_port.extract_products.return_value = ProductExtractionResult(
            products=[sample_products[0], sample_products[1], new_product],
            total_found=3,
            source="products.json",
        )

        result2 = await use_case.execute(page_id="page-1")
        assert result2.products_synced == 3

        # Verify upsert was called twice
        assert len(fake_product_repo.upsert_calls) == 2

    @pytest.mark.asyncio
    async def test_sync_products_logs_operations(
        self,
        use_case: SyncProductsForPageUseCase,
        mock_product_extractor_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_logger: FakeLoggingPort,
        shopify_page: Page,
        sample_products: list[Product],
    ) -> None:
        """Test that sync operations are properly logged."""
        await fake_page_repo.save(shopify_page)
        mock_product_extractor_port.extract_products.return_value = ProductExtractionResult(
            products=sample_products,
            total_found=3,
            source="products.json",
        )

        await use_case.execute(page_id="page-1")

        # Verify logs
        log_messages = [log["msg"] for log in fake_logger.logs]
        assert "Starting product sync" in log_messages
        assert "Products extracted" in log_messages
        assert "Product sync completed" in log_messages

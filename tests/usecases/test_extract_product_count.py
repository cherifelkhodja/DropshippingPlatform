"""Tests for ExtractProductCountUseCase.

Tests the product count extraction use case with mocked ports.
"""

import pytest
from unittest.mock import AsyncMock

from src.app.core.domain import (
    Page,
    Url,
    Country,
    ProductCount,
    PageStatus,
    EntityNotFoundError,
    SitemapNotFoundError,
)
from src.app.core.usecases import ExtractProductCountUseCase, ExtractProductCountResult
from tests.conftest import FakeLoggingPort, FakePageRepository


class TestExtractProductCountUseCase:
    """Tests for ExtractProductCountUseCase."""

    @pytest.fixture
    def use_case(
        self,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_logger: FakeLoggingPort,
    ) -> ExtractProductCountUseCase:
        """Create use case with mocked dependencies."""
        return ExtractProductCountUseCase(
            sitemap_port=mock_sitemap_port,
            page_repository=fake_page_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_extract_product_count_happy_path(
        self,
        use_case: ExtractProductCountUseCase,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test successful product count extraction."""
        # Setup page
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        # Setup mock response
        mock_sitemap_port.get_sitemap_urls.return_value = [
            Url("https://example.com/sitemap.xml"),
            Url("https://example.com/sitemap_products.xml"),
        ]
        mock_sitemap_port.extract_product_count.return_value = ProductCount(150)

        # Execute
        result = await use_case.execute(
            page_id="page-1",
            website_url=Url("https://example.com"),
            country=Country("US"),
        )

        # Verify result
        assert isinstance(result, ExtractProductCountResult)
        assert result.page_id == "page-1"
        assert result.product_count == 150
        assert result.sitemaps_found == 2

        # Verify ports were called
        mock_sitemap_port.get_sitemap_urls.assert_called_once()
        mock_sitemap_port.extract_product_count.assert_called_once()

        # Verify page was updated
        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.product_count.value == 150

    @pytest.mark.asyncio
    async def test_extract_product_count_page_not_found(
        self,
        use_case: ExtractProductCountUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                page_id="nonexistent",
                website_url=Url("https://example.com"),
                country=Country("US"),
            )

    @pytest.mark.asyncio
    async def test_extract_product_count_no_sitemaps(
        self,
        use_case: ExtractProductCountUseCase,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test with no sitemaps found."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        mock_sitemap_port.get_sitemap_urls.return_value = []

        result = await use_case.execute(
            page_id="page-1",
            website_url=Url("https://example.com"),
            country=Country("US"),
        )

        assert result.product_count == 0
        assert result.sitemaps_found == 0

    @pytest.mark.asyncio
    async def test_extract_product_count_handles_sitemap_not_found_error(
        self,
        use_case: ExtractProductCountUseCase,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test graceful handling of SitemapNotFoundError."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        mock_sitemap_port.get_sitemap_urls.side_effect = SitemapNotFoundError(
            "https://example.com"
        )

        result = await use_case.execute(
            page_id="page-1",
            website_url=Url("https://example.com"),
            country=Country("US"),
        )

        # Should return zero, not raise error
        assert result.product_count == 0
        assert result.sitemaps_found == 0

    @pytest.mark.asyncio
    async def test_extract_product_count_preserves_previous_count(
        self,
        use_case: ExtractProductCountUseCase,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that previous count is preserved in result."""
        # Page with existing product count
        page = Page.create(id="page-1", url=Url("https://example.com"))
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state,
            product_count=ProductCount(50),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        mock_sitemap_port.get_sitemap_urls.return_value = [
            Url("https://example.com/sitemap.xml")
        ]
        mock_sitemap_port.extract_product_count.return_value = ProductCount(100)

        result = await use_case.execute(
            page_id="page-1",
            website_url=Url("https://example.com"),
            country=Country("US"),
        )

        assert result.previous_count == 50
        assert result.product_count == 100

    @pytest.mark.asyncio
    async def test_extract_product_count_transitions_to_active(
        self,
        use_case: ExtractProductCountUseCase,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that verified Shopify page transitions to ACTIVE."""
        # Create a verified Shopify page
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.VERIFIED_SHOPIFY),
            is_shopify=True,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        mock_sitemap_port.get_sitemap_urls.return_value = [
            Url("https://example.com/sitemap.xml")
        ]
        mock_sitemap_port.extract_product_count.return_value = ProductCount(50)

        await use_case.execute(
            page_id="page-1",
            website_url=Url("https://example.com"),
            country=Country("US"),
        )

        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.state.status == PageStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_extract_product_count_zero_products_no_transition(
        self,
        use_case: ExtractProductCountUseCase,
        mock_sitemap_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that zero products doesn't trigger transition."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.VERIFIED_SHOPIFY),
            is_shopify=True,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        mock_sitemap_port.get_sitemap_urls.return_value = [
            Url("https://example.com/sitemap.xml")
        ]
        mock_sitemap_port.extract_product_count.return_value = ProductCount(0)

        await use_case.execute(
            page_id="page-1",
            website_url=Url("https://example.com"),
            country=Country("US"),
        )

        # Should remain VERIFIED_SHOPIFY, not transition to ACTIVE
        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.state.status == PageStatus.VERIFIED_SHOPIFY

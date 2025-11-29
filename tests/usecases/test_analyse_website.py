"""Tests for AnalyseWebsiteUseCase.

Tests the website analysis use case with mocked ports.
"""

import pytest
from unittest.mock import AsyncMock

from src.app.core.domain import (
    Page,
    Url,
    Country,
    PageStatus,
    EntityNotFoundError,
)
from src.app.core.usecases import AnalyseWebsiteUseCase, AnalyseWebsiteResult
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeTaskDispatcher,
)


class TestAnalyseWebsiteUseCase:
    """Tests for AnalyseWebsiteUseCase."""

    @pytest.fixture
    def use_case(
        self,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
        fake_logger: FakeLoggingPort,
    ) -> AnalyseWebsiteUseCase:
        """Create use case with mocked dependencies."""
        return AnalyseWebsiteUseCase(
            html_scraper=mock_html_scraper_port,
            page_repository=fake_page_repo,
            task_dispatcher=fake_task_dispatcher,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_analyse_website_detects_shopify(
        self,
        use_case: AnalyseWebsiteUseCase,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
    ) -> None:
        """Test successful Shopify detection."""
        # Setup page (needs to be in ANALYZED state to transition to VERIFIED)
        page = Page.create(
            id="page-1",
            url=Url("https://example.com"),
            country=Country("US"),
        )
        # Transition to ANALYZED state
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.ANALYZED),
            country=page.country,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        # Setup Shopify HTML response
        shopify_html = """
        <html>
        <head>
            <meta property="og:site_name" content="My Awesome Store">
            <script src="https://cdn.shopify.com/s/files/theme.js"></script>
        </head>
        <body>
            <div class="shopify-section">
                Shopify.theme = {"name": "Dawn"};
                "currency": "USD"
            </div>
        </body>
        </html>
        """
        mock_html_scraper_port.fetch_html.return_value = shopify_html
        mock_html_scraper_port.fetch_headers.return_value = {"server": "Shopify"}

        # Execute
        result = await use_case.execute(
            page_id="page-1",
            url=Url("https://my-store.com"),
        )

        # Verify result
        assert isinstance(result, AnalyseWebsiteResult)
        assert result.is_shopify is True
        assert result.shop_name == "My Awesome Store"
        assert result.sitemap_count_dispatched is True

        # Verify page was updated
        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.is_shopify is True
        assert updated_page.state.status == PageStatus.VERIFIED_SHOPIFY

        # Verify sitemap count was dispatched
        assert len(fake_task_dispatcher.dispatched_tasks) == 1
        assert fake_task_dispatcher.dispatched_tasks[0]["type"] == "sitemap_count"

    @pytest.mark.asyncio
    async def test_analyse_website_not_shopify(
        self,
        use_case: AnalyseWebsiteUseCase,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
    ) -> None:
        """Test non-Shopify website detection."""
        # Setup page in ANALYZED state
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        # Non-Shopify HTML
        mock_html_scraper_port.fetch_html.return_value = """
        <html>
        <head><title>Regular Website</title></head>
        <body><p>Just a regular website</p></body>
        </html>
        """
        mock_html_scraper_port.fetch_headers.return_value = {"server": "nginx"}

        result = await use_case.execute(
            page_id="page-1",
            url=Url("https://regular-site.com"),
        )

        assert result.is_shopify is False
        assert result.sitemap_count_dispatched is False

        # Verify page was marked as not Shopify
        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.is_shopify is False
        assert updated_page.state.status == PageStatus.NOT_SHOPIFY

        # No sitemap task should be dispatched
        assert len(fake_task_dispatcher.dispatched_tasks) == 0

    @pytest.mark.asyncio
    async def test_analyse_website_page_not_found(
        self,
        use_case: AnalyseWebsiteUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                page_id="nonexistent",
                url=Url("https://example.com"),
            )

    @pytest.mark.asyncio
    async def test_analyse_website_extracts_currency(
        self,
        use_case: AnalyseWebsiteUseCase,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test currency extraction."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        mock_html_scraper_port.fetch_html.return_value = """
        <html>
        <script src="https://cdn.shopify.com/s/files/theme.js"></script>
        <script>
            "currency": "EUR"
        </script>
        </html>
        """
        mock_html_scraper_port.fetch_headers.return_value = {}

        result = await use_case.execute(
            page_id="page-1",
            url=Url("https://store.com"),
        )

        assert result.currency == "EUR"

    @pytest.mark.asyncio
    async def test_analyse_website_detects_payment_methods(
        self,
        use_case: AnalyseWebsiteUseCase,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test payment methods detection."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        mock_html_scraper_port.fetch_html.return_value = """
        <html>
        <script src="https://cdn.shopify.com/s/files/theme.js"></script>
        <div class="payment-methods">
            <img src="paypal.png" alt="PayPal">
            <img src="apple-pay.png" alt="Apple Pay">
            <span>Klarna available</span>
        </div>
        </html>
        """
        mock_html_scraper_port.fetch_headers.return_value = {}

        result = await use_case.execute(
            page_id="page-1",
            url=Url("https://store.com"),
        )

        assert result.payment_methods is not None
        assert "paypal" in result.payment_methods
        assert "apple_pay" in result.payment_methods
        assert "klarna" in result.payment_methods

    @pytest.mark.asyncio
    async def test_analyse_website_detects_category(
        self,
        use_case: AnalyseWebsiteUseCase,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test category detection from content."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        mock_html_scraper_port.fetch_html.return_value = """
        <html>
        <script src="https://cdn.shopify.com/s/files/theme.js"></script>
        <title>Fashion Store - Clothing and Apparel</title>
        <div>
            Latest fashion trends, clothing, dresses, and accessories.
        </div>
        </html>
        """
        mock_html_scraper_port.fetch_headers.return_value = {}

        result = await use_case.execute(
            page_id="page-1",
            url=Url("https://fashion-store.com"),
        )

        assert result.category == "fashion"

    @pytest.mark.asyncio
    async def test_analyse_website_detects_shopify_via_header(
        self,
        use_case: AnalyseWebsiteUseCase,
        mock_html_scraper_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test Shopify detection via HTTP headers."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        from src.app.core.domain import PageState

        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        await fake_page_repo.save(page)

        # Minimal HTML but Shopify header
        mock_html_scraper_port.fetch_html.return_value = "<html></html>"
        mock_html_scraper_port.fetch_headers.return_value = {
            "x-shopify-stage": "production"
        }

        result = await use_case.execute(
            page_id="page-1",
            url=Url("https://store.com"),
        )

        assert result.is_shopify is True

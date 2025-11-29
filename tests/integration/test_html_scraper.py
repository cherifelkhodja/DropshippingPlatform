"""Integration tests for HTML scraper client."""

import pytest

from src.app.adapters.outbound.scraper import HtmlScraperClient
from src.app.core.domain.value_objects import Url

pytestmark = pytest.mark.integration


class TestHtmlScraperClient:
    """Tests for HtmlScraperClient with mock server."""

    @pytest.mark.asyncio
    async def test_fetch_html_success(self, http_session, fake_logger, mock_server_url):
        """Test fetching HTML content successfully."""
        scraper = HtmlScraperClient(session=http_session, logger=fake_logger)
        url = Url(value=f"{mock_server_url}/")

        html = await scraper.fetch_html(url)

        assert "Test Store" in html
        assert "Shopify" in html

    @pytest.mark.asyncio
    async def test_fetch_html_product_page(
        self, http_session, fake_logger, mock_server_url
    ):
        """Test fetching a product page."""
        scraper = HtmlScraperClient(session=http_session, logger=fake_logger)
        url = Url(value=f"{mock_server_url}/products/test-product")

        html = await scraper.fetch_html(url)

        assert "Test Product" in html
        assert "$29.99" in html

    @pytest.mark.asyncio
    async def test_fetch_headers(self, http_session, fake_logger, mock_server_url):
        """Test fetching HTTP headers."""
        scraper = HtmlScraperClient(session=http_session, logger=fake_logger)
        url = Url(value=f"{mock_server_url}/")

        headers = await scraper.fetch_headers(url)

        assert isinstance(headers, dict)
        assert "Content-Type" in headers or "content-type" in headers

    @pytest.mark.asyncio
    async def test_logging_on_fetch(self, http_session, fake_logger, mock_server_url):
        """Test that scraper logs operations."""
        scraper = HtmlScraperClient(session=http_session, logger=fake_logger)
        url = Url(value=f"{mock_server_url}/")

        await scraper.fetch_html(url)

        assert len(fake_logger.messages) >= 2  # Start and end logs
        assert any("Fetching HTML" in msg for _, msg, _ in fake_logger.messages)

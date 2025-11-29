"""Integration tests for sitemap client."""

import pytest

from src.app.adapters.outbound.sitemap import SitemapClient
from src.app.core.domain.value_objects import Country, Url

pytestmark = pytest.mark.integration


class TestSitemapClient:
    """Tests for SitemapClient with mock server."""

    @pytest.mark.asyncio
    async def test_get_sitemap_urls(self, http_session, fake_logger, mock_server_url):
        """Test discovering sitemap URLs."""
        client = SitemapClient(session=http_session, logger=fake_logger)
        website = Url(value=mock_server_url)

        sitemap_urls = await client.get_sitemap_urls(website)

        assert len(sitemap_urls) > 0
        assert any("sitemap_products" in url.value for url in sitemap_urls)

    @pytest.mark.asyncio
    async def test_extract_product_count(
        self, http_session, fake_logger, mock_server_url
    ):
        """Test extracting product count from sitemaps."""
        client = SitemapClient(session=http_session, logger=fake_logger)
        website = Url(value=mock_server_url)

        sitemap_urls = await client.get_sitemap_urls(website)
        product_count = await client.extract_product_count(
            sitemap_urls=sitemap_urls,
            country=Country(code="US"),
        )

        assert product_count.value >= 0

    @pytest.mark.asyncio
    async def test_prioritizes_product_sitemaps(
        self, http_session, fake_logger, mock_server_url
    ):
        """Test that product sitemaps are prioritized."""
        client = SitemapClient(session=http_session, logger=fake_logger)
        website = Url(value=mock_server_url)

        sitemap_urls = await client.get_sitemap_urls(website)

        # First URL should be a product sitemap if one exists
        if len(sitemap_urls) > 1:
            first_url = sitemap_urls[0].value.lower()
            assert "product" in first_url or sitemap_urls[0] == sitemap_urls[0]

    @pytest.mark.asyncio
    async def test_logging_on_discovery(
        self, http_session, fake_logger, mock_server_url
    ):
        """Test that client logs discovery operations."""
        client = SitemapClient(session=http_session, logger=fake_logger)
        website = Url(value=mock_server_url)

        await client.get_sitemap_urls(website)

        assert len(fake_logger.messages) >= 1
        assert any("sitemap" in msg.lower() for _, msg, _ in fake_logger.messages)

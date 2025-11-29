"""Integration tests for Meta Ads client."""

import pytest
from unittest.mock import AsyncMock, patch

from src.app.adapters.outbound.meta import MetaAdsClient, MetaAdsConfig
from src.app.core.domain.value_objects import Country, Language

pytestmark = pytest.mark.integration


class TestMetaAdsClient:
    """Tests for MetaAdsClient with mocked responses."""

    @pytest.fixture
    def meta_config(self) -> MetaAdsConfig:
        """Create Meta Ads configuration for testing."""
        return MetaAdsConfig(
            access_token="test_token",
            base_url="https://graph.facebook.com",
            api_version="v18.0",
        )

    @pytest.mark.asyncio
    async def test_search_ads_by_keyword_success(
        self, http_session, fake_logger, meta_config
    ):
        """Test successful keyword search with mocked response."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        mock_response = {
            "data": [
                {"id": "ad_1", "page_id": "page_1"},
                {"id": "ad_2", "page_id": "page_2"},
            ],
            "paging": {},
        }

        with patch.object(
            client, "_execute_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = mock_response

            ads = await client.search_ads_by_keyword(
                keyword="test product",
                country=Country(code="US"),
                limit=10,
            )

            assert len(list(ads)) == 2
            mock_req.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_ads_with_language(
        self, http_session, fake_logger, meta_config
    ):
        """Test keyword search with language filter."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        mock_response = {"data": [{"id": "ad_1", "page_id": "page_1"}], "paging": {}}

        with patch.object(
            client, "_execute_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = mock_response

            ads = await client.search_ads_by_keyword(
                keyword="test",
                country=Country(code="FR"),
                language=Language(code="fr"),
                limit=10,
            )

            assert len(list(ads)) == 1

    @pytest.mark.asyncio
    async def test_get_ads_by_page(self, http_session, fake_logger, meta_config):
        """Test getting ads by page IDs."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        mock_response = {
            "data": [{"id": "ad_1", "page_id": "page_123"}],
            "paging": {},
        }

        with patch.object(
            client, "_execute_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = mock_response

            ads = await client.get_ads_by_page(
                page_ids=["page_123"],
                country=Country(code="US"),
                limit=10,
            )

            assert len(list(ads)) == 1

    @pytest.mark.asyncio
    async def test_get_ads_details(self, http_session, fake_logger, meta_config):
        """Test getting detailed ad information."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        mock_response = {
            "data": [
                {
                    "id": "ad_1",
                    "page_id": "page_123",
                    "page_name": "Test Store",
                    "ad_creative_bodies": ["Buy now!"],
                }
            ],
            "paging": {},
        }

        with patch.object(
            client, "_execute_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = mock_response

            ads = await client.get_ads_details(
                page_id="page_123",
                country=Country(code="US"),
                limit=10,
            )

            result = list(ads)
            assert len(result) == 1
            assert result[0].get("page_name") == "Test Store"

    @pytest.mark.asyncio
    async def test_empty_page_ids_returns_empty(
        self, http_session, fake_logger, meta_config
    ):
        """Test that empty page IDs returns empty list."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        ads = await client.get_ads_by_page(
            page_ids=[],
            country=Country(code="US"),
        )

        assert list(ads) == []

    @pytest.mark.asyncio
    async def test_pagination_handling(self, http_session, fake_logger, meta_config):
        """Test that pagination is handled correctly."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        # First page response with next URL
        first_response = {
            "data": [{"id": f"ad_{i}", "page_id": "page_1"} for i in range(5)],
            "paging": {"next": "https://graph.facebook.com/next_page"},
        }

        # Second page response without next
        second_response = {
            "data": [{"id": f"ad_{i}", "page_id": "page_1"} for i in range(5, 8)],
            "paging": {},
        }

        call_count = 0

        async def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return first_response
            return second_response

        with patch.object(client, "_execute_request", side_effect=mock_execute):
            ads = await client.search_ads_by_keyword(
                keyword="test",
                country=Country(code="US"),
                limit=100,
            )

            assert len(list(ads)) == 8
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_logging_on_search(self, http_session, fake_logger, meta_config):
        """Test that client logs search operations."""
        client = MetaAdsClient(
            config=meta_config,
            session=http_session,
            logger=fake_logger,
        )

        mock_response = {"data": [], "paging": {}}

        with patch.object(
            client, "_execute_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = mock_response

            await client.search_ads_by_keyword(
                keyword="test",
                country=Country(code="US"),
            )

            assert len(fake_logger.messages) >= 2
            assert any(
                "keyword search" in msg.lower() for _, msg, _ in fake_logger.messages
            )

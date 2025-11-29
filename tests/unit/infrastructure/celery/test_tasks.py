"""Tests for Celery task definitions.

Verifies tasks properly call use cases via the container.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestAsyncTask:
    """Tests for the AsyncTask base class."""

    def test_run_async_executes_coroutine(self) -> None:
        """run_async executes an async coroutine synchronously."""
        from src.app.infrastructure.celery.tasks import AsyncTask

        task = AsyncTask()

        async def sample_coro() -> str:
            return "result"

        result = task.run_async(sample_coro())
        assert result == "result"

    def test_run_async_propagates_exceptions(self) -> None:
        """run_async propagates exceptions from coroutine."""
        from src.app.infrastructure.celery.tasks import AsyncTask

        task = AsyncTask()

        async def failing_coro() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            task.run_async(failing_coro())


class TestScanPageTask:
    """Tests for scan_page_task."""

    @patch("src.app.infrastructure.celery.tasks.get_container")
    @patch("src.app.infrastructure.celery.tasks.configure_logging")
    def test_scan_page_task_calls_use_case(
        self,
        mock_configure_logging: MagicMock,
        mock_get_container: MagicMock,
    ) -> None:
        """scan_page_task calls AnalysePageDeepUseCase."""
        from src.app.infrastructure.celery.tasks import scan_page_task

        # Setup mocks
        mock_result = MagicMock()
        mock_result.page_id = "page-123"
        mock_result.ads_found = 5
        mock_result.ads_saved = 5
        mock_result.destination_url = None
        mock_result.website_analysis_dispatched = True

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = mock_result

        mock_container = MagicMock()
        mock_container.execution_context = MagicMock()
        mock_container.get_analyse_page_deep_use_case = AsyncMock(
            return_value=mock_use_case
        )

        # Setup async context manager
        mock_db_session = MagicMock()
        mock_http_session = MagicMock()

        async def mock_context():
            yield (mock_db_session, mock_http_session)

        mock_container.execution_context.return_value.__aenter__ = AsyncMock(
            return_value=(mock_db_session, mock_http_session)
        )
        mock_container.execution_context.return_value.__aexit__ = AsyncMock(
            return_value=None
        )

        mock_get_container.return_value = mock_container

        # Execute task
        result = scan_page_task.apply(
            args=["page-123", "550e8400-e29b-41d4-a716-446655440000", "US"]
        ).get(timeout=5)

        assert result["page_id"] == "page-123"
        assert result["status"] == "completed"
        assert result["ads_found"] == 5


class TestAnalyseWebsiteTask:
    """Tests for analyse_website_task."""

    @patch("src.app.infrastructure.celery.tasks.get_container")
    @patch("src.app.infrastructure.celery.tasks.configure_logging")
    def test_analyse_website_task_calls_use_case(
        self,
        mock_configure_logging: MagicMock,
        mock_get_container: MagicMock,
    ) -> None:
        """analyse_website_task calls AnalyseWebsiteUseCase."""
        from src.app.infrastructure.celery.tasks import analyse_website_task

        # Setup mocks
        mock_result = MagicMock()
        mock_result.page_id = "page-123"
        mock_result.is_shopify = True
        mock_result.shop_name = "Test Shop"
        mock_result.theme_name = "Dawn"
        mock_result.currency = "USD"
        mock_result.category = "fashion"
        mock_result.payment_methods = ["paypal", "credit_card"]
        mock_result.sitemap_count_dispatched = True

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = mock_result

        mock_container = MagicMock()
        mock_container.get_analyse_website_use_case = AsyncMock(
            return_value=mock_use_case
        )
        mock_container.execution_context.return_value.__aenter__ = AsyncMock(
            return_value=(MagicMock(), MagicMock())
        )
        mock_container.execution_context.return_value.__aexit__ = AsyncMock(
            return_value=None
        )

        mock_get_container.return_value = mock_container

        # Execute task
        result = analyse_website_task.apply(
            args=["page-123", "https://test-shop.com"]
        ).get(timeout=5)

        assert result["page_id"] == "page-123"
        assert result["is_shopify"] is True
        assert result["shop_name"] == "Test Shop"


class TestCountSitemapProductsTask:
    """Tests for count_sitemap_products_task."""

    @patch("src.app.infrastructure.celery.tasks.get_container")
    @patch("src.app.infrastructure.celery.tasks.configure_logging")
    def test_count_sitemap_products_task_calls_use_case(
        self,
        mock_configure_logging: MagicMock,
        mock_get_container: MagicMock,
    ) -> None:
        """count_sitemap_products_task calls ExtractProductCountUseCase."""
        from src.app.infrastructure.celery.tasks import count_sitemap_products_task

        # Setup mocks
        mock_result = MagicMock()
        mock_result.page_id = "page-123"
        mock_result.product_count = 150
        mock_result.sitemaps_found = 3
        mock_result.previous_count = 100

        mock_use_case = AsyncMock()
        mock_use_case.execute.return_value = mock_result

        mock_container = MagicMock()
        mock_container.get_extract_product_count_use_case = AsyncMock(
            return_value=mock_use_case
        )
        mock_container.execution_context.return_value.__aenter__ = AsyncMock(
            return_value=(MagicMock(), MagicMock())
        )
        mock_container.execution_context.return_value.__aexit__ = AsyncMock(
            return_value=None
        )

        mock_get_container.return_value = mock_container

        # Execute task
        result = count_sitemap_products_task.apply(
            args=["page-123", "https://test-shop.com", "US"]
        ).get(timeout=5)

        assert result["page_id"] == "page-123"
        assert result["product_count"] == 150
        assert result["sitemaps_found"] == 3

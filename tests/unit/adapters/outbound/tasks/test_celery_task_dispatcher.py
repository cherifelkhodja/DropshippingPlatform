"""Unit tests for CeleryTaskDispatcher.

Tests the Celery-based task dispatcher adapter.
"""

import logging
from unittest.mock import MagicMock

import pytest

from src.app.adapters.outbound.tasks.celery_task_dispatcher import CeleryTaskDispatcher
from src.app.core.domain.errors import TaskDispatchError
from src.app.core.domain.value_objects import Country, ScanId, Url


@pytest.fixture
def mock_celery_app() -> MagicMock:
    """Create a mock Celery application."""
    return MagicMock()


@pytest.fixture
def mock_logger() -> MagicMock:
    """Create a mock logger."""
    return MagicMock(spec=logging.Logger)


@pytest.fixture
def dispatcher(
    mock_celery_app: MagicMock, mock_logger: MagicMock
) -> CeleryTaskDispatcher:
    """Create a CeleryTaskDispatcher instance with mocked dependencies."""
    return CeleryTaskDispatcher(
        celery_app=mock_celery_app,
        logger=mock_logger,
    )


class TestCeleryTaskDispatcherInit:
    """Tests for CeleryTaskDispatcher initialization."""

    def test_init_with_custom_logger(
        self, mock_celery_app: MagicMock, mock_logger: MagicMock
    ) -> None:
        """Dispatcher initializes with custom logger."""
        dispatcher = CeleryTaskDispatcher(
            celery_app=mock_celery_app,
            logger=mock_logger,
        )

        assert dispatcher._celery is mock_celery_app
        assert dispatcher._logger is mock_logger

    def test_init_with_default_logger(self, mock_celery_app: MagicMock) -> None:
        """Dispatcher creates default logger when none provided."""
        dispatcher = CeleryTaskDispatcher(celery_app=mock_celery_app)

        assert dispatcher._celery is mock_celery_app
        assert dispatcher._logger is not None


class TestDispatchScanPage:
    """Tests for dispatch_scan_page method."""

    @pytest.mark.asyncio
    async def test_dispatch_scan_page_success(
        self, dispatcher: CeleryTaskDispatcher, mock_celery_app: MagicMock
    ) -> None:
        """Successfully dispatches scan_page task."""
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_celery_app.send_task.return_value = mock_result

        page_id = "page-456"
        scan_id = ScanId.generate()
        country = Country("US")

        await dispatcher.dispatch_scan_page(page_id, scan_id, country)

        mock_celery_app.send_task.assert_called_once_with(
            "tasks.scan_page",
            args=[page_id, str(scan_id), str(country)],
        )

    @pytest.mark.asyncio
    async def test_dispatch_scan_page_logs_info(
        self,
        dispatcher: CeleryTaskDispatcher,
        mock_celery_app: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Logs info when dispatching scan_page task."""
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_celery_app.send_task.return_value = mock_result

        page_id = "page-456"
        scan_id = ScanId.generate()
        country = Country("US")

        await dispatcher.dispatch_scan_page(page_id, scan_id, country)

        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args
        assert "Dispatching scan_page task" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_dispatch_scan_page_failure_raises_task_dispatch_error(
        self, dispatcher: CeleryTaskDispatcher, mock_celery_app: MagicMock
    ) -> None:
        """Raises TaskDispatchError when task dispatch fails."""
        mock_celery_app.send_task.side_effect = Exception("Redis connection failed")

        page_id = "page-456"
        scan_id = ScanId.generate()
        country = Country("US")

        with pytest.raises(TaskDispatchError) as exc_info:
            await dispatcher.dispatch_scan_page(page_id, scan_id, country)

        # task_name is stored in 'value', reason in 'message'
        assert exc_info.value.value == "scan_page"
        assert "Redis connection failed" in exc_info.value.message


class TestDispatchAnalyseWebsite:
    """Tests for dispatch_analyse_website method."""

    @pytest.mark.asyncio
    async def test_dispatch_analyse_website_success(
        self, dispatcher: CeleryTaskDispatcher, mock_celery_app: MagicMock
    ) -> None:
        """Successfully dispatches analyse_website task."""
        mock_result = MagicMock()
        mock_result.id = "task-789"
        mock_celery_app.send_task.return_value = mock_result

        page_id = "page-456"
        url = Url("https://example-shop.com")

        await dispatcher.dispatch_analyse_website(page_id, url)

        mock_celery_app.send_task.assert_called_once_with(
            "tasks.analyse_website",
            args=[page_id, str(url)],
        )

    @pytest.mark.asyncio
    async def test_dispatch_analyse_website_logs_info(
        self,
        dispatcher: CeleryTaskDispatcher,
        mock_celery_app: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Logs info when dispatching analyse_website task."""
        mock_result = MagicMock()
        mock_result.id = "task-789"
        mock_celery_app.send_task.return_value = mock_result

        page_id = "page-456"
        url = Url("https://example-shop.com")

        await dispatcher.dispatch_analyse_website(page_id, url)

        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args
        assert "Dispatching analyse_website task" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_dispatch_analyse_website_failure_raises_task_dispatch_error(
        self, dispatcher: CeleryTaskDispatcher, mock_celery_app: MagicMock
    ) -> None:
        """Raises TaskDispatchError when task dispatch fails."""
        mock_celery_app.send_task.side_effect = Exception("Broker unavailable")

        page_id = "page-456"
        url = Url("https://example-shop.com")

        with pytest.raises(TaskDispatchError) as exc_info:
            await dispatcher.dispatch_analyse_website(page_id, url)

        # task_name is stored in 'value', reason in 'message'
        assert exc_info.value.value == "analyse_website"
        assert "Broker unavailable" in exc_info.value.message


class TestDispatchSitemapCount:
    """Tests for dispatch_sitemap_count method."""

    @pytest.mark.asyncio
    async def test_dispatch_sitemap_count_success(
        self, dispatcher: CeleryTaskDispatcher, mock_celery_app: MagicMock
    ) -> None:
        """Successfully dispatches sitemap_count task."""
        mock_result = MagicMock()
        mock_result.id = "task-abc"
        mock_celery_app.send_task.return_value = mock_result

        page_id = "page-456"
        website = Url("https://store.example.com")
        country = Country("FR")

        await dispatcher.dispatch_sitemap_count(page_id, website, country)

        mock_celery_app.send_task.assert_called_once_with(
            "tasks.count_sitemap_products",
            args=[page_id, str(website), str(country)],
        )

    @pytest.mark.asyncio
    async def test_dispatch_sitemap_count_logs_info(
        self,
        dispatcher: CeleryTaskDispatcher,
        mock_celery_app: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Logs info when dispatching sitemap_count task."""
        mock_result = MagicMock()
        mock_result.id = "task-abc"
        mock_celery_app.send_task.return_value = mock_result

        page_id = "page-456"
        website = Url("https://store.example.com")
        country = Country("FR")

        await dispatcher.dispatch_sitemap_count(page_id, website, country)

        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args
        assert "Dispatching sitemap_count task" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_dispatch_sitemap_count_failure_raises_task_dispatch_error(
        self, dispatcher: CeleryTaskDispatcher, mock_celery_app: MagicMock
    ) -> None:
        """Raises TaskDispatchError when task dispatch fails."""
        mock_celery_app.send_task.side_effect = Exception("Queue full")

        page_id = "page-456"
        website = Url("https://store.example.com")
        country = Country("FR")

        with pytest.raises(TaskDispatchError) as exc_info:
            await dispatcher.dispatch_sitemap_count(page_id, website, country)

        # task_name is stored in 'value', reason in 'message'
        assert exc_info.value.value == "sitemap_count"
        assert "Queue full" in exc_info.value.message


class TestErrorLogging:
    """Tests for error logging behavior."""

    @pytest.mark.asyncio
    async def test_logs_error_on_dispatch_failure(
        self,
        dispatcher: CeleryTaskDispatcher,
        mock_celery_app: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Logs error message when dispatch fails."""
        mock_celery_app.send_task.side_effect = Exception("Connection reset")

        page_id = "page-456"
        scan_id = ScanId.generate()
        country = Country("US")

        with pytest.raises(TaskDispatchError):
            await dispatcher.dispatch_scan_page(page_id, scan_id, country)

        mock_logger.error.assert_called()
        call_args = mock_logger.error.call_args
        assert "Failed to dispatch scan_page task" in call_args[0][0]

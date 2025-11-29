"""Tests for AnalysePageDeepUseCase.

Tests the deep page analysis use case with mocked ports.
"""

import pytest
from unittest.mock import AsyncMock

from src.app.core.domain import (
    Page,
    Url,
    Country,
    ScanId,
    ScanStatus,
    EntityNotFoundError,
)
from src.app.core.usecases import AnalysePageDeepUseCase, AnalysePageDeepResult
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeAdsRepository,
    FakeScanRepository,
    FakeTaskDispatcher,
)


class TestAnalysePageDeepUseCase:
    """Tests for AnalysePageDeepUseCase."""

    @pytest.fixture
    def use_case(
        self,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scan_repo: FakeScanRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
        fake_logger: FakeLoggingPort,
    ) -> AnalysePageDeepUseCase:
        """Create use case with mocked dependencies."""
        return AnalysePageDeepUseCase(
            meta_ads_port=mock_meta_ads_port,
            ads_repository=fake_ads_repo,
            scan_repository=fake_scan_repo,
            page_repository=fake_page_repo,
            task_dispatcher=fake_task_dispatcher,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_analyse_page_deep_happy_path(
        self,
        use_case: AnalysePageDeepUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scan_repo: FakeScanRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
    ) -> None:
        """Test successful deep page analysis."""
        # Setup page
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        scan_id = ScanId.generate()

        # Setup mock response
        mock_meta_ads_port.get_ads_details.return_value = [
            {
                "id": "ad-1",
                "page_id": "page-1",
                "link_url": "https://shop.example.com/product",
                "ad_creative_title": "Amazing Product",
                "is_active": True,
            },
            {
                "id": "ad-2",
                "page_id": "page-1",
                "link_title": "https://shop.example.com/other",
                "is_active": True,
            },
        ]

        # Execute
        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
            scan_id=scan_id,
        )

        # Verify result
        assert isinstance(result, AnalysePageDeepResult)
        assert result.page_id == "page-1"
        assert result.ads_found == 2
        assert result.ads_saved == 2
        assert result.destination_url is not None
        assert result.website_analysis_dispatched is True

        # Verify ads were saved
        assert len(fake_ads_repo.ads) == 2

        # Verify scan was saved with completed status
        saved_scan = await fake_scan_repo.get_scan(scan_id)
        assert saved_scan is not None
        assert saved_scan.status == ScanStatus.COMPLETED

        # Verify website analysis was dispatched
        assert len(fake_task_dispatcher.dispatched_tasks) == 1
        task = fake_task_dispatcher.dispatched_tasks[0]
        assert task["type"] == "analyse_website"
        assert task["page_id"] == "page-1"

    @pytest.mark.asyncio
    async def test_analyse_page_deep_page_not_found(
        self,
        use_case: AnalysePageDeepUseCase,
    ) -> None:
        """Test error when page not found."""
        scan_id = ScanId.generate()

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                page_id="nonexistent",
                country=Country("US"),
                scan_id=scan_id,
            )

    @pytest.mark.asyncio
    async def test_analyse_page_deep_no_ads(
        self,
        use_case: AnalysePageDeepUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_task_dispatcher: FakeTaskDispatcher,
    ) -> None:
        """Test analysis with no ads found."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        mock_meta_ads_port.get_ads_details.return_value = []

        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
            scan_id=ScanId.generate(),
        )

        assert result.ads_found == 0
        assert result.destination_url is None
        assert result.website_analysis_dispatched is False
        assert len(fake_task_dispatcher.dispatched_tasks) == 0

    @pytest.mark.asyncio
    async def test_analyse_page_deep_extracts_best_url(
        self,
        use_case: AnalysePageDeepUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test URL extraction priority (link_url > link_title > link_caption)."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        # Only link_title available (not link_url)
        mock_meta_ads_port.get_ads_details.return_value = [
            {
                "id": "ad-1",
                "page_id": "page-1",
                "link_title": "https://priority-url.com/product",
            },
        ]

        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
            scan_id=ScanId.generate(),
        )

        assert result.destination_url is not None
        assert "priority-url.com" in str(result.destination_url)

    @pytest.mark.asyncio
    async def test_analyse_page_deep_records_failure_on_error(
        self,
        use_case: AnalysePageDeepUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_scan_repo: FakeScanRepository,
    ) -> None:
        """Test that failures are recorded in scan."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        scan_id = ScanId.generate()
        mock_meta_ads_port.get_ads_details.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await use_case.execute(
                page_id="page-1",
                country=Country("US"),
                scan_id=scan_id,
            )

        # Verify scan was saved with failed status
        saved_scan = await fake_scan_repo.get_scan(scan_id)
        assert saved_scan is not None
        assert saved_scan.status == ScanStatus.FAILED
        assert saved_scan.error_message == "API Error"

    @pytest.mark.asyncio
    async def test_analyse_page_deep_handles_invalid_urls(
        self,
        use_case: AnalysePageDeepUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that invalid URLs are handled gracefully."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        mock_meta_ads_port.get_ads_details.return_value = [
            {
                "id": "ad-1",
                "page_id": "page-1",
                "link_url": "not-a-valid-url",  # Invalid
            },
            {
                "id": "ad-2",
                "page_id": "page-1",
                "link_url": "https://valid-url.com/product",
            },
        ]

        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
            scan_id=ScanId.generate(),
        )

        # Should still find the valid URL
        assert result.destination_url is not None
        assert "valid-url.com" in str(result.destination_url)

"""Tests for SearchAdsByKeywordUseCase.

Tests the keyword search use case with mocked ports.
"""

import pytest
from unittest.mock import AsyncMock

from src.app.core.domain import (
    Country,
    Language,
    ScanId,
    KeywordRunStatus,
)
from src.app.core.usecases import SearchAdsByKeywordUseCase, SearchAdsResult
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeKeywordRunRepository,
)


class TestSearchAdsByKeywordUseCase:
    """Tests for SearchAdsByKeywordUseCase."""

    @pytest.fixture
    def use_case(
        self,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_keyword_run_repo: FakeKeywordRunRepository,
        fake_logger: FakeLoggingPort,
    ) -> SearchAdsByKeywordUseCase:
        """Create use case with mocked dependencies."""
        return SearchAdsByKeywordUseCase(
            meta_ads_port=mock_meta_ads_port,
            page_repository=fake_page_repo,
            keyword_run_repository=fake_keyword_run_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_search_ads_happy_path(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_keyword_run_repo: FakeKeywordRunRepository,
    ) -> None:
        """Test successful keyword search."""
        # Setup mock response
        mock_meta_ads_port.search_ads_by_keyword.return_value = [
            {"id": "ad-1", "page_id": "page-1", "is_active": True},
            {"id": "ad-2", "page_id": "page-1", "is_active": True},
            {"id": "ad-3", "page_id": "page-2", "is_active": True},
        ]

        # Execute
        result = await use_case.execute(
            keyword="dropshipping",
            country=Country("US"),
            language=Language("en"),
        )

        # Verify result
        assert isinstance(result, SearchAdsResult)
        assert result.count_ads == 3
        assert len(result.pages) == 2
        assert "page-1" in result.pages
        assert "page-2" in result.pages

        # Verify port was called correctly
        mock_meta_ads_port.search_ads_by_keyword.assert_called_once()
        call_args = mock_meta_ads_port.search_ads_by_keyword.call_args
        assert call_args.kwargs["keyword"] == "dropshipping"
        assert call_args.kwargs["country"].code == "US"

        # Verify keyword run was saved
        assert len(fake_keyword_run_repo.runs) == 1
        saved_run = fake_keyword_run_repo.runs[0]
        assert saved_run.keyword == "dropshipping"
        assert saved_run.status == KeywordRunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_search_ads_empty_keyword_raises_error(
        self,
        use_case: SearchAdsByKeywordUseCase,
    ) -> None:
        """Test that empty keyword raises ValueError."""
        with pytest.raises(ValueError, match="Keyword cannot be empty"):
            await use_case.execute(
                keyword="",
                country=Country("US"),
            )

    @pytest.mark.asyncio
    async def test_search_ads_whitespace_keyword_raises_error(
        self,
        use_case: SearchAdsByKeywordUseCase,
    ) -> None:
        """Test that whitespace-only keyword raises ValueError."""
        with pytest.raises(ValueError, match="Keyword cannot be empty"):
            await use_case.execute(
                keyword="   ",
                country=Country("US"),
            )

    @pytest.mark.asyncio
    async def test_search_ads_deduplicates_ads(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
    ) -> None:
        """Test that duplicate ads are deduplicated."""
        # Return duplicate ads
        mock_meta_ads_port.search_ads_by_keyword.return_value = [
            {"id": "ad-1", "page_id": "page-1"},
            {"id": "ad-1", "page_id": "page-1"},  # Duplicate
            {"id": "ad-2", "page_id": "page-1"},
        ]

        result = await use_case.execute(
            keyword="test",
            country=Country("US"),
        )

        assert result.count_ads == 2  # Only unique ads

    @pytest.mark.asyncio
    async def test_search_ads_filters_blacklisted_pages(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that blacklisted pages are filtered out."""
        # Blacklist a page
        await fake_page_repo.blacklist("page-2")

        mock_meta_ads_port.search_ads_by_keyword.return_value = [
            {"id": "ad-1", "page_id": "page-1"},
            {"id": "ad-2", "page_id": "page-2"},  # Blacklisted
        ]

        result = await use_case.execute(
            keyword="test",
            country=Country("US"),
        )

        assert len(result.pages) == 1
        assert "page-1" in result.pages
        assert "page-2" not in result.pages

    @pytest.mark.asyncio
    async def test_search_ads_returns_provided_scan_id(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
    ) -> None:
        """Test that provided scan_id is returned."""
        mock_meta_ads_port.search_ads_by_keyword.return_value = []
        scan_id = ScanId.generate()

        result = await use_case.execute(
            keyword="test",
            country=Country("US"),
            scan_id=scan_id,
        )

        assert result.scan_id == scan_id

    @pytest.mark.asyncio
    async def test_search_ads_generates_scan_id_if_not_provided(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
    ) -> None:
        """Test that scan_id is generated if not provided."""
        mock_meta_ads_port.search_ads_by_keyword.return_value = []

        result = await use_case.execute(
            keyword="test",
            country=Country("US"),
        )

        assert result.scan_id is not None

    @pytest.mark.asyncio
    async def test_search_ads_counts_new_pages(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that new pages are counted correctly."""
        # Pre-add an existing page
        from src.app.core.domain import Page, Url
        existing_page = Page.create(
            id="page-1",
            url=Url("https://existing.com"),
        )
        await fake_page_repo.save(existing_page)

        mock_meta_ads_port.search_ads_by_keyword.return_value = [
            {"id": "ad-1", "page_id": "page-1"},  # Existing
            {"id": "ad-2", "page_id": "page-2"},  # New
        ]

        result = await use_case.execute(
            keyword="test",
            country=Country("US"),
        )

        assert result.new_pages == 1

    @pytest.mark.asyncio
    async def test_search_ads_no_results(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
    ) -> None:
        """Test search with no results."""
        mock_meta_ads_port.search_ads_by_keyword.return_value = []

        result = await use_case.execute(
            keyword="nonexistent",
            country=Country("US"),
        )

        assert result.count_ads == 0
        assert len(result.pages) == 0

    @pytest.mark.asyncio
    async def test_search_ads_records_failure_on_error(
        self,
        use_case: SearchAdsByKeywordUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_keyword_run_repo: FakeKeywordRunRepository,
    ) -> None:
        """Test that failures are recorded in keyword run."""
        mock_meta_ads_port.search_ads_by_keyword.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await use_case.execute(
                keyword="test",
                country=Country("US"),
            )

        # Verify failure was recorded
        assert len(fake_keyword_run_repo.runs) == 1
        saved_run = fake_keyword_run_repo.runs[0]
        assert saved_run.status == KeywordRunStatus.FAILED

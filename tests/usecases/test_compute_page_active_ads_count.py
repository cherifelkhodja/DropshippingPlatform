"""Tests for ComputePageActiveAdsCountUseCase.

Tests the page ads counting use case with mocked ports.
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
from src.app.core.usecases import (
    ComputePageActiveAdsCountUseCase,
    PageAdsCountResult,
    PageAdsTier,
)
from tests.conftest import FakeLoggingPort, FakePageRepository


class TestComputePageActiveAdsCountUseCase:
    """Tests for ComputePageActiveAdsCountUseCase."""

    @pytest.fixture
    def use_case(
        self,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
        fake_logger: FakeLoggingPort,
    ) -> ComputePageActiveAdsCountUseCase:
        """Create use case with mocked dependencies."""
        return ComputePageActiveAdsCountUseCase(
            meta_ads_port=mock_meta_ads_port,
            page_repository=fake_page_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_compute_ads_count_happy_path(
        self,
        use_case: ComputePageActiveAdsCountUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test successful ads count computation."""
        # Setup page
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        # Setup mock response
        mock_meta_ads_port.get_ads_by_page.return_value = [
            {"id": "ad-1", "is_active": True},
            {"id": "ad-2", "is_active": True},
            {"id": "ad-3", "is_active": False},
        ]

        # Execute
        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
        )

        # Verify result
        assert isinstance(result, PageAdsCountResult)
        assert result.page_id == "page-1"
        assert result.active_ads_count == 2
        assert result.tier == PageAdsTier.S  # 1-5 ads

        # Verify port was called
        mock_meta_ads_port.get_ads_by_page.assert_called_once()

        # Verify page was updated
        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.active_ads_count == 2

    @pytest.mark.asyncio
    async def test_compute_ads_count_page_not_found(
        self,
        use_case: ComputePageActiveAdsCountUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(
                page_id="nonexistent",
                country=Country("US"),
            )
        assert "Page" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compute_ads_count_zero_ads(
        self,
        use_case: ComputePageActiveAdsCountUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test with zero ads (XS tier)."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        mock_meta_ads_port.get_ads_by_page.return_value = []

        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
        )

        assert result.active_ads_count == 0
        assert result.tier == PageAdsTier.XS

    @pytest.mark.asyncio
    async def test_compute_ads_count_tier_classification(
        self,
        use_case: ComputePageActiveAdsCountUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test tier classification for different ad counts."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        await fake_page_repo.save(page)

        test_cases = [
            (0, PageAdsTier.XS),
            (3, PageAdsTier.S),
            (15, PageAdsTier.M),
            (35, PageAdsTier.L),
            (75, PageAdsTier.XL),
            (150, PageAdsTier.XXL),
        ]

        for count, expected_tier in test_cases:
            mock_meta_ads_port.get_ads_by_page.return_value = [
                {"id": f"ad-{i}", "is_active": True}
                for i in range(count)
            ]

            result = await use_case.execute(
                page_id="page-1",
                country=Country("US"),
            )

            assert result.tier == expected_tier, f"Failed for count={count}"

    @pytest.mark.asyncio
    async def test_compute_ads_count_preserves_previous_count(
        self,
        use_case: ComputePageActiveAdsCountUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that previous count is preserved in result."""
        # Page with existing ads count
        page = Page.create(id="page-1", url=Url("https://example.com"))
        page = page.update_ads_count(active=10, total=20)
        await fake_page_repo.save(page)

        mock_meta_ads_port.get_ads_by_page.return_value = [
            {"id": "ad-1", "is_active": True},
        ]

        result = await use_case.execute(
            page_id="page-1",
            country=Country("US"),
        )

        assert result.previous_count == 10
        assert result.active_ads_count == 1

    @pytest.mark.asyncio
    async def test_compute_ads_count_transitions_to_active(
        self,
        use_case: ComputePageActiveAdsCountUseCase,
        mock_meta_ads_port: AsyncMock,
        fake_page_repo: FakePageRepository,
    ) -> None:
        """Test that verified Shopify page transitions to ACTIVE."""
        # Create a verified Shopify page
        page = Page.create(id="page-1", url=Url("https://example.com"))
        # Manually set state to VERIFIED_SHOPIFY
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

        mock_meta_ads_port.get_ads_by_page.return_value = [
            {"id": "ad-1", "is_active": True},
        ]

        await use_case.execute(
            page_id="page-1",
            country=Country("US"),
        )

        updated_page = await fake_page_repo.get("page-1")
        assert updated_page is not None
        assert updated_page.state.status == PageStatus.ACTIVE


class TestPageAdsTier:
    """Tests for PageAdsTier classification."""

    def test_tier_from_count(self) -> None:
        """Test tier classification from count."""
        assert PageAdsTier.from_count(0) == PageAdsTier.XS
        assert PageAdsTier.from_count(1) == PageAdsTier.S
        assert PageAdsTier.from_count(5) == PageAdsTier.S
        assert PageAdsTier.from_count(6) == PageAdsTier.M
        assert PageAdsTier.from_count(20) == PageAdsTier.M
        assert PageAdsTier.from_count(21) == PageAdsTier.L
        assert PageAdsTier.from_count(50) == PageAdsTier.L
        assert PageAdsTier.from_count(51) == PageAdsTier.XL
        assert PageAdsTier.from_count(100) == PageAdsTier.XL
        assert PageAdsTier.from_count(101) == PageAdsTier.XXL
        assert PageAdsTier.from_count(1000) == PageAdsTier.XXL

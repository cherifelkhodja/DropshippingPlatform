"""Unit tests for GetRankedShopsUseCase."""

import pytest
from uuid import uuid4

from src.app.core.domain.entities.shop_score import ShopScore
from src.app.core.domain.entities.ranked_shop import RankedShopsResult
from src.app.core.domain.value_objects.ranking import RankingCriteria
from src.app.core.usecases.get_ranked_shops import GetRankedShopsUseCase
from tests.conftest import FakeScoringRepository, FakeLoggingPort


class TestGetRankedShopsUseCase:
    """Tests for GetRankedShopsUseCase."""

    @pytest.fixture
    def fake_scoring_repo(self) -> FakeScoringRepository:
        """Create a fake scoring repository for testing."""
        return FakeScoringRepository()

    @pytest.fixture
    def fake_logger(self) -> FakeLoggingPort:
        """Create a fake logger for testing."""
        return FakeLoggingPort()

    @pytest.fixture
    def use_case(
        self,
        fake_scoring_repo: FakeScoringRepository,
        fake_logger: FakeLoggingPort,
    ) -> GetRankedShopsUseCase:
        """Create use case with mocked dependencies."""
        return GetRankedShopsUseCase(
            scoring_repository=fake_scoring_repo,
            logger=fake_logger,
        )

    async def _create_score(
        self,
        fake_scoring_repo: FakeScoringRepository,
        page_id: str,
        score_value: float,
        country: str | None = None,
        url: str | None = None,
        name: str | None = None,
    ) -> ShopScore:
        """Helper to create and save a score with page info."""
        score = ShopScore.create(
            id=str(uuid4()),
            page_id=page_id,
            score=score_value,
        )
        await fake_scoring_repo.save(score)
        fake_scoring_repo.set_page_info(page_id, url, country, name)
        return score

    @pytest.mark.asyncio
    async def test_execute_basic(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test basic execution returns RankedShopsResult."""
        # Setup: Create some scores
        await self._create_score(
            fake_scoring_repo, "page-1", 90.0, "FR", "https://shop1.com", "Shop 1"
        )
        await self._create_score(
            fake_scoring_repo, "page-2", 70.0, "FR", "https://shop2.com", "Shop 2"
        )
        await self._create_score(
            fake_scoring_repo, "page-3", 50.0, "US", "https://shop3.com", "Shop 3"
        )

        # Execute
        criteria = RankingCriteria(limit=10, offset=0)
        result = await use_case.execute(criteria)

        # Verify
        assert isinstance(result, RankedShopsResult)
        assert len(result.items) == 3
        assert result.total == 3
        assert result.limit == 10
        assert result.offset == 0

        # Verify ordering (highest score first)
        assert result.items[0].score == 90.0
        assert result.items[1].score == 70.0
        assert result.items[2].score == 50.0

    @pytest.mark.asyncio
    async def test_execute_with_filters_tier(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test execution with tier filter."""
        # Create scores in different tiers
        await self._create_score(fake_scoring_repo, "page-xxl", 90.0, "FR")  # XXL
        await self._create_score(fake_scoring_repo, "page-xl", 75.0, "FR")  # XL
        await self._create_score(fake_scoring_repo, "page-m", 45.0, "FR")  # M

        # Filter by XL tier (70-85)
        criteria = RankingCriteria(limit=10, offset=0, tier="XL")
        result = await use_case.execute(criteria)

        # Only XL tier should be returned
        assert len(result.items) == 1
        assert result.total == 1
        assert result.items[0].score == 75.0
        assert result.items[0].tier == "XL"

    @pytest.mark.asyncio
    async def test_execute_with_filters_min_score(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test execution with min_score filter."""
        await self._create_score(fake_scoring_repo, "page-1", 90.0, "FR")
        await self._create_score(fake_scoring_repo, "page-2", 60.0, "FR")
        await self._create_score(fake_scoring_repo, "page-3", 30.0, "FR")

        # Filter by min_score=50
        criteria = RankingCriteria(limit=10, offset=0, min_score=50.0)
        result = await use_case.execute(criteria)

        # Only scores >= 50 should be returned
        assert len(result.items) == 2
        assert result.total == 2
        assert all(item.score >= 50.0 for item in result.items)

    @pytest.mark.asyncio
    async def test_execute_with_filters_country(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test execution with country filter."""
        await self._create_score(fake_scoring_repo, "page-fr-1", 90.0, "FR")
        await self._create_score(fake_scoring_repo, "page-fr-2", 70.0, "FR")
        await self._create_score(fake_scoring_repo, "page-us", 85.0, "US")

        # Filter by country=FR
        criteria = RankingCriteria(limit=10, offset=0, country="FR")
        result = await use_case.execute(criteria)

        # Only FR shops should be returned
        assert len(result.items) == 2
        assert result.total == 2
        assert all(item.country == "FR" for item in result.items)

    @pytest.mark.asyncio
    async def test_returns_ranked_shops_result_structure(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test that result has correct structure with all fields."""
        await self._create_score(
            fake_scoring_repo,
            "page-1",
            85.0,
            country="US",
            url="https://example.com",
            name="Example Shop",
        )

        criteria = RankingCriteria(limit=50, offset=10)
        result = await use_case.execute(criteria)

        # Verify RankedShopsResult structure
        assert isinstance(result, RankedShopsResult)
        assert result.limit == 50
        assert result.offset == 10
        assert result.total == 1  # Only 1 shop, offset=10 means no items
        assert isinstance(result.items, list)

        # Test with offset=0 to get the item
        criteria_no_offset = RankingCriteria(limit=50, offset=0)
        result_with_items = await use_case.execute(criteria_no_offset)

        assert len(result_with_items.items) == 1
        item = result_with_items.items[0]
        assert item.page_id == "page-1"
        assert item.score == 85.0
        assert item.tier == "XXL"
        assert item.url == "https://example.com"
        assert item.country == "US"
        assert item.name == "Example Shop"

    @pytest.mark.asyncio
    async def test_logs_called(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Test that logger is called with criteria."""
        await self._create_score(fake_scoring_repo, "page-1", 80.0, "FR")

        criteria = RankingCriteria(
            limit=25, offset=5, tier="XL", min_score=60.0, country="FR"
        )
        await use_case.execute(criteria)

        # Verify logger was called
        assert len(fake_logger.logs) >= 1

        # Find the info log for getting ranked shops
        info_logs = [log for log in fake_logger.logs if log["level"] == "info"]
        assert len(info_logs) >= 1

        # Verify criteria was logged
        log = info_logs[0]
        assert log["msg"] == "Getting ranked shops"
        assert log["limit"] == 25
        assert log["offset"] == 5
        assert log["tier"] == "XL"
        assert log["min_score"] == 60.0
        assert log["country"] == "FR"

    @pytest.mark.asyncio
    async def test_pagination_works(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test that pagination returns correct slices."""
        # Create 5 scores
        for i in range(5):
            await self._create_score(
                fake_scoring_repo, f"page-{i}", float(100 - i * 10), "FR"
            )

        # Get first page (limit=2, offset=0)
        criteria_page1 = RankingCriteria(limit=2, offset=0)
        result_page1 = await use_case.execute(criteria_page1)

        assert len(result_page1.items) == 2
        assert result_page1.total == 5
        assert result_page1.items[0].score == 100.0
        assert result_page1.items[1].score == 90.0

        # Get second page (limit=2, offset=2)
        criteria_page2 = RankingCriteria(limit=2, offset=2)
        result_page2 = await use_case.execute(criteria_page2)

        assert len(result_page2.items) == 2
        assert result_page2.total == 5
        assert result_page2.items[0].score == 80.0
        assert result_page2.items[1].score == 70.0

        # Verify has_more property
        assert result_page1.has_more is True
        assert result_page2.has_more is True

        # Get last page
        criteria_page3 = RankingCriteria(limit=2, offset=4)
        result_page3 = await use_case.execute(criteria_page3)

        assert len(result_page3.items) == 1
        assert result_page3.has_more is False

    @pytest.mark.asyncio
    async def test_empty_result(
        self,
        use_case: GetRankedShopsUseCase,
    ) -> None:
        """Test that empty repository returns empty result."""
        criteria = RankingCriteria(limit=10, offset=0)
        result = await use_case.execute(criteria)

        assert isinstance(result, RankedShopsResult)
        assert result.items == []
        assert result.total == 0
        assert result.limit == 10
        assert result.offset == 0

    @pytest.mark.asyncio
    async def test_combined_filters(
        self,
        use_case: GetRankedShopsUseCase,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test that multiple filters work together."""
        # Create diverse data
        await self._create_score(fake_scoring_repo, "page-fr-xxl", 90.0, "FR")  # XXL, FR
        await self._create_score(fake_scoring_repo, "page-fr-xl", 75.0, "FR")  # XL, FR
        await self._create_score(fake_scoring_repo, "page-us-xxl", 88.0, "US")  # XXL, US
        await self._create_score(fake_scoring_repo, "page-fr-m", 45.0, "FR")  # M, FR

        # Filter: country=FR AND min_score=70
        criteria = RankingCriteria(limit=10, offset=0, country="FR", min_score=70.0)
        result = await use_case.execute(criteria)

        assert len(result.items) == 2
        assert result.total == 2
        assert all(
            item.country == "FR" and item.score >= 70.0 for item in result.items
        )

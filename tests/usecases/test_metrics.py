"""Tests for Metrics Use Cases.

Tests for:
- RecordDailyMetricsForAllPagesUseCase
- GetPageMetricsHistoryUseCase

Sprint 7: Historisation & Time Series
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest

from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.shop_score import ShopScore
from src.app.core.domain.entities.page_daily_metrics import (
    PageDailyMetrics,
    PageMetricsHistoryResult,
)
from src.app.core.domain.value_objects import Url, Country, Category
from src.app.core.domain.tiering import score_to_tier
from src.app.core.domain.errors import EntityNotFoundError
from src.app.core.usecases.metrics import (
    RecordDailyMetricsForAllPagesUseCase,
    GetPageMetricsHistoryUseCase,
    RecordDailyMetricsResult,
)
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeScoringRepository,
    FakeProductRepository,
    FakePageMetricsRepository,
)


# =============================================================================
# RecordDailyMetricsForAllPagesUseCase Tests
# =============================================================================


class TestRecordDailyMetricsForAllPagesUseCase:
    """Tests for RecordDailyMetricsForAllPagesUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_page_repo: FakePageRepository,
        fake_scoring_repo: FakeScoringRepository,
        fake_product_repo: FakeProductRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        fake_logger: FakeLoggingPort,
    ) -> RecordDailyMetricsForAllPagesUseCase:
        """Create use case instance with fake dependencies."""
        return RecordDailyMetricsForAllPagesUseCase(
            page_repository=fake_page_repo,
            scoring_repository=fake_scoring_repo,
            product_repository=fake_product_repo,
            page_metrics_repository=fake_page_metrics_repo,
            logger=fake_logger,
        )

    @pytest.fixture
    def sample_page(self) -> Page:
        """Create a sample page for testing."""
        return Page.create(
            id="page-123",
            url=Url("https://example-store.com"),
            country=Country("US"),
            category=Category("fashion"),
        )

    @pytest.fixture
    def sample_score(self, sample_page: Page) -> ShopScore:
        """Create a sample shop score for testing."""
        return ShopScore(
            id=str(uuid4()),
            page_id=sample_page.id,
            score=75.0,
            tier=score_to_tier(75.0),
            components={
                "ads_activity": 30.0,
                "shopify": 20.0,
                "creative_quality": 15.0,
                "catalog": 10.0,
            },
            created_at=datetime.utcnow(),
        )

    @pytest.mark.asyncio
    async def test_execute_no_pages(
        self,
        use_case: RecordDailyMetricsForAllPagesUseCase,
    ) -> None:
        """Test execution with no pages returns empty result."""
        result = await use_case.execute()

        assert result.pages_processed == 0
        assert result.snapshots_written == 0
        assert result.errors_count == 0
        assert result.snapshot_date == date.today()

    @pytest.mark.asyncio
    async def test_execute_with_pages_and_scores(
        self,
        use_case: RecordDailyMetricsForAllPagesUseCase,
        fake_page_repo: FakePageRepository,
        fake_scoring_repo: FakeScoringRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
        sample_score: ShopScore,
    ) -> None:
        """Test execution creates snapshots for pages with scores."""
        # Setup
        await fake_page_repo.save(sample_page)
        await fake_scoring_repo.save(sample_score)

        # Execute
        result = await use_case.execute()

        # Verify result
        assert result.pages_processed == 1
        assert result.snapshots_written == 1
        assert result.errors_count == 0

        # Verify snapshot was created
        assert len(fake_page_metrics_repo.upsert_calls) == 1
        assert len(fake_page_metrics_repo.upsert_calls[0]) == 1

        snapshot = fake_page_metrics_repo.upsert_calls[0][0]
        assert snapshot.page_id == sample_page.id
        assert snapshot.shop_score == sample_score.score
        assert snapshot.tier == sample_score.tier

    @pytest.mark.asyncio
    async def test_execute_skips_pages_without_scores(
        self,
        use_case: RecordDailyMetricsForAllPagesUseCase,
        fake_page_repo: FakePageRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
    ) -> None:
        """Test execution skips pages without scores."""
        # Setup - page without score
        await fake_page_repo.save(sample_page)

        # Execute
        result = await use_case.execute()

        # Verify - page processed but no snapshot
        assert result.pages_processed == 1
        assert result.snapshots_written == 0

    @pytest.mark.asyncio
    async def test_execute_with_custom_date(
        self,
        use_case: RecordDailyMetricsForAllPagesUseCase,
        fake_page_repo: FakePageRepository,
        fake_scoring_repo: FakeScoringRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
        sample_score: ShopScore,
    ) -> None:
        """Test execution with custom snapshot date."""
        # Setup
        await fake_page_repo.save(sample_page)
        await fake_scoring_repo.save(sample_score)

        custom_date = date(2024, 1, 15)

        # Execute
        result = await use_case.execute(snapshot_date=custom_date)

        # Verify date
        assert result.snapshot_date == custom_date

        snapshot = fake_page_metrics_repo.upsert_calls[0][0]
        assert snapshot.date == custom_date

    @pytest.mark.asyncio
    async def test_execute_includes_products_count(
        self,
        use_case: RecordDailyMetricsForAllPagesUseCase,
        fake_page_repo: FakePageRepository,
        fake_scoring_repo: FakeScoringRepository,
        fake_product_repo: FakeProductRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
        sample_score: ShopScore,
    ) -> None:
        """Test execution includes products count in snapshot."""
        from src.app.core.domain.entities.product import Product

        # Setup page and score
        await fake_page_repo.save(sample_page)
        await fake_scoring_repo.save(sample_score)

        # Add some products
        products = [
            Product(
                id=str(uuid4()),
                page_id=sample_page.id,
                handle=f"product-{i}",
                title=f"Product {i}",
                url=f"https://example.com/product-{i}",
                available=True,
                tags=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(5)
        ]
        await fake_product_repo.upsert_many(products)

        # Execute
        result = await use_case.execute()

        # Verify products count
        assert result.snapshots_written == 1
        snapshot = fake_page_metrics_repo.upsert_calls[0][0]
        assert snapshot.products_count == 5


# =============================================================================
# GetPageMetricsHistoryUseCase Tests
# =============================================================================


class TestGetPageMetricsHistoryUseCase:
    """Tests for GetPageMetricsHistoryUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_page_repo: FakePageRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        fake_logger: FakeLoggingPort,
    ) -> GetPageMetricsHistoryUseCase:
        """Create use case instance with fake dependencies."""
        return GetPageMetricsHistoryUseCase(
            page_repository=fake_page_repo,
            page_metrics_repository=fake_page_metrics_repo,
            logger=fake_logger,
        )

    @pytest.fixture
    def sample_page(self) -> Page:
        """Create a sample page for testing."""
        return Page.create(
            id="page-456",
            url=Url("https://test-store.com"),
            country=Country("FR"),
            category=Category("electronics"),
        )

    @pytest.fixture
    def sample_metrics(self, sample_page: Page) -> list[PageDailyMetrics]:
        """Create sample metrics for testing."""
        base_date = date(2024, 1, 1)
        return [
            PageDailyMetrics.create(
                id=str(uuid4()),
                page_id=sample_page.id,
                snapshot_date=base_date + timedelta(days=i),
                ads_count=10 + i * 2,
                shop_score=50.0 + i * 5,
                products_count=100 + i * 10,
            )
            for i in range(10)
        ]

    @pytest.mark.asyncio
    async def test_execute_page_not_found(
        self,
        use_case: GetPageMetricsHistoryUseCase,
    ) -> None:
        """Test execution raises error for non-existent page."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(page_id="non-existent")

        assert "Page" in str(exc_info.value)
        assert "non-existent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_returns_empty_history(
        self,
        use_case: GetPageMetricsHistoryUseCase,
        fake_page_repo: FakePageRepository,
        sample_page: Page,
    ) -> None:
        """Test execution returns empty history for page without metrics."""
        await fake_page_repo.save(sample_page)

        result = await use_case.execute(page_id=sample_page.id)

        assert result.page_id == sample_page.id
        assert result.metrics == []
        assert result.count == 0

    @pytest.mark.asyncio
    async def test_execute_returns_metrics_history(
        self,
        use_case: GetPageMetricsHistoryUseCase,
        fake_page_repo: FakePageRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
        sample_metrics: list[PageDailyMetrics],
    ) -> None:
        """Test execution returns metrics history ordered by date ASC."""
        # Setup
        await fake_page_repo.save(sample_page)
        await fake_page_metrics_repo.upsert_daily_metrics(sample_metrics)

        # Execute
        result = await use_case.execute(page_id=sample_page.id)

        # Verify
        assert result.page_id == sample_page.id
        assert len(result.metrics) == 10

        # Verify ordering (date ASC)
        for i in range(len(result.metrics) - 1):
            assert result.metrics[i].date < result.metrics[i + 1].date

    @pytest.mark.asyncio
    async def test_execute_with_date_filter(
        self,
        use_case: GetPageMetricsHistoryUseCase,
        fake_page_repo: FakePageRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
        sample_metrics: list[PageDailyMetrics],
    ) -> None:
        """Test execution with date range filter."""
        # Setup
        await fake_page_repo.save(sample_page)
        await fake_page_metrics_repo.upsert_daily_metrics(sample_metrics)

        # Execute with date filter (days 3-6)
        date_from = date(2024, 1, 4)
        date_to = date(2024, 1, 7)

        result = await use_case.execute(
            page_id=sample_page.id,
            date_from=date_from,
            date_to=date_to,
        )

        # Verify - should have 4 metrics (Jan 4, 5, 6, 7)
        assert len(result.metrics) == 4
        assert result.metrics[0].date == date_from
        assert result.metrics[-1].date == date_to

    @pytest.mark.asyncio
    async def test_execute_with_limit(
        self,
        use_case: GetPageMetricsHistoryUseCase,
        fake_page_repo: FakePageRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
        sample_metrics: list[PageDailyMetrics],
    ) -> None:
        """Test execution with limit."""
        # Setup
        await fake_page_repo.save(sample_page)
        await fake_page_metrics_repo.upsert_daily_metrics(sample_metrics)

        # Execute with limit
        result = await use_case.execute(page_id=sample_page.id, limit=5)

        # Verify
        assert len(result.metrics) == 5

    @pytest.mark.asyncio
    async def test_execute_default_limit_applied(
        self,
        use_case: GetPageMetricsHistoryUseCase,
        fake_page_repo: FakePageRepository,
        fake_page_metrics_repo: FakePageMetricsRepository,
        sample_page: Page,
    ) -> None:
        """Test that default limit of 90 is applied when limit exceeds it."""
        # Create many metrics (more than 90)
        await fake_page_repo.save(sample_page)

        many_metrics = [
            PageDailyMetrics.create(
                id=str(uuid4()),
                page_id=sample_page.id,
                snapshot_date=date(2024, 1, 1) + timedelta(days=i),
                ads_count=10,
                shop_score=50.0,
            )
            for i in range(100)
        ]
        await fake_page_metrics_repo.upsert_daily_metrics(many_metrics)

        # Execute with limit > 90
        result = await use_case.execute(page_id=sample_page.id, limit=200)

        # Should be capped at 90
        assert len(result.metrics) == 90


# =============================================================================
# PageDailyMetrics Entity Tests
# =============================================================================


class TestPageDailyMetricsEntity:
    """Tests for PageDailyMetrics entity."""

    def test_create_with_valid_data(self) -> None:
        """Test creating a PageDailyMetrics with valid data."""
        metric = PageDailyMetrics.create(
            id="metric-123",
            page_id="page-123",
            snapshot_date=date(2024, 1, 15),
            ads_count=42,
            shop_score=75.5,
            products_count=100,
        )

        assert metric.id == "metric-123"
        assert metric.page_id == "page-123"
        assert metric.date == date(2024, 1, 15)
        assert metric.ads_count == 42
        assert metric.shop_score == 75.5
        assert metric.tier == score_to_tier(75.5)
        assert metric.products_count == 100

    def test_tier_computed_from_score(self) -> None:
        """Test that tier is automatically computed from score."""
        metric = PageDailyMetrics.create(
            id="metric-1",
            page_id="page-1",
            snapshot_date=date.today(),
            ads_count=10,
            shop_score=90.0,  # Should be XXL tier
        )

        assert metric.tier == "XXL"

    def test_score_clamped_to_valid_range(self) -> None:
        """Test that score is clamped to 0-100 range."""
        # Score above 100
        metric_high = PageDailyMetrics.create(
            id="metric-1",
            page_id="page-1",
            snapshot_date=date.today(),
            ads_count=10,
            shop_score=150.0,
        )
        assert metric_high.shop_score == 100.0

        # Score below 0
        metric_low = PageDailyMetrics.create(
            id="metric-2",
            page_id="page-2",
            snapshot_date=date.today(),
            ads_count=10,
            shop_score=-10.0,
        )
        assert metric_low.shop_score == 0.0

    def test_is_high_performing(self) -> None:
        """Test high performing check."""
        high_metric = PageDailyMetrics.create(
            id="metric-1",
            page_id="page-1",
            snapshot_date=date.today(),
            ads_count=10,
            shop_score=80.0,
        )
        low_metric = PageDailyMetrics.create(
            id="metric-2",
            page_id="page-2",
            snapshot_date=date.today(),
            ads_count=10,
            shop_score=50.0,
        )

        assert high_metric.is_high_performing() is True
        assert low_metric.is_high_performing() is False

    def test_has_active_ads(self) -> None:
        """Test active ads check."""
        with_ads = PageDailyMetrics.create(
            id="metric-1",
            page_id="page-1",
            snapshot_date=date.today(),
            ads_count=10,
            shop_score=50.0,
        )
        without_ads = PageDailyMetrics.create(
            id="metric-2",
            page_id="page-2",
            snapshot_date=date.today(),
            ads_count=0,
            shop_score=50.0,
        )

        assert with_ads.has_active_ads() is True
        assert without_ads.has_active_ads() is False


# =============================================================================
# PageMetricsHistoryResult Tests
# =============================================================================


class TestPageMetricsHistoryResult:
    """Tests for PageMetricsHistoryResult value object."""

    def test_empty_result(self) -> None:
        """Test empty result properties."""
        result = PageMetricsHistoryResult(page_id="page-1", metrics=[])

        assert result.count == 0
        assert result.first_date is None
        assert result.last_date is None
        assert result.score_trend is None
        assert result.ads_trend is None

    def test_score_trend(self) -> None:
        """Test score trend calculation."""
        metrics = [
            PageDailyMetrics.create(
                id="m1",
                page_id="page-1",
                snapshot_date=date(2024, 1, 1),
                ads_count=10,
                shop_score=50.0,
            ),
            PageDailyMetrics.create(
                id="m2",
                page_id="page-1",
                snapshot_date=date(2024, 1, 2),
                ads_count=20,
                shop_score=75.0,
            ),
        ]

        result = PageMetricsHistoryResult(page_id="page-1", metrics=metrics)

        assert result.score_trend == 25.0  # 75 - 50
        assert result.ads_trend == 10  # 20 - 10

    def test_first_and_last_date(self) -> None:
        """Test first and last date properties."""
        metrics = [
            PageDailyMetrics.create(
                id="m1",
                page_id="page-1",
                snapshot_date=date(2024, 1, 10),
                ads_count=10,
                shop_score=50.0,
            ),
            PageDailyMetrics.create(
                id="m2",
                page_id="page-1",
                snapshot_date=date(2024, 1, 20),
                ads_count=20,
                shop_score=75.0,
            ),
        ]

        result = PageMetricsHistoryResult(page_id="page-1", metrics=metrics)

        assert result.first_date == date(2024, 1, 10)
        assert result.last_date == date(2024, 1, 20)

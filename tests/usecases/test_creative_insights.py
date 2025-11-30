"""Tests for Creative Insights Use Cases.

Tests the AnalyzeAdCreativeUseCase and BuildPageCreativeInsightsUseCase.
"""

import pytest
from datetime import datetime, timezone

from src.app.core.domain import (
    Page,
    Ad,
    AdStatus,
    Url,
    PageState,
    PageStatus,
    EntityNotFoundError,
)
from src.app.core.domain.entities.creative_analysis import (
    CreativeAnalysis,
    PageCreativeInsights,
)
from src.app.core.usecases.creative_insights import (
    AnalyzeAdCreativeUseCase,
    BuildPageCreativeInsightsUseCase,
)
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeAdsRepository,
    FakeCreativeAnalysisRepository,
    FakeCreativeTextAnalyzer,
)


class TestAnalyzeAdCreativeUseCase:
    """Tests for AnalyzeAdCreativeUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        fake_creative_text_analyzer: FakeCreativeTextAnalyzer,
        fake_logger: FakeLoggingPort,
    ) -> AnalyzeAdCreativeUseCase:
        """Create use case with mocked dependencies."""
        return AnalyzeAdCreativeUseCase(
            ads_repository=fake_ads_repo,
            creative_analysis_repository=fake_creative_analysis_repo,
            text_analyzer=fake_creative_text_analyzer,
            logger=fake_logger,
        )

    @pytest.fixture
    def sample_ad(self) -> Ad:
        """Create a sample ad for testing."""
        return Ad(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            title="Amazing Product - Buy Now!",
            body="This is the best product ever. Free shipping!",
            status=AdStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    @pytest.mark.asyncio
    async def test_analyze_new_ad_success(
        self,
        use_case: AnalyzeAdCreativeUseCase,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        sample_ad: Ad,
    ) -> None:
        """Test successful analysis of a new ad using execute_for_ad."""
        # Use execute_for_ad which takes the ad entity directly
        result = await use_case.execute_for_ad(ad=sample_ad)

        assert result.ad_id == "ad-1"
        assert isinstance(result.analysis, CreativeAnalysis)
        assert result.analysis.ad_id == "ad-1"
        assert result.analysis.creative_score >= 0.0
        assert result.analysis.creative_score <= 100.0
        assert result.was_cached is False

        # Verify analysis was saved
        saved = await fake_creative_analysis_repo.get_by_ad_id("ad-1")
        assert saved is not None
        assert saved.ad_id == "ad-1"

    @pytest.mark.asyncio
    async def test_analyze_cached_ad(
        self,
        use_case: AnalyzeAdCreativeUseCase,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        sample_ad: Ad,
    ) -> None:
        """Test that existing analysis is returned (idempotent)."""
        # Create existing analysis
        existing_analysis = CreativeAnalysis(
            id="analysis-1",
            ad_id="ad-1",
            creative_score=85.0,
            style_tags=["bold"],
            angle_tags=["urgency"],
            tone_tags=["casual"],
            sentiment="positive",
            analysis_version="v1.0",
            created_at=datetime.now(timezone.utc),
        )
        await fake_creative_analysis_repo.save(existing_analysis)

        # Use execute_for_ad - should return cached analysis
        result = await use_case.execute_for_ad(ad=sample_ad)

        assert result.was_cached is True
        assert result.analysis.id == "analysis-1"
        assert result.analysis.creative_score == 85.0

    @pytest.mark.asyncio
    async def test_analyze_ad_not_found_via_execute(
        self,
        use_case: AnalyzeAdCreativeUseCase,
    ) -> None:
        """Test that execute (by ad_id) raises error since get_by_id not available."""
        # execute() method raises EntityNotFoundError because
        # it can't look up ads by ID
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(ad_id="nonexistent")

        assert exc_info.value.value == "nonexistent"

    @pytest.mark.asyncio
    async def test_analyze_ad_with_no_text(
        self,
        use_case: AnalyzeAdCreativeUseCase,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
    ) -> None:
        """Test analyzing ad with no text content."""
        ad_no_text = Ad(
            id="ad-no-text",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-2",
            title=None,
            body=None,
            status=AdStatus.ACTIVE,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Use execute_for_ad
        result = await use_case.execute_for_ad(ad=ad_no_text)

        # Analysis should still be created (fake analyzer returns default score)
        assert result.analysis is not None
        assert result.analysis.ad_id == "ad-no-text"
        # Note: Fake analyzer returns its default_score regardless of input
        # Real HeuristicCreativeTextAnalyzer would return 0.0 for empty text


class TestBuildPageCreativeInsightsUseCase:
    """Tests for BuildPageCreativeInsightsUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        fake_creative_text_analyzer: FakeCreativeTextAnalyzer,
        fake_logger: FakeLoggingPort,
    ) -> BuildPageCreativeInsightsUseCase:
        """Create use case with mocked dependencies."""
        return BuildPageCreativeInsightsUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            creative_analysis_repository=fake_creative_analysis_repo,
            text_analyzer=fake_creative_text_analyzer,
            logger=fake_logger,
        )

    @pytest.fixture
    def sample_page(self) -> Page:
        """Create a sample page for testing."""
        page = Page.create(id="page-1", url=Url("https://test-store.com"))
        return Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=PageState(status=PageStatus.VERIFIED_SHOPIFY),
            is_shopify=True,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

    @pytest.fixture
    def sample_ads(self) -> list[Ad]:
        """Create sample ads for testing."""
        return [
            Ad(
                id=f"ad-{i}",
                page_id="page-1",
                meta_page_id="meta-1",
                meta_ad_id=f"meta-ad-{i}",
                title=f"Product {i} - Great Deal!",
                body=f"Buy product {i} today and save!",
                status=AdStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

    @pytest.mark.asyncio
    async def test_build_insights_success(
        self,
        use_case: BuildPageCreativeInsightsUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        sample_page: Page,
        sample_ads: list[Ad],
    ) -> None:
        """Test successful insights building."""
        await fake_page_repo.save(sample_page)
        await fake_ads_repo.save_many(sample_ads)

        result = await use_case.execute(page_id="page-1", top_n=3)

        assert result.page_id == "page-1"
        assert result.ads_analyzed == 5
        assert isinstance(result.insights, PageCreativeInsights)
        assert result.insights.page_id == "page-1"
        assert result.insights.total_analyzed == 5
        assert len(result.insights.top_creatives) <= 3  # top_n=3

    @pytest.mark.asyncio
    async def test_build_insights_page_not_found(
        self,
        use_case: BuildPageCreativeInsightsUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute(page_id="nonexistent")

        assert exc_info.value.value == "nonexistent"

    @pytest.mark.asyncio
    async def test_build_insights_no_ads(
        self,
        use_case: BuildPageCreativeInsightsUseCase,
        fake_page_repo: FakePageRepository,
        sample_page: Page,
    ) -> None:
        """Test handling when no ads exist."""
        await fake_page_repo.save(sample_page)

        result = await use_case.execute(page_id="page-1")

        assert result.page_id == "page-1"
        assert result.ads_analyzed == 0
        assert result.insights.avg_score == 0.0
        assert result.insights.best_score == 0.0
        assert len(result.insights.top_creatives) == 0

    @pytest.mark.asyncio
    async def test_build_insights_quality_tier_excellent(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        fake_logger: FakeLoggingPort,
        sample_page: Page,
        sample_ads: list[Ad],
    ) -> None:
        """Test that high scores result in excellent tier."""
        # Create use case with high-score analyzer
        high_score_analyzer = FakeCreativeTextAnalyzer(default_score=85.0)
        use_case = BuildPageCreativeInsightsUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            creative_analysis_repository=fake_creative_analysis_repo,
            text_analyzer=high_score_analyzer,
            logger=fake_logger,
        )

        await fake_page_repo.save(sample_page)
        await fake_ads_repo.save_many(sample_ads)

        result = await use_case.execute(page_id="page-1")

        assert result.insights.quality_tier == "excellent"

    @pytest.mark.asyncio
    async def test_build_insights_quality_tier_good(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        fake_logger: FakeLoggingPort,
        sample_page: Page,
        sample_ads: list[Ad],
    ) -> None:
        """Test that medium-high scores result in good tier."""
        good_score_analyzer = FakeCreativeTextAnalyzer(default_score=65.0)
        use_case = BuildPageCreativeInsightsUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            creative_analysis_repository=fake_creative_analysis_repo,
            text_analyzer=good_score_analyzer,
            logger=fake_logger,
        )

        await fake_page_repo.save(sample_page)
        await fake_ads_repo.save_many(sample_ads)

        result = await use_case.execute(page_id="page-1")

        assert result.insights.quality_tier == "good"

    @pytest.mark.asyncio
    async def test_build_insights_quality_tier_average(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        fake_logger: FakeLoggingPort,
        sample_page: Page,
        sample_ads: list[Ad],
    ) -> None:
        """Test that medium scores result in average tier."""
        avg_score_analyzer = FakeCreativeTextAnalyzer(default_score=45.0)
        use_case = BuildPageCreativeInsightsUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            creative_analysis_repository=fake_creative_analysis_repo,
            text_analyzer=avg_score_analyzer,
            logger=fake_logger,
        )

        await fake_page_repo.save(sample_page)
        await fake_ads_repo.save_many(sample_ads)

        result = await use_case.execute(page_id="page-1")

        assert result.insights.quality_tier == "average"

    @pytest.mark.asyncio
    async def test_build_insights_quality_tier_poor(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        fake_logger: FakeLoggingPort,
        sample_page: Page,
        sample_ads: list[Ad],
    ) -> None:
        """Test that low scores result in poor tier."""
        poor_score_analyzer = FakeCreativeTextAnalyzer(default_score=25.0)
        use_case = BuildPageCreativeInsightsUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            creative_analysis_repository=fake_creative_analysis_repo,
            text_analyzer=poor_score_analyzer,
            logger=fake_logger,
        )

        await fake_page_repo.save(sample_page)
        await fake_ads_repo.save_many(sample_ads)

        result = await use_case.execute(page_id="page-1")

        assert result.insights.quality_tier == "poor"

    @pytest.mark.asyncio
    async def test_build_insights_top_creatives_sorted(
        self,
        use_case: BuildPageCreativeInsightsUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        sample_page: Page,
    ) -> None:
        """Test that top creatives are sorted by score descending."""
        await fake_page_repo.save(sample_page)

        # Create ads
        ads = [
            Ad(
                id=f"ad-{i}",
                page_id="page-1",
                meta_page_id="meta-1",
                meta_ad_id=f"meta-ad-{i}",
                title=f"Ad {i}",
                body=f"Body {i}",
                status=AdStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        await fake_ads_repo.save_many(ads)

        # Pre-create analyses with different scores (deliberately unsorted)
        scores = [50.0, 90.0, 70.0]
        for i, score in enumerate(scores):
            analysis = CreativeAnalysis(
                id=f"analysis-{i}",
                ad_id=f"ad-{i}",
                creative_score=score,
                style_tags=[],
                angle_tags=[],
                tone_tags=[],
                sentiment="neutral",
                analysis_version="v1.0",
                created_at=datetime.now(timezone.utc),
            )
            await fake_creative_analysis_repo.save(analysis)

        result = await use_case.execute(page_id="page-1", top_n=3)

        # Verify sorted by score DESC
        top_scores = [c.creative_score for c in result.insights.top_creatives]
        assert top_scores == sorted(top_scores, reverse=True)
        assert top_scores[0] == 90.0
        assert top_scores[1] == 70.0
        assert top_scores[2] == 50.0

    @pytest.mark.asyncio
    async def test_build_insights_calculates_averages(
        self,
        use_case: BuildPageCreativeInsightsUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_creative_analysis_repo: FakeCreativeAnalysisRepository,
        sample_page: Page,
    ) -> None:
        """Test that average and best scores are calculated correctly."""
        await fake_page_repo.save(sample_page)

        ads = [
            Ad(
                id=f"ad-{i}",
                page_id="page-1",
                meta_page_id="meta-1",
                meta_ad_id=f"meta-ad-{i}",
                title=f"Ad {i}",
                body=f"Body {i}",
                status=AdStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(3)
        ]
        await fake_ads_repo.save_many(ads)

        # Pre-create analyses with known scores
        scores = [60.0, 80.0, 100.0]
        for i, score in enumerate(scores):
            analysis = CreativeAnalysis(
                id=f"analysis-{i}",
                ad_id=f"ad-{i}",
                creative_score=score,
                style_tags=[],
                angle_tags=[],
                tone_tags=[],
                sentiment="neutral",
                analysis_version="v1.0",
                created_at=datetime.now(timezone.utc),
            )
            await fake_creative_analysis_repo.save(analysis)

        result = await use_case.execute(page_id="page-1")

        # Average: (60 + 80 + 100) / 3 = 80.0
        assert result.insights.avg_score == 80.0
        # Best score
        assert result.insights.best_score == 100.0

    @pytest.mark.asyncio
    async def test_build_insights_logs_operations(
        self,
        use_case: BuildPageCreativeInsightsUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_logger: FakeLoggingPort,
        sample_page: Page,
        sample_ads: list[Ad],
    ) -> None:
        """Test that operations are properly logged."""
        await fake_page_repo.save(sample_page)
        await fake_ads_repo.save_many(sample_ads)

        await use_case.execute(page_id="page-1")

        log_messages = [log["msg"] for log in fake_logger.logs]
        assert any("Building" in msg for msg in log_messages)
        assert any("built" in msg or "insights" in msg.lower() for msg in log_messages)

"""Tests for ComputeShopScoreUseCase.

Tests the shop scoring use case with mocked ports.
Tests cover three main scenarios:
1. High-activity shop (expected score ~80-100)
2. Medium-activity shop (expected score ~40-70)
3. Low-activity shop (expected score <30)
"""

import pytest

from src.app.core.domain import (
    Page,
    Ad,
    AdStatus,
    AdPlatform,
    Url,
    Country,
    Currency,
    ProductCount,
    EntityNotFoundError,
)
from src.app.core.usecases import (
    ComputeShopScoreUseCase,
    ComputeShopScoreResult,
)
from src.app.core.usecases.compute_shop_score import (
    _calc_ads_activity_score,
    _calc_shopify_score,
    _calc_creative_quality_score,
    _calc_catalog_score,
    _clamp,
)
from tests.conftest import (
    FakeLoggingPort,
    FakePageRepository,
    FakeAdsRepository,
    FakeScoringRepository,
)


class TestComputeShopScoreUseCase:
    """Tests for ComputeShopScoreUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scoring_repo: FakeScoringRepository,
        fake_logger: FakeLoggingPort,
    ) -> ComputeShopScoreUseCase:
        """Create use case with mocked dependencies."""
        return ComputeShopScoreUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            scoring_repository=fake_scoring_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_high_activity_shop(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test scoring for a highly active shop.

        Scenario:
        - 60 ads (normalized: 1.0)
        - Multiple countries (US, FR, DE, GB, ES) => diversity 1.0
        - Multiple platforms (FB, IG, Messenger) => diversity 1.0
        - Confirmed Shopify store
        - Strong currency (EUR)
        - Active ads > 0
        - High total ads
        - Creative quality: has %, emoji, CTA, text, cta_type
        - Large catalog (300 products)

        Expected global score: ~80-100
        """
        # Create page with strong Shopify signals
        page = Page(
            id="high-activity-page",
            url=Url("https://high-activity-store.com"),
            domain="high-activity-store.com",
            is_shopify=True,
            currency=Currency("EUR"),
            product_count=ProductCount(300),
            active_ads_count=60,
            total_ads_count=100,
        )
        await fake_page_repo.save(page)

        # Create many ads with diverse targeting and quality content
        countries = [
            Country("US"),
            Country("FR"),
            Country("DE"),
            Country("GB"),
            Country("ES"),
        ]
        platforms = [AdPlatform.FACEBOOK, AdPlatform.INSTAGRAM, AdPlatform.MESSENGER]

        ads = []
        for i in range(60):
            ad = Ad(
                id=f"ad-{i}",
                page_id="high-activity-page",
                meta_page_id="meta-123",
                meta_ad_id=f"meta-ad-{i}",
                title=f"🔥 50% OFF! Shop Now! Amazing Deal #{i}",
                body="Get yours today! Limited time offer. Buy now and save!",
                cta_type="shop_now",
                status=AdStatus.ACTIVE,
                platforms=platforms,
                countries=countries,
            )
            ads.append(ad)

        await fake_ads_repo.save_many(ads)

        # Execute
        result = await use_case.execute("high-activity-page")

        # Verify result
        assert isinstance(result, ComputeShopScoreResult)
        assert result.page_id == "high-activity-page"
        assert result.global_score >= 80.0, f"Expected >= 80, got {result.global_score}"

        # Verify components are all high
        assert result.components["ads_activity"] >= 90.0
        assert result.components["shopify"] >= 80.0
        assert result.components["creative_quality"] >= 80.0
        assert result.components["catalog"] >= 100.0

        # Verify score was persisted
        assert len(fake_scoring_repo.scores) == 1
        assert fake_scoring_repo.scores[0].score == result.global_score

    @pytest.mark.asyncio
    async def test_medium_activity_shop(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test scoring for a medium activity shop.

        Scenario:
        - 15 ads (normalized: 0.3)
        - 2 countries (US, CA)
        - 1 platform (FB)
        - Confirmed Shopify store
        - Non-premium currency (CAD)
        - Some active ads
        - Basic creative (text, no %, no emoji)
        - Medium catalog (80 products)

        Expected global score: ~40-70
        """
        page = Page(
            id="medium-activity-page",
            url=Url("https://medium-store.com"),
            domain="medium-store.com",
            is_shopify=True,
            currency=Currency("CAD"),
            product_count=ProductCount(80),
            active_ads_count=15,
            total_ads_count=20,
        )
        await fake_page_repo.save(page)

        countries = [Country("US"), Country("CA")]
        platforms = [AdPlatform.FACEBOOK]

        ads = []
        for i in range(15):
            ad = Ad(
                id=f"ad-{i}",
                page_id="medium-activity-page",
                meta_page_id="meta-456",
                meta_ad_id=f"meta-ad-{i}",
                title=f"Check out our products #{i}",
                body="Great products for you.",
                cta_type="learn_more",
                status=AdStatus.ACTIVE,
                platforms=platforms,
                countries=countries,
            )
            ads.append(ad)

        await fake_ads_repo.save_many(ads)

        result = await use_case.execute("medium-activity-page")

        assert result.global_score >= 40.0
        assert result.global_score <= 70.0

        # Verify components are medium
        assert result.components["ads_activity"] >= 20.0
        assert result.components["ads_activity"] <= 50.0
        assert result.components["shopify"] >= 50.0  # Shopify + active ads
        assert result.components["catalog"] >= 30.0

    @pytest.mark.asyncio
    async def test_low_activity_shop(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test scoring for a low activity / inactive shop.

        Scenario:
        - 1 ad only
        - 1 country
        - 1 platform
        - Not Shopify
        - No premium currency
        - No active ads
        - Minimal creative (no title, no CTA)
        - Very small catalog (5 products)

        Expected global score: <30
        """
        page = Page(
            id="low-activity-page",
            url=Url("https://low-store.com"),
            domain="low-store.com",
            is_shopify=False,
            currency=None,
            product_count=ProductCount(5),
            active_ads_count=0,
            total_ads_count=1,
        )
        await fake_page_repo.save(page)

        # Single poor-quality ad
        ad = Ad(
            id="ad-0",
            page_id="low-activity-page",
            meta_page_id="meta-789",
            meta_ad_id="meta-ad-0",
            title=None,  # No title
            body=None,  # No body
            cta_type=None,  # No CTA
            status=AdStatus.INACTIVE,
            platforms=[AdPlatform.FACEBOOK],
            countries=[Country("US")],
        )
        await fake_ads_repo.save_many([ad])

        result = await use_case.execute("low-activity-page")

        assert result.global_score < 30.0, f"Expected < 30, got {result.global_score}"

        # Verify components are low
        assert result.components["ads_activity"] < 20.0
        assert result.components["shopify"] <= 30.0  # Only base score, not Shopify
        assert result.components["creative_quality"] == 0.0  # No content
        assert result.components["catalog"] < 10.0

    @pytest.mark.asyncio
    async def test_page_not_found(
        self,
        use_case: ComputeShopScoreUseCase,
    ) -> None:
        """Test error when page not found."""
        with pytest.raises(EntityNotFoundError) as exc_info:
            await use_case.execute("nonexistent-page")
        assert "Page" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_ads(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test scoring with zero ads."""
        page = Page(
            id="no-ads-page",
            url=Url("https://no-ads-store.com"),
            domain="no-ads-store.com",
            is_shopify=True,
            currency=Currency("USD"),
            product_count=ProductCount(50),
            active_ads_count=0,
            total_ads_count=0,
        )
        await fake_page_repo.save(page)

        result = await use_case.execute("no-ads-page")

        # Ads activity and creative quality should be 0
        assert result.components["ads_activity"] == 0.0
        assert result.components["creative_quality"] == 0.0
        # Shopify and catalog should still contribute
        assert result.components["shopify"] > 0.0
        assert result.components["catalog"] > 0.0

    @pytest.mark.asyncio
    async def test_score_ordering(
        self,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
        fake_scoring_repo: FakeScoringRepository,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Test that high > medium > low scores."""
        use_case = ComputeShopScoreUseCase(
            page_repository=fake_page_repo,
            ads_repository=fake_ads_repo,
            scoring_repository=fake_scoring_repo,
            logger=fake_logger,
        )

        # High activity page
        high_page = Page(
            id="high-page",
            url=Url("https://high.com"),
            domain="high.com",
            is_shopify=True,
            currency=Currency("USD"),
            product_count=ProductCount(200),
            active_ads_count=50,
            total_ads_count=100,
        )
        await fake_page_repo.save(high_page)

        high_ads = [
            Ad(
                id=f"high-ad-{i}",
                page_id="high-page",
                meta_page_id="m1",
                meta_ad_id=f"high-{i}",
                title="🔥 50% off! Shop now!",
                body="Amazing deals!",
                cta_type="shop_now",
                platforms=[AdPlatform.FACEBOOK, AdPlatform.INSTAGRAM],
                countries=[Country("US"), Country("GB"), Country("DE")],
            )
            for i in range(50)
        ]
        await fake_ads_repo.save_many(high_ads)

        # Medium activity page
        medium_page = Page(
            id="medium-page",
            url=Url("https://medium.com"),
            domain="medium.com",
            is_shopify=True,
            currency=Currency("CAD"),
            product_count=ProductCount(50),
            active_ads_count=10,
            total_ads_count=15,
        )
        await fake_page_repo.save(medium_page)

        medium_ads = [
            Ad(
                id=f"med-ad-{i}",
                page_id="medium-page",
                meta_page_id="m2",
                meta_ad_id=f"med-{i}",
                title="Products available",
                body="Check them out",
                platforms=[AdPlatform.FACEBOOK],
                countries=[Country("US")],
            )
            for i in range(10)
        ]
        await fake_ads_repo.save_many(medium_ads)

        # Low activity page
        low_page = Page(
            id="low-page",
            url=Url("https://low.com"),
            domain="low.com",
            is_shopify=False,
            product_count=ProductCount(0),
            active_ads_count=0,
            total_ads_count=0,
        )
        await fake_page_repo.save(low_page)

        # Execute all
        high_result = await use_case.execute("high-page")
        medium_result = await use_case.execute("medium-page")
        low_result = await use_case.execute("low-page")

        # Verify ordering
        assert high_result.global_score > medium_result.global_score
        assert medium_result.global_score > low_result.global_score

    @pytest.mark.asyncio
    async def test_score_persistence(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_scoring_repo: FakeScoringRepository,
    ) -> None:
        """Test that score is properly persisted."""
        page = Page(
            id="persist-test-page",
            url=Url("https://persist-test.com"),
            domain="persist-test.com",
        )
        await fake_page_repo.save(page)

        result = await use_case.execute("persist-test-page")

        # Verify persistence
        assert len(fake_scoring_repo.scores) == 1
        saved_score = fake_scoring_repo.scores[0]
        assert saved_score.page_id == "persist-test-page"
        assert saved_score.score == result.global_score
        assert saved_score.components == result.components


class TestScoreCalculationFunctions:
    """Tests for individual score calculation functions."""

    def test_clamp(self) -> None:
        """Test _clamp function."""
        assert _clamp(50.0) == 50.0
        assert _clamp(-10.0) == 0.0
        assert _clamp(150.0) == 100.0
        assert _clamp(0.0) == 0.0
        assert _clamp(100.0) == 100.0

    def test_ads_activity_score_no_ads(self) -> None:
        """Test ads activity score with no ads."""
        assert _calc_ads_activity_score([]) == 0.0

    def test_ads_activity_score_max_ads(self) -> None:
        """Test ads activity score with many ads and high diversity."""
        countries = [
            Country("US"),
            Country("FR"),
            Country("DE"),
            Country("GB"),
            Country("ES"),
        ]
        platforms = [AdPlatform.FACEBOOK, AdPlatform.INSTAGRAM, AdPlatform.MESSENGER]

        ads = [
            Ad(
                id=f"ad-{i}",
                page_id="p1",
                meta_page_id="m1",
                meta_ad_id=f"m-{i}",
                platforms=platforms,
                countries=countries,
            )
            for i in range(60)
        ]

        score = _calc_ads_activity_score(ads)
        assert score >= 90.0  # Should be high due to max diversity

    def test_shopify_score_base(self) -> None:
        """Test shopify score base value."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            is_shopify=False,
        )
        score = _calc_shopify_score(page)
        assert score == 20.0  # Base score only

    def test_shopify_score_full(self) -> None:
        """Test shopify score with all bonuses."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            is_shopify=True,
            currency=Currency("USD"),
            active_ads_count=5,
            total_ads_count=15,
        )
        score = _calc_shopify_score(page)
        # Base (20) + Shopify (30) + Currency (20) + Active ads (20) + Total ads (10)
        assert score == 100.0

    def test_creative_quality_score_no_ads(self) -> None:
        """Test creative quality with no ads."""
        assert _calc_creative_quality_score([]) == 0.0

    def test_creative_quality_score_full_quality(self) -> None:
        """Test creative quality with all quality indicators."""
        ad = Ad(
            id="ad-1",
            page_id="p1",
            meta_page_id="m1",
            meta_ad_id="m1",
            title="🔥 50% OFF! Shop Now!",
            body="Great sale prices!",
            cta_type="shop_now",
        )
        score = _calc_creative_quality_score([ad])
        # Text (20) + % (20) + emoji (15) + CTA phrase (25) + CTA type (20) = 100
        assert score == 100.0

    def test_creative_quality_score_minimal(self) -> None:
        """Test creative quality with minimal content."""
        ad = Ad(
            id="ad-1",
            page_id="p1",
            meta_page_id="m1",
            meta_ad_id="m1",
            title="Product",
            body=None,
            cta_type=None,
        )
        score = _calc_creative_quality_score([ad])
        # Only text content (20)
        assert score == 20.0

    def test_catalog_score_zero(self) -> None:
        """Test catalog score with zero products."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            product_count=ProductCount(0),
        )
        score = _calc_catalog_score(page)
        assert score == 0.0

    def test_catalog_score_max(self) -> None:
        """Test catalog score with many products."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            product_count=ProductCount(200),
        )
        score = _calc_catalog_score(page)
        assert score == 100.0

    def test_catalog_score_partial(self) -> None:
        """Test catalog score with partial products."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            product_count=ProductCount(100),
        )
        score = _calc_catalog_score(page)
        assert score == 50.0  # 100/200 * 100

"""Tests for ComputeShopScoreUseCase.

Tests the shop scoring use case with mocked ports.
Tests cover three main scenarios:
1. High-activity shop (expected score ~80-100)
2. Medium-activity shop (expected score ~40-70)
3. Low-activity shop (expected score <30)

Additionally includes "snapshot" tests that serve as guard-rails
for the scoring formula, alerting on significant changes:
- test_snapshot_scoring_high_winner: Premium shop scoring XXL tier
- test_snapshot_scoring_dead_shop: Inactive shop scoring XS tier
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
        score, warning = _calc_catalog_score(page)
        assert score == 0.0
        assert warning is not None  # Should have warning for 0 products

    def test_catalog_score_max(self) -> None:
        """Test catalog score with many products."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            product_count=ProductCount(200),
        )
        score, warning = _calc_catalog_score(page)
        assert score == 100.0
        assert warning is None  # No warning for valid product count

    def test_catalog_score_partial(self) -> None:
        """Test catalog score with partial products."""
        page = Page(
            id="p1",
            url=Url("https://test.com"),
            domain="test.com",
            product_count=ProductCount(100),
        )
        score, warning = _calc_catalog_score(page)
        assert score == 50.0  # 100/200 * 100
        assert warning is None  # No warning for valid product count


class TestShopScoreTier:
    """Tests for ShopScore.tier property."""

    def test_tier_xxl(self) -> None:
        """Test XXL tier for score >= 85."""
        from src.app.core.domain.entities.shop_score import ShopScore

        score = ShopScore.create(id="1", page_id="p1", score=85.0)
        assert score.tier == "XXL"

        score = ShopScore.create(id="2", page_id="p1", score=100.0)
        assert score.tier == "XXL"

    def test_tier_xl(self) -> None:
        """Test XL tier for score >= 70 and < 85."""
        from src.app.core.domain.entities.shop_score import ShopScore

        score = ShopScore.create(id="1", page_id="p1", score=70.0)
        assert score.tier == "XL"

        score = ShopScore.create(id="2", page_id="p1", score=84.9)
        assert score.tier == "XL"

    def test_tier_l(self) -> None:
        """Test L tier for score >= 55 and < 70."""
        from src.app.core.domain.entities.shop_score import ShopScore

        score = ShopScore.create(id="1", page_id="p1", score=55.0)
        assert score.tier == "L"

        score = ShopScore.create(id="2", page_id="p1", score=69.9)
        assert score.tier == "L"

    def test_tier_m(self) -> None:
        """Test M tier for score >= 40 and < 55."""
        from src.app.core.domain.entities.shop_score import ShopScore

        score = ShopScore.create(id="1", page_id="p1", score=40.0)
        assert score.tier == "M"

        score = ShopScore.create(id="2", page_id="p1", score=54.9)
        assert score.tier == "M"

    def test_tier_s(self) -> None:
        """Test S tier for score >= 25 and < 40."""
        from src.app.core.domain.entities.shop_score import ShopScore

        score = ShopScore.create(id="1", page_id="p1", score=25.0)
        assert score.tier == "S"

        score = ShopScore.create(id="2", page_id="p1", score=39.9)
        assert score.tier == "S"

    def test_tier_xs(self) -> None:
        """Test XS tier for score < 25."""
        from src.app.core.domain.entities.shop_score import ShopScore

        score = ShopScore.create(id="1", page_id="p1", score=24.9)
        assert score.tier == "XS"

        score = ShopScore.create(id="2", page_id="p1", score=0.0)
        assert score.tier == "XS"


class TestScoringSnapshots:
    """Snapshot tests for ComputeShopScoreUseCase.

    These tests serve as guard-rails against unintended changes to the
    scoring formula. They test specific scenarios with well-defined
    expected score ranges and tier assignments.

    If these tests fail after a code change, it indicates that the
    scoring behavior has changed and should be reviewed for correctness.

    The tiering logic is sourced from core/domain/tiering.py which is
    the single source of truth for tier definitions.
    """

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
    async def test_snapshot_scoring_high_winner(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
    ) -> None:
        """Snapshot test: Premium high-performing shop should score XXL tier.

        This test represents an ideal "winner" shop with:
        - Strong advertising presence (60+ ads across multiple countries/platforms)
        - Confirmed Shopify store with premium currency (EUR/USD/GBP/AUD)
        - High-quality creative content (emojis, CTAs, discount indicators)
        - Large product catalog (300+ products)

        Expected behavior:
        - Global score: 85 <= score <= 100
        - Tier: XXL

        If this test fails, review the scoring formula changes to ensure
        high-quality shops are still properly recognized.
        """
        # Setup: Premium Shopify store with strong signals
        page = Page(
            id="snapshot-winner-page",
            url=Url("https://premium-winner-store.com"),
            domain="premium-winner-store.com",
            is_shopify=True,
            currency=Currency("EUR"),  # Strong premium currency
            product_count=ProductCount(350),  # Large catalog
            active_ads_count=60,
            total_ads_count=120,
        )
        await fake_page_repo.save(page)

        # High-diversity ad targeting
        countries = [
            Country("US"),
            Country("FR"),
            Country("DE"),
            Country("GB"),
            Country("AU"),
        ]
        platforms = [
            AdPlatform.FACEBOOK,
            AdPlatform.INSTAGRAM,
            AdPlatform.MESSENGER,
        ]

        # High-quality creative content
        ads = []
        for i in range(60):
            ad = Ad(
                id=f"winner-ad-{i}",
                page_id="snapshot-winner-page",
                meta_page_id="meta-winner",
                meta_ad_id=f"meta-winner-ad-{i}",
                title=f"🔥 50% OFF! Shop Now! #{i}",  # Emoji + % + CTA
                body="Get yours today! Limited offer. Buy now!",  # CTA phrases
                cta_type="shop_now",
                status=AdStatus.ACTIVE,
                platforms=platforms,
                countries=countries,
            )
            ads.append(ad)
        await fake_ads_repo.save_many(ads)

        # Execute
        result = await use_case.execute("snapshot-winner-page")

        # Snapshot assertions
        assert 85 <= result.global_score <= 100, (
            f"SNAPSHOT FAILURE: High-winner shop score {result.global_score} "
            f"outside expected range [85, 100]. "
            f"Components: {result.components}"
        )
        assert result.tier == "XXL", (
            f"SNAPSHOT FAILURE: High-winner shop tier '{result.tier}' "
            f"should be 'XXL' (score={result.global_score})"
        )

        # Component sanity checks (non-strict, for diagnostics)
        assert result.components["ads_activity"] >= 90.0, (
            f"Ads activity {result.components['ads_activity']} lower than expected"
        )
        assert result.components["shopify"] >= 80.0, (
            f"Shopify score {result.components['shopify']} lower than expected"
        )
        assert result.components["creative_quality"] >= 80.0, (
            f"Creative quality {result.components['creative_quality']} lower than expected"
        )
        assert result.components["catalog"] == 100.0, (
            f"Catalog score {result.components['catalog']} should be 100 (350 products)"
        )

    @pytest.mark.asyncio
    async def test_snapshot_scoring_dead_shop(
        self,
        use_case: ComputeShopScoreUseCase,
        fake_page_repo: FakePageRepository,
        fake_ads_repo: FakeAdsRepository,
    ) -> None:
        """Snapshot test: Inactive/dead shop should score XS tier.

        This test represents a "dead" or abandoned shop with:
        - Minimal advertising (0-1 ads)
        - Not confirmed as Shopify
        - No premium currency signals
        - No active ads
        - Poor creative quality (no text, no CTA)
        - Very small or no product catalog

        Expected behavior:
        - Global score: <= 20
        - Tier: XS

        If this test fails, review the scoring formula changes to ensure
        low-quality/inactive shops are still properly identified.
        """
        # Setup: Dead/abandoned store with minimal signals
        page = Page(
            id="snapshot-dead-page",
            url=Url("https://dead-abandoned-store.com"),
            domain="dead-abandoned-store.com",
            is_shopify=False,  # Not Shopify
            currency=None,  # No currency info
            product_count=ProductCount(0),  # No products
            active_ads_count=0,  # No active ads
            total_ads_count=1,  # Only 1 historical ad
        )
        await fake_page_repo.save(page)

        # Single poor-quality ad with no content
        dead_ad = Ad(
            id="dead-ad-0",
            page_id="snapshot-dead-page",
            meta_page_id="meta-dead",
            meta_ad_id="meta-dead-ad-0",
            title=None,  # No title
            body=None,  # No body
            cta_type=None,  # No CTA
            status=AdStatus.INACTIVE,
            platforms=[AdPlatform.FACEBOOK],  # Single platform
            countries=[Country("US")],  # Single country
        )
        await fake_ads_repo.save_many([dead_ad])

        # Execute
        result = await use_case.execute("snapshot-dead-page")

        # Snapshot assertions
        assert result.global_score <= 20, (
            f"SNAPSHOT FAILURE: Dead shop score {result.global_score} "
            f"exceeds expected maximum of 20. "
            f"Components: {result.components}"
        )
        assert result.tier == "XS", (
            f"SNAPSHOT FAILURE: Dead shop tier '{result.tier}' "
            f"should be 'XS' (score={result.global_score})"
        )

        # Component sanity checks (non-strict, for diagnostics)
        # Note: Even 1 ad gives some score (~12), so we use 15 as threshold
        assert result.components["ads_activity"] < 15.0, (
            f"Ads activity {result.components['ads_activity']} too high for dead shop"
        )
        assert result.components["shopify"] <= 30.0, (
            f"Shopify score {result.components['shopify']} too high (not Shopify, no ads)"
        )
        assert result.components["creative_quality"] == 0.0, (
            f"Creative quality {result.components['creative_quality']} should be 0 (no content)"
        )
        assert result.components["catalog"] == 0.0, (
            f"Catalog score {result.components['catalog']} should be 0 (no products)"
        )

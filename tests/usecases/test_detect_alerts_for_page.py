"""Unit tests for DetectAlertsForPageUseCase.

Tests the alert detection logic for score changes, tier changes, and ads boosts.
"""

import pytest

from src.app.core.domain.entities.alert import (
    ALERT_TYPE_NEW_ADS_BOOST,
    ALERT_TYPE_SCORE_JUMP,
    ALERT_TYPE_SCORE_DROP,
    ALERT_TYPE_TIER_UP,
    ALERT_TYPE_TIER_DOWN,
)
from src.app.core.usecases.detect_alerts_for_page import (
    DetectAlertsForPageUseCase,
    DetectAlertsInput,
    SCORE_CHANGE_THRESHOLD,
    ADS_BOOST_RATIO_THRESHOLD,
)
from tests.conftest import FakeLoggingPort, FakeAlertRepository


class TestDetectAlertsForPageUseCase:
    """Tests for DetectAlertsForPageUseCase."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_no_alerts_when_no_historical_data(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should return no alerts when there's no historical data."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=75.0,
            new_tier="L",
            new_ads_count=10,
            old_score=None,  # No historical data
            old_tier=None,
            old_ads_count=None,
        )

        result = await use_case.execute(input_data)

        assert result == []
        assert len(fake_alert_repo.alerts) == 0

    @pytest.mark.asyncio
    async def test_no_alerts_when_no_significant_change(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should return no alerts when changes are below thresholds."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=75.0,
            new_tier="L",
            new_ads_count=12,
            old_score=72.0,  # Only +3 points (below 10)
            old_tier="L",  # Same tier
            old_ads_count=10,  # Only +20% (below 100%)
        )

        result = await use_case.execute(input_data)

        assert result == []
        assert len(fake_alert_repo.alerts) == 0


class TestScoreJumpDetection:
    """Tests for SCORE_JUMP alert detection."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_score_jump_at_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create SCORE_JUMP alert when score increases by exactly threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=60.0,
            new_tier="M",
            new_ads_count=10,
            old_score=50.0,  # +10 points (exactly threshold)
            old_tier="M",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        assert len(result) == 1
        assert result[0].type == ALERT_TYPE_SCORE_JUMP
        assert result[0].page_id == "page-123"
        assert result[0].old_score == 50.0
        assert result[0].new_score == 60.0
        assert "jumped" in result[0].message.lower()

    @pytest.mark.asyncio
    async def test_score_jump_above_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create SCORE_JUMP alert when score increases above threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=80.0,
            new_tier="XL",
            new_ads_count=10,
            old_score=55.0,  # +25 points
            old_tier="M",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        # Should have both SCORE_JUMP and TIER_UP
        score_jumps = [a for a in result if a.type == ALERT_TYPE_SCORE_JUMP]
        assert len(score_jumps) == 1
        assert score_jumps[0].old_score == 55.0
        assert score_jumps[0].new_score == 80.0

    @pytest.mark.asyncio
    async def test_no_score_jump_below_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
    ) -> None:
        """Should not create SCORE_JUMP alert when increase is below threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=59.0,
            new_tier="M",
            new_ads_count=10,
            old_score=50.0,  # +9 points (below 10)
            old_tier="M",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        score_jumps = [a for a in result if a.type == ALERT_TYPE_SCORE_JUMP]
        assert len(score_jumps) == 0


class TestScoreDropDetection:
    """Tests for SCORE_DROP alert detection."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_score_drop_at_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create SCORE_DROP alert when score decreases by exactly threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=50.0,
            new_tier="M",
            new_ads_count=10,
            old_score=60.0,  # -10 points (exactly threshold)
            old_tier="M",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        assert len(result) == 1
        assert result[0].type == ALERT_TYPE_SCORE_DROP
        assert result[0].page_id == "page-123"
        assert result[0].old_score == 60.0
        assert result[0].new_score == 50.0
        assert "dropped" in result[0].message.lower()

    @pytest.mark.asyncio
    async def test_score_drop_above_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create SCORE_DROP alert when score decreases above threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=40.0,
            new_tier="S",
            new_ads_count=10,
            old_score=70.0,  # -30 points
            old_tier="L",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        # Should have both SCORE_DROP and TIER_DOWN
        score_drops = [a for a in result if a.type == ALERT_TYPE_SCORE_DROP]
        assert len(score_drops) == 1
        assert score_drops[0].old_score == 70.0
        assert score_drops[0].new_score == 40.0

    @pytest.mark.asyncio
    async def test_no_score_drop_below_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
    ) -> None:
        """Should not create SCORE_DROP alert when decrease is below threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=51.0,
            new_tier="M",
            new_ads_count=10,
            old_score=60.0,  # -9 points (below 10)
            old_tier="M",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        score_drops = [a for a in result if a.type == ALERT_TYPE_SCORE_DROP]
        assert len(score_drops) == 0


class TestTierUpDetection:
    """Tests for TIER_UP alert detection."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_tier_up_single_level(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create TIER_UP alert when tier improves by one level."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=75.0,
            new_tier="L",
            new_ads_count=10,
            old_score=65.0,  # Small change
            old_tier="M",  # M -> L is tier up
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        tier_ups = [a for a in result if a.type == ALERT_TYPE_TIER_UP]
        assert len(tier_ups) == 1
        assert tier_ups[0].old_tier == "M"
        assert tier_ups[0].new_tier == "L"
        assert "upgraded" in tier_ups[0].message.lower()

    @pytest.mark.asyncio
    async def test_tier_up_multiple_levels(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create TIER_UP alert when tier improves by multiple levels."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=92.0,
            new_tier="XXL",
            new_ads_count=10,
            old_score=45.0,
            old_tier="S",  # S -> XXL is major tier up
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        tier_ups = [a for a in result if a.type == ALERT_TYPE_TIER_UP]
        assert len(tier_ups) == 1
        assert tier_ups[0].old_tier == "S"
        assert tier_ups[0].new_tier == "XXL"

    @pytest.mark.asyncio
    async def test_no_tier_up_same_tier(
        self,
        use_case: DetectAlertsForPageUseCase,
    ) -> None:
        """Should not create TIER_UP alert when tier stays the same."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=72.0,
            new_tier="L",
            new_ads_count=10,
            old_score=70.0,
            old_tier="L",  # Same tier
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        tier_ups = [a for a in result if a.type == ALERT_TYPE_TIER_UP]
        assert len(tier_ups) == 0

    @pytest.mark.asyncio
    async def test_tier_up_case_insensitive(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should handle tier comparison case-insensitively."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=75.0,
            new_tier="l",  # lowercase
            new_ads_count=10,
            old_score=65.0,
            old_tier="m",  # lowercase
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        tier_ups = [a for a in result if a.type == ALERT_TYPE_TIER_UP]
        assert len(tier_ups) == 1


class TestTierDownDetection:
    """Tests for TIER_DOWN alert detection."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_tier_down_single_level(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create TIER_DOWN alert when tier degrades by one level."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=65.0,
            new_tier="M",
            new_ads_count=10,
            old_score=75.0,
            old_tier="L",  # L -> M is tier down
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        tier_downs = [a for a in result if a.type == ALERT_TYPE_TIER_DOWN]
        assert len(tier_downs) == 1
        assert tier_downs[0].old_tier == "L"
        assert tier_downs[0].new_tier == "M"
        assert "downgraded" in tier_downs[0].message.lower()

    @pytest.mark.asyncio
    async def test_tier_down_multiple_levels(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create TIER_DOWN alert when tier degrades by multiple levels."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=25.0,
            new_tier="XS",
            new_ads_count=10,
            old_score=85.0,
            old_tier="XL",  # XL -> XS is major tier down
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        tier_downs = [a for a in result if a.type == ALERT_TYPE_TIER_DOWN]
        assert len(tier_downs) == 1
        assert tier_downs[0].old_tier == "XL"
        assert tier_downs[0].new_tier == "XS"


class TestAdsBoostDetection:
    """Tests for NEW_ADS_BOOST alert detection."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_ads_boost_at_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create NEW_ADS_BOOST alert when ads count exactly doubles."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=70.0,
            new_tier="L",
            new_ads_count=20,  # 100% increase (doubled)
            old_score=70.0,
            old_tier="L",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        ads_boosts = [a for a in result if a.type == ALERT_TYPE_NEW_ADS_BOOST]
        assert len(ads_boosts) == 1
        assert ads_boosts[0].page_id == "page-123"
        assert "increased" in ads_boosts[0].message.lower()

    @pytest.mark.asyncio
    async def test_ads_boost_above_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should create NEW_ADS_BOOST alert when ads count more than doubles."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=70.0,
            new_tier="L",
            new_ads_count=30,  # 200% increase (tripled)
            old_score=70.0,
            old_tier="L",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        ads_boosts = [a for a in result if a.type == ALERT_TYPE_NEW_ADS_BOOST]
        assert len(ads_boosts) == 1

    @pytest.mark.asyncio
    async def test_no_ads_boost_below_threshold(
        self,
        use_case: DetectAlertsForPageUseCase,
    ) -> None:
        """Should not create NEW_ADS_BOOST alert when increase is below threshold."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=70.0,
            new_tier="L",
            new_ads_count=15,  # 50% increase (below 100%)
            old_score=70.0,
            old_tier="L",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        ads_boosts = [a for a in result if a.type == ALERT_TYPE_NEW_ADS_BOOST]
        assert len(ads_boosts) == 0

    @pytest.mark.asyncio
    async def test_no_ads_boost_when_count_decreases(
        self,
        use_case: DetectAlertsForPageUseCase,
    ) -> None:
        """Should not create NEW_ADS_BOOST alert when ads count decreases."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=70.0,
            new_tier="L",
            new_ads_count=5,  # Decreased
            old_score=70.0,
            old_tier="L",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        ads_boosts = [a for a in result if a.type == ALERT_TYPE_NEW_ADS_BOOST]
        assert len(ads_boosts) == 0

    @pytest.mark.asyncio
    async def test_no_ads_boost_without_historical_count(
        self,
        use_case: DetectAlertsForPageUseCase,
    ) -> None:
        """Should not create NEW_ADS_BOOST alert when no historical count."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=70.0,
            new_tier="L",
            new_ads_count=100,
            old_score=70.0,
            old_tier="L",
            old_ads_count=None,  # No historical data
        )

        result = await use_case.execute(input_data)

        ads_boosts = [a for a in result if a.type == ALERT_TYPE_NEW_ADS_BOOST]
        assert len(ads_boosts) == 0

    @pytest.mark.asyncio
    async def test_ads_boost_from_zero_count(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should handle ads boost from zero (avoids division by zero)."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=70.0,
            new_tier="L",
            new_ads_count=5,  # From 0 to 5
            old_score=70.0,
            old_tier="L",
            old_ads_count=0,  # Was zero
        )

        result = await use_case.execute(input_data)

        # Should detect as boost (5/1 = 500% increase >= 100%)
        ads_boosts = [a for a in result if a.type == ALERT_TYPE_NEW_ADS_BOOST]
        assert len(ads_boosts) == 1


class TestMultipleAlertsDetection:
    """Tests for detecting multiple alerts simultaneously."""

    @pytest.fixture
    def use_case(
        self,
        fake_alert_repo: FakeAlertRepository,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case instance with fake dependencies."""
        return DetectAlertsForPageUseCase(
            alert_repository=fake_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_score_jump_and_tier_up_together(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should detect both SCORE_JUMP and TIER_UP when both conditions met."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=85.0,
            new_tier="XL",
            new_ads_count=10,
            old_score=60.0,  # +25 points (>= 10)
            old_tier="M",  # M -> XL
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        types = {a.type for a in result}
        assert ALERT_TYPE_SCORE_JUMP in types
        assert ALERT_TYPE_TIER_UP in types
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_score_drop_and_tier_down_together(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should detect both SCORE_DROP and TIER_DOWN when both conditions met."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=45.0,
            new_tier="S",
            new_ads_count=10,
            old_score=75.0,  # -30 points (>= 10)
            old_tier="L",  # L -> S
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        types = {a.type for a in result}
        assert ALERT_TYPE_SCORE_DROP in types
        assert ALERT_TYPE_TIER_DOWN in types
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_all_alerts_together(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should detect multiple alert types simultaneously."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=85.0,
            new_tier="XL",
            new_ads_count=25,  # 150% increase
            old_score=60.0,  # +25 points
            old_tier="M",  # M -> XL
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        types = {a.type for a in result}
        assert ALERT_TYPE_SCORE_JUMP in types
        assert ALERT_TYPE_TIER_UP in types
        assert ALERT_TYPE_NEW_ADS_BOOST in types
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_alerts_are_persisted(
        self,
        use_case: DetectAlertsForPageUseCase,
        fake_alert_repo: FakeAlertRepository,
    ) -> None:
        """Should persist all detected alerts to the repository."""
        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=85.0,
            new_tier="XL",
            new_ads_count=10,
            old_score=60.0,
            old_tier="M",
            old_ads_count=10,
        )

        result = await use_case.execute(input_data)

        assert len(fake_alert_repo.alerts) == len(result)
        assert len(fake_alert_repo.alerts) == 2  # SCORE_JUMP and TIER_UP


class TestAlertPersistenceFailure:
    """Tests for handling alert persistence failures."""

    @pytest.fixture
    def failing_alert_repo(self) -> FakeAlertRepository:
        """Create a failing alert repository."""
        class FailingAlertRepository(FakeAlertRepository):
            def __init__(self) -> None:
                super().__init__()
                self.fail_on_save = False

            async def save(self, alert):
                if self.fail_on_save:
                    raise Exception("Database error")
                return await super().save(alert)

        return FailingAlertRepository()

    @pytest.fixture
    def use_case_with_failing_repo(
        self,
        failing_alert_repo,
        fake_logger: FakeLoggingPort,
    ) -> DetectAlertsForPageUseCase:
        """Create use case with failing repository."""
        return DetectAlertsForPageUseCase(
            alert_repository=failing_alert_repo,
            logger=fake_logger,
        )

    @pytest.mark.asyncio
    async def test_continues_on_save_failure(
        self,
        use_case_with_failing_repo: DetectAlertsForPageUseCase,
        failing_alert_repo,
        fake_logger: FakeLoggingPort,
    ) -> None:
        """Should continue processing other alerts when one save fails."""
        failing_alert_repo.fail_on_save = True

        input_data = DetectAlertsInput(
            page_id="page-123",
            new_score=85.0,
            new_tier="XL",
            new_ads_count=10,
            old_score=60.0,
            old_tier="M",
            old_ads_count=10,
        )

        # Should not raise exception
        result = await use_case_with_failing_repo.execute(input_data)

        # Result should be empty since saves failed
        assert len(result) == 0

        # Error should be logged
        error_logs = [l for l in fake_logger.logs if l["level"] == "error"]
        assert len(error_logs) > 0

"""Detect Alerts For Page Use Case.

Detects significant changes during shop rescoring and creates alerts.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from ..domain.entities.alert import (
    Alert,
    ALERT_TYPE_NEW_ADS_BOOST,
    ALERT_TYPE_SCORE_JUMP,
    ALERT_TYPE_SCORE_DROP,
    ALERT_TYPE_TIER_UP,
    ALERT_TYPE_TIER_DOWN,
)
from ..domain.config import SCORE_CHANGE_THRESHOLD, ADS_BOOST_RATIO_THRESHOLD
from ..domain.tiering import TIERS_ORDERED
from ..ports import AlertRepository, LoggingPort


@dataclass
class DetectAlertsInput:
    """Input data for alert detection.

    Attributes:
        page_id: The page identifier.
        new_score: The new calculated score.
        new_tier: The new tier based on new_score.
        new_ads_count: Current active ads count.
        old_score: Previous score (None if first scoring).
        old_tier: Previous tier (None if first scoring).
        old_ads_count: Previous ads count (None if first scoring).
    """

    page_id: str
    new_score: float
    new_tier: str
    new_ads_count: int
    old_score: Optional[float] = None
    old_tier: Optional[str] = None
    old_ads_count: Optional[int] = None


class DetectAlertsForPageUseCase:
    """Use case for detecting alerts during shop rescoring.

    Compares old and new scoring data to detect significant changes
    and creates alerts for:
    - NEW_ADS_BOOST: Ads count increased by >= 100%
    - SCORE_JUMP: Score increased by >= 10 points
    - SCORE_DROP: Score decreased by >= 10 points
    - TIER_UP: Tier improved (e.g., M -> L)
    - TIER_DOWN: Tier degraded (e.g., L -> M)
    """

    def __init__(
        self,
        alert_repository: AlertRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            alert_repository: Repository for persisting alerts.
            logger: Logging port for structured logging.
        """
        self._alert_repo = alert_repository
        self._logger = logger

    async def execute(self, input_data: DetectAlertsInput) -> list[Alert]:
        """Execute alert detection for a page.

        Compares current state with previous state and creates alerts
        for significant changes.

        Args:
            input_data: The input data containing old and new metrics.

        Returns:
            List of created alerts.
        """
        self._logger.debug(
            "Starting alert detection",
            page_id=input_data.page_id,
            new_score=input_data.new_score,
            new_tier=input_data.new_tier,
            old_score=input_data.old_score,
            old_tier=input_data.old_tier,
        )

        alerts: list[Alert] = []

        # No comparison possible without historical data
        if input_data.old_score is None:
            self._logger.info(
                "No historical data for page, skipping alert detection",
                page_id=input_data.page_id,
            )
            return alerts

        # Check for NEW_ADS_BOOST
        ads_boost_alert = self._check_ads_boost(input_data)
        if ads_boost_alert:
            alerts.append(ads_boost_alert)

        # Check for SCORE_JUMP
        score_jump_alert = self._check_score_jump(input_data)
        if score_jump_alert:
            alerts.append(score_jump_alert)

        # Check for SCORE_DROP
        score_drop_alert = self._check_score_drop(input_data)
        if score_drop_alert:
            alerts.append(score_drop_alert)

        # Check for TIER_UP
        tier_up_alert = self._check_tier_up(input_data)
        if tier_up_alert:
            alerts.append(tier_up_alert)

        # Check for TIER_DOWN
        tier_down_alert = self._check_tier_down(input_data)
        if tier_down_alert:
            alerts.append(tier_down_alert)

        # Persist all alerts
        saved_alerts = []
        for alert in alerts:
            try:
                saved = await self._alert_repo.save(alert)
                saved_alerts.append(saved)
                self._logger.info(
                    "Alert created",
                    alert_id=saved.id,
                    alert_type=saved.type,
                    page_id=saved.page_id,
                    severity=saved.severity,
                )
            except Exception as exc:
                self._logger.error(
                    "Failed to save alert",
                    alert_type=alert.type,
                    page_id=alert.page_id,
                    error=str(exc),
                )
                # Continue with other alerts even if one fails

        self._logger.info(
            "Alert detection completed",
            page_id=input_data.page_id,
            alerts_created=len(saved_alerts),
        )

        return saved_alerts

    def _check_ads_boost(self, input_data: DetectAlertsInput) -> Optional[Alert]:
        """Check for NEW_ADS_BOOST condition.

        Triggers if ads count increased by >= 100% (doubled or more).

        Args:
            input_data: The input data.

        Returns:
            Alert if condition met, None otherwise.
        """
        if input_data.old_ads_count is None:
            return None

        old_count = max(input_data.old_ads_count, 1)  # Avoid division by zero
        new_count = input_data.new_ads_count

        if new_count <= old_count:
            return None

        increase_ratio = (new_count - old_count) / old_count
        if increase_ratio >= ADS_BOOST_RATIO_THRESHOLD:
            return Alert.new_ads_boost(
                id=str(uuid4()),
                page_id=input_data.page_id,
                old_count=input_data.old_ads_count,
                new_count=new_count,
            )

        return None

    def _check_score_jump(self, input_data: DetectAlertsInput) -> Optional[Alert]:
        """Check for SCORE_JUMP condition.

        Triggers if score increased by >= SCORE_CHANGE_THRESHOLD points.

        Args:
            input_data: The input data.

        Returns:
            Alert if condition met, None otherwise.
        """
        if input_data.old_score is None:
            return None

        score_diff = input_data.new_score - input_data.old_score
        if score_diff >= SCORE_CHANGE_THRESHOLD:
            return Alert.score_jump(
                id=str(uuid4()),
                page_id=input_data.page_id,
                old_score=input_data.old_score,
                new_score=input_data.new_score,
            )

        return None

    def _check_score_drop(self, input_data: DetectAlertsInput) -> Optional[Alert]:
        """Check for SCORE_DROP condition.

        Triggers if score decreased by >= SCORE_CHANGE_THRESHOLD points.

        Args:
            input_data: The input data.

        Returns:
            Alert if condition met, None otherwise.
        """
        if input_data.old_score is None:
            return None

        score_diff = input_data.old_score - input_data.new_score
        if score_diff >= SCORE_CHANGE_THRESHOLD:
            return Alert.score_drop(
                id=str(uuid4()),
                page_id=input_data.page_id,
                old_score=input_data.old_score,
                new_score=input_data.new_score,
            )

        return None

    def _check_tier_up(self, input_data: DetectAlertsInput) -> Optional[Alert]:
        """Check for TIER_UP condition.

        Triggers if tier improved (moved up in TIERS_ORDERED).

        Args:
            input_data: The input data.

        Returns:
            Alert if condition met, None otherwise.
        """
        if input_data.old_tier is None:
            return None

        old_tier = input_data.old_tier.upper()
        new_tier = input_data.new_tier.upper()

        if old_tier == new_tier:
            return None

        try:
            old_index = TIERS_ORDERED.index(old_tier)
            new_index = TIERS_ORDERED.index(new_tier)

            # Lower index = better tier (XXL=0, XS=5)
            if new_index < old_index:
                return Alert.tier_up(
                    id=str(uuid4()),
                    page_id=input_data.page_id,
                    old_tier=old_tier,
                    new_tier=new_tier,
                )
        except ValueError:
            # Invalid tier - skip
            pass

        return None

    def _check_tier_down(self, input_data: DetectAlertsInput) -> Optional[Alert]:
        """Check for TIER_DOWN condition.

        Triggers if tier degraded (moved down in TIERS_ORDERED).

        Args:
            input_data: The input data.

        Returns:
            Alert if condition met, None otherwise.
        """
        if input_data.old_tier is None:
            return None

        old_tier = input_data.old_tier.upper()
        new_tier = input_data.new_tier.upper()

        if old_tier == new_tier:
            return None

        try:
            old_index = TIERS_ORDERED.index(old_tier)
            new_index = TIERS_ORDERED.index(new_tier)

            # Higher index = worse tier (XXL=0, XS=5)
            if new_index > old_index:
                return Alert.tier_down(
                    id=str(uuid4()),
                    page_id=input_data.page_id,
                    old_tier=old_tier,
                    new_tier=new_tier,
                )
        except ValueError:
            # Invalid tier - skip
            pass

        return None

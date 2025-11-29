"""Alert Domain Entities.

Entities for managing alerts - notifications about significant changes
detected during shop rescoring operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# =============================================================================
# Alert Type Constants
# =============================================================================

ALERT_TYPE_NEW_ADS_BOOST = "NEW_ADS_BOOST"
ALERT_TYPE_SCORE_JUMP = "SCORE_JUMP"
ALERT_TYPE_SCORE_DROP = "SCORE_DROP"
ALERT_TYPE_TIER_UP = "TIER_UP"
ALERT_TYPE_TIER_DOWN = "TIER_DOWN"

VALID_ALERT_TYPES = {
    ALERT_TYPE_NEW_ADS_BOOST,
    ALERT_TYPE_SCORE_JUMP,
    ALERT_TYPE_SCORE_DROP,
    ALERT_TYPE_TIER_UP,
    ALERT_TYPE_TIER_DOWN,
}


# =============================================================================
# Alert Severity Constants
# =============================================================================

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"

VALID_SEVERITIES = {
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
}


@dataclass
class Alert:
    """Entity representing an alert for a page.

    An Alert is created when a significant change is detected during
    a rescore operation (e.g., score jump, tier change, ads boost).

    Attributes:
        id: Unique identifier for this alert.
        page_id: The page this alert is associated with.
        type: Type of alert (NEW_ADS_BOOST, SCORE_JUMP, etc.).
        message: Human-readable description of the alert.
        severity: Alert severity level (info, warning, critical).
        old_score: Previous score value (if applicable).
        new_score: New score value (if applicable).
        old_tier: Previous tier (if applicable).
        new_tier: New tier (if applicable).
        created_at: When this alert was created.
    """

    id: str
    page_id: str
    type: str
    message: str
    severity: str = SEVERITY_INFO
    old_score: Optional[float] = None
    new_score: Optional[float] = None
    old_tier: Optional[str] = None
    new_tier: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate alert after initialization."""
        if self.type not in VALID_ALERT_TYPES:
            raise ValueError(
                f"Invalid alert type: {self.type}. "
                f"Must be one of: {VALID_ALERT_TYPES}"
            )
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity: {self.severity}. "
                f"Must be one of: {VALID_SEVERITIES}"
            )
        if not self.message or not self.message.strip():
            raise ValueError("Alert message cannot be empty")

    @classmethod
    def create(
        cls,
        id: str,
        page_id: str,
        alert_type: str,
        message: str,
        severity: str = SEVERITY_INFO,
        old_score: Optional[float] = None,
        new_score: Optional[float] = None,
        old_tier: Optional[str] = None,
        new_tier: Optional[str] = None,
    ) -> "Alert":
        """Factory method to create a new Alert.

        Args:
            id: Unique identifier for the alert.
            page_id: The page this alert is for.
            alert_type: Type of alert.
            message: Human-readable message.
            severity: Alert severity level.
            old_score: Previous score value.
            new_score: New score value.
            old_tier: Previous tier.
            new_tier: New tier.

        Returns:
            A new Alert instance.
        """
        return cls(
            id=id,
            page_id=page_id,
            type=alert_type,
            message=message,
            severity=severity,
            old_score=old_score,
            new_score=new_score,
            old_tier=old_tier,
            new_tier=new_tier,
            created_at=datetime.utcnow(),
        )

    @classmethod
    def new_ads_boost(
        cls,
        id: str,
        page_id: str,
        old_count: int,
        new_count: int,
    ) -> "Alert":
        """Create a NEW_ADS_BOOST alert.

        Args:
            id: Unique identifier for the alert.
            page_id: The page this alert is for.
            old_count: Previous ads count.
            new_count: New ads count.

        Returns:
            A new Alert for ads boost.
        """
        return cls.create(
            id=id,
            page_id=page_id,
            alert_type=ALERT_TYPE_NEW_ADS_BOOST,
            message=f"Ads count increased from {old_count} to {new_count} (+{new_count - old_count})",
            severity=SEVERITY_WARNING,
        )

    @classmethod
    def score_jump(
        cls,
        id: str,
        page_id: str,
        old_score: float,
        new_score: float,
    ) -> "Alert":
        """Create a SCORE_JUMP alert.

        Args:
            id: Unique identifier for the alert.
            page_id: The page this alert is for.
            old_score: Previous score.
            new_score: New score.

        Returns:
            A new Alert for score jump.
        """
        return cls.create(
            id=id,
            page_id=page_id,
            alert_type=ALERT_TYPE_SCORE_JUMP,
            message=f"Score jumped from {old_score:.1f} to {new_score:.1f} (+{new_score - old_score:.1f})",
            severity=SEVERITY_WARNING,
            old_score=old_score,
            new_score=new_score,
        )

    @classmethod
    def score_drop(
        cls,
        id: str,
        page_id: str,
        old_score: float,
        new_score: float,
    ) -> "Alert":
        """Create a SCORE_DROP alert.

        Args:
            id: Unique identifier for the alert.
            page_id: The page this alert is for.
            old_score: Previous score.
            new_score: New score.

        Returns:
            A new Alert for score drop.
        """
        return cls.create(
            id=id,
            page_id=page_id,
            alert_type=ALERT_TYPE_SCORE_DROP,
            message=f"Score dropped from {old_score:.1f} to {new_score:.1f} ({new_score - old_score:.1f})",
            severity=SEVERITY_WARNING,
            old_score=old_score,
            new_score=new_score,
        )

    @classmethod
    def tier_up(
        cls,
        id: str,
        page_id: str,
        old_tier: str,
        new_tier: str,
    ) -> "Alert":
        """Create a TIER_UP alert.

        Args:
            id: Unique identifier for the alert.
            page_id: The page this alert is for.
            old_tier: Previous tier.
            new_tier: New tier.

        Returns:
            A new Alert for tier upgrade.
        """
        return cls.create(
            id=id,
            page_id=page_id,
            alert_type=ALERT_TYPE_TIER_UP,
            message=f"Tier upgraded from {old_tier} to {new_tier}",
            severity=SEVERITY_INFO,
            old_tier=old_tier,
            new_tier=new_tier,
        )

    @classmethod
    def tier_down(
        cls,
        id: str,
        page_id: str,
        old_tier: str,
        new_tier: str,
    ) -> "Alert":
        """Create a TIER_DOWN alert.

        Args:
            id: Unique identifier for the alert.
            page_id: The page this alert is for.
            old_tier: Previous tier.
            new_tier: New tier.

        Returns:
            A new Alert for tier downgrade.
        """
        return cls.create(
            id=id,
            page_id=page_id,
            alert_type=ALERT_TYPE_TIER_DOWN,
            message=f"Tier downgraded from {old_tier} to {new_tier}",
            severity=SEVERITY_WARNING,
            old_tier=old_tier,
            new_tier=new_tier,
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on identity (id)."""
        if isinstance(other, Alert):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        """Hash based on identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Alert(id={self.id}, page_id={self.page_id}, "
            f"type={self.type}, severity={self.severity})>"
        )

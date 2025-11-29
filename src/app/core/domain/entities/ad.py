"""Ad Entity.

Represents an advertisement detected from Meta Ads Library.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from ..value_objects import Url, Country


class AdStatus(Enum):
    """Enumeration of ad statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class AdPlatform(Enum):
    """Enumeration of ad platforms."""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    MESSENGER = "messenger"
    AUDIENCE_NETWORK = "audience_network"
    UNKNOWN = "unknown"


@dataclass
class Ad:
    """Entity representing a Meta advertisement.

    An Ad represents a single advertisement found in the Meta Ads Library,
    associated with a specific page/advertiser.

    Attributes:
        id: Unique identifier for the ad (from Meta).
        page_id: Reference to the associated Page entity.
        meta_page_id: The Meta/Facebook page ID.
        meta_ad_id: The original Meta ad library ID.
        title: Ad title/headline.
        body: Ad body text/description.
        link_url: Destination URL of the ad.
        image_url: URL to the ad creative image.
        video_url: URL to the ad video (if applicable).
        cta_type: Call-to-action type (e.g., "Shop Now").
        status: Current status of the ad.
        platforms: Platforms where the ad is shown.
        countries: Countries where the ad is targeted.
        started_at: When the ad started running.
        ended_at: When the ad stopped running (if applicable).
        impressions_lower: Lower bound of impression estimate.
        impressions_upper: Upper bound of impression estimate.
        spend_lower: Lower bound of spend estimate.
        spend_upper: Upper bound of spend estimate.
        currency: Currency for spend estimates.
        first_seen_at: When we first detected this ad.
        last_seen_at: When we last saw this ad active.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    id: str
    page_id: str
    meta_page_id: str
    meta_ad_id: str
    title: Optional[str] = None
    body: Optional[str] = None
    link_url: Optional[Url] = None
    image_url: Optional[Url] = None
    video_url: Optional[Url] = None
    cta_type: Optional[str] = None
    status: AdStatus = AdStatus.UNKNOWN
    platforms: list[AdPlatform] = field(default_factory=list)
    countries: list[Country] = field(default_factory=list)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    impressions_lower: Optional[int] = None
    impressions_upper: Optional[int] = None
    spend_lower: Optional[float] = None
    spend_upper: Optional[float] = None
    currency: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Initialize derived fields after creation."""
        if self.first_seen_at is None:
            object.__setattr__(self, "first_seen_at", self.created_at)
        if self.last_seen_at is None:
            object.__setattr__(self, "last_seen_at", self.created_at)

    @classmethod
    def create(
        cls,
        id: str,
        page_id: str,
        meta_page_id: str,
        meta_ad_id: str,
        status: AdStatus = AdStatus.ACTIVE,
    ) -> "Ad":
        """Factory method to create a new Ad.

        Args:
            id: Unique identifier.
            page_id: Associated Page ID.
            meta_page_id: Meta/Facebook page ID.
            meta_ad_id: Meta ad library ID.
            status: Initial ad status.

        Returns:
            A new Ad instance.
        """
        now = datetime.utcnow()
        return cls(
            id=id,
            page_id=page_id,
            meta_page_id=meta_page_id,
            meta_ad_id=meta_ad_id,
            status=status,
            first_seen_at=now,
            last_seen_at=now,
            created_at=now,
            updated_at=now,
        )

    def mark_as_active(self) -> "Ad":
        """Mark the ad as active.

        Returns:
            Updated Ad instance.
        """
        return Ad(
            id=self.id,
            page_id=self.page_id,
            meta_page_id=self.meta_page_id,
            meta_ad_id=self.meta_ad_id,
            title=self.title,
            body=self.body,
            link_url=self.link_url,
            image_url=self.image_url,
            video_url=self.video_url,
            cta_type=self.cta_type,
            status=AdStatus.ACTIVE,
            platforms=self.platforms,
            countries=self.countries,
            started_at=self.started_at,
            ended_at=None,
            impressions_lower=self.impressions_lower,
            impressions_upper=self.impressions_upper,
            spend_lower=self.spend_lower,
            spend_upper=self.spend_upper,
            currency=self.currency,
            first_seen_at=self.first_seen_at,
            last_seen_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def mark_as_inactive(self) -> "Ad":
        """Mark the ad as inactive.

        Returns:
            Updated Ad instance.
        """
        now = datetime.utcnow()
        return Ad(
            id=self.id,
            page_id=self.page_id,
            meta_page_id=self.meta_page_id,
            meta_ad_id=self.meta_ad_id,
            title=self.title,
            body=self.body,
            link_url=self.link_url,
            image_url=self.image_url,
            video_url=self.video_url,
            cta_type=self.cta_type,
            status=AdStatus.INACTIVE,
            platforms=self.platforms,
            countries=self.countries,
            started_at=self.started_at,
            ended_at=now,
            impressions_lower=self.impressions_lower,
            impressions_upper=self.impressions_upper,
            spend_lower=self.spend_lower,
            spend_upper=self.spend_upper,
            currency=self.currency,
            first_seen_at=self.first_seen_at,
            last_seen_at=self.last_seen_at,
            created_at=self.created_at,
            updated_at=now,
        )

    def update_metrics(
        self,
        impressions_lower: Optional[int] = None,
        impressions_upper: Optional[int] = None,
        spend_lower: Optional[float] = None,
        spend_upper: Optional[float] = None,
    ) -> "Ad":
        """Update ad metrics.

        Args:
            impressions_lower: Lower bound of impressions.
            impressions_upper: Upper bound of impressions.
            spend_lower: Lower bound of spend.
            spend_upper: Upper bound of spend.

        Returns:
            Updated Ad instance.
        """
        return Ad(
            id=self.id,
            page_id=self.page_id,
            meta_page_id=self.meta_page_id,
            meta_ad_id=self.meta_ad_id,
            title=self.title,
            body=self.body,
            link_url=self.link_url,
            image_url=self.image_url,
            video_url=self.video_url,
            cta_type=self.cta_type,
            status=self.status,
            platforms=self.platforms,
            countries=self.countries,
            started_at=self.started_at,
            ended_at=self.ended_at,
            impressions_lower=impressions_lower or self.impressions_lower,
            impressions_upper=impressions_upper or self.impressions_upper,
            spend_lower=spend_lower or self.spend_lower,
            spend_upper=spend_upper or self.spend_upper,
            currency=self.currency,
            first_seen_at=self.first_seen_at,
            last_seen_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def is_active(self) -> bool:
        """Check if the ad is currently active."""
        return self.status == AdStatus.ACTIVE

    def is_video_ad(self) -> bool:
        """Check if this is a video ad."""
        return self.video_url is not None

    def has_link(self) -> bool:
        """Check if the ad has a destination link."""
        return self.link_url is not None

    def get_running_days(self) -> Optional[int]:
        """Calculate how many days the ad has been running.

        Returns:
            Number of days, or None if start date unknown.
        """
        if self.started_at is None:
            return None
        end = self.ended_at or datetime.utcnow()
        return (end - self.started_at).days

    def get_estimated_impressions_avg(self) -> Optional[float]:
        """Get average of impression estimates.

        Returns:
            Average impressions, or None if not available.
        """
        if self.impressions_lower is None or self.impressions_upper is None:
            return None
        return (self.impressions_lower + self.impressions_upper) / 2

    def get_estimated_spend_avg(self) -> Optional[float]:
        """Get average of spend estimates.

        Returns:
            Average spend, or None if not available.
        """
        if self.spend_lower is None or self.spend_upper is None:
            return None
        return (self.spend_lower + self.spend_upper) / 2

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ad):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

"""Page Entity.

Represents a tracked page (typically a Shopify store) in the system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..value_objects import (
    Url,
    Country,
    Language,
    Currency,
    Category,
    PageState,
    PageStatus,
    ProductCount,
)


@dataclass
class Page:
    """Entity representing a tracked page/store.

    A Page represents a website (typically a Shopify store) that is being
    tracked for advertising activity and competitive intelligence.

    Attributes:
        id: Unique identifier for the page.
        url: The page's URL.
        domain: The domain extracted from the URL.
        state: Current state of the page in the tracking pipeline.
        country: Target country of the store.
        language: Primary language of the store.
        currency: Primary currency used.
        category: Product category of the store.
        product_count: Number of products in the store.
        is_shopify: Whether the store is confirmed as Shopify.
        shopify_profile_id: Reference to associated ShopifyProfile.
        active_ads_count: Number of currently active ads.
        total_ads_count: Total ads ever detected.
        score: Computed relevance/quality score.
        first_seen_at: When the page was first discovered.
        last_scanned_at: When the page was last analyzed.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    id: str
    url: Url
    domain: str
    state: PageState = field(default_factory=PageState.initial)
    country: Optional[Country] = None
    language: Optional[Language] = None
    currency: Optional[Currency] = None
    category: Optional[Category] = None
    product_count: ProductCount = field(default_factory=ProductCount.zero)
    is_shopify: bool = False
    shopify_profile_id: Optional[str] = None
    active_ads_count: int = 0
    total_ads_count: int = 0
    score: float = 0.0
    first_seen_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Initialize derived fields after creation."""
        if not self.domain and self.url:
            object.__setattr__(self, "domain", self.url.domain)
        if self.first_seen_at is None:
            object.__setattr__(self, "first_seen_at", self.created_at)

    @classmethod
    def create(
        cls,
        id: str,
        url: Url,
        country: Optional[Country] = None,
        category: Optional[Category] = None,
    ) -> "Page":
        """Factory method to create a new Page.

        Args:
            id: Unique identifier.
            url: The page URL.
            country: Target country (optional).
            category: Product category (optional).

        Returns:
            A new Page instance in DISCOVERED state.
        """
        now = datetime.utcnow()
        return cls(
            id=id,
            url=url,
            domain=url.domain,
            state=PageState.initial(),
            country=country,
            category=category,
            first_seen_at=now,
            created_at=now,
            updated_at=now,
        )

    def mark_as_shopify(self, profile_id: str) -> "Page":
        """Mark the page as a confirmed Shopify store.

        Args:
            profile_id: The associated ShopifyProfile ID.

        Returns:
            Updated Page instance.
        """
        return Page(
            id=self.id,
            url=self.url,
            domain=self.domain,
            state=self.state.transition_to(PageStatus.VERIFIED_SHOPIFY),
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            is_shopify=True,
            shopify_profile_id=profile_id,
            active_ads_count=self.active_ads_count,
            total_ads_count=self.total_ads_count,
            score=self.score,
            first_seen_at=self.first_seen_at,
            last_scanned_at=self.last_scanned_at,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def mark_as_not_shopify(self) -> "Page":
        """Mark the page as not a Shopify store.

        Returns:
            Updated Page instance.
        """
        return Page(
            id=self.id,
            url=self.url,
            domain=self.domain,
            state=self.state.transition_to(PageStatus.NOT_SHOPIFY),
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            is_shopify=False,
            shopify_profile_id=None,
            active_ads_count=self.active_ads_count,
            total_ads_count=self.total_ads_count,
            score=self.score,
            first_seen_at=self.first_seen_at,
            last_scanned_at=self.last_scanned_at,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def update_ads_count(self, active: int, total: int) -> "Page":
        """Update the ads count for this page.

        Args:
            active: Number of currently active ads.
            total: Total number of ads detected.

        Returns:
            Updated Page instance.
        """
        return Page(
            id=self.id,
            url=self.url,
            domain=self.domain,
            state=self.state,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            is_shopify=self.is_shopify,
            shopify_profile_id=self.shopify_profile_id,
            active_ads_count=active,
            total_ads_count=total,
            score=self.score,
            first_seen_at=self.first_seen_at,
            last_scanned_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def update_score(self, score: float) -> "Page":
        """Update the page score.

        Args:
            score: The new score value.

        Returns:
            Updated Page instance.
        """
        return Page(
            id=self.id,
            url=self.url,
            domain=self.domain,
            state=self.state,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            is_shopify=self.is_shopify,
            shopify_profile_id=self.shopify_profile_id,
            active_ads_count=self.active_ads_count,
            total_ads_count=self.total_ads_count,
            score=score,
            first_seen_at=self.first_seen_at,
            last_scanned_at=self.last_scanned_at,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def transition_state(self, new_status: PageStatus) -> "Page":
        """Transition the page to a new state.

        Args:
            new_status: The target state.

        Returns:
            Updated Page instance with new state.
        """
        return Page(
            id=self.id,
            url=self.url,
            domain=self.domain,
            state=self.state.transition_to(new_status),
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            is_shopify=self.is_shopify,
            shopify_profile_id=self.shopify_profile_id,
            active_ads_count=self.active_ads_count,
            total_ads_count=self.total_ads_count,
            score=self.score,
            first_seen_at=self.first_seen_at,
            last_scanned_at=self.last_scanned_at,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def is_active(self) -> bool:
        """Check if the page is actively monitored."""
        return self.state.is_active()

    def needs_analysis(self) -> bool:
        """Check if the page requires analysis."""
        return self.state.requires_analysis()

    def has_active_ads(self) -> bool:
        """Check if the page has active ads."""
        return self.active_ads_count > 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Page):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

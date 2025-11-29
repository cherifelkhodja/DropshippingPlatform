"""Compute Page Active Ads Count Use Case.

Counts active ads for a page and updates its state.
"""

from dataclasses import dataclass
from enum import Enum

from ..domain import (
    Country,
    PageStatus,
    EntityNotFoundError,
)
from ..ports import (
    MetaAdsPort,
    PageRepository,
    LoggingPort,
)


class PageAdsTier(Enum):
    """Classification of pages by active ads count."""

    XS = "xs"  # 0 ads
    S = "s"  # 1-5 ads
    M = "m"  # 6-20 ads
    L = "l"  # 21-50 ads
    XL = "xl"  # 51-100 ads
    XXL = "xxl"  # 100+ ads

    @classmethod
    def from_count(cls, count: int) -> "PageAdsTier":
        """Determine tier from ads count."""
        if count == 0:
            return cls.XS
        elif count <= 5:
            return cls.S
        elif count <= 20:
            return cls.M
        elif count <= 50:
            return cls.L
        elif count <= 100:
            return cls.XL
        else:
            return cls.XXL


@dataclass(frozen=True)
class PageAdsCountResult:
    """Result of the compute page active ads count use case.

    Attributes:
        page_id: The page identifier.
        active_ads_count: Number of active ads.
        tier: Classification tier (XS to XXL).
        previous_count: Previous ads count (for comparison).
    """

    page_id: str
    active_ads_count: int
    tier: PageAdsTier
    previous_count: int = 0


class ComputePageActiveAdsCountUseCase:
    """Use case for counting active ads for a page.

    This use case:
    1. Fetches ads for the page via MetaAdsPort
    2. Counts active ads
    3. Classifies page into tier (XS, S, M, L, XL, XXL)
    4. Updates page state
    5. Saves via PageRepository
    """

    def __init__(
        self,
        meta_ads_port: MetaAdsPort,
        page_repository: PageRepository,
        logger: LoggingPort,
    ) -> None:
        self._meta_ads = meta_ads_port
        self._page_repo = page_repository
        self._logger = logger

    async def execute(
        self,
        page_id: str,
        country: Country,
    ) -> PageAdsCountResult:
        """Execute the compute page active ads count use case.

        Args:
            page_id: The page identifier.
            country: Target country for filtering.

        Returns:
            PageAdsCountResult with count and tier.

        Raises:
            EntityNotFoundError: If page does not exist.
        """
        self._logger.info(
            "Computing active ads count",
            page_id=page_id,
            country=str(country),
        )

        # Get page
        page = await self._page_repo.get(page_id)
        if page is None:
            raise EntityNotFoundError("Page", page_id)

        previous_count = page.active_ads_count

        # Fetch ads for page
        raw_ads = await self._meta_ads.get_ads_by_page(
            page_ids=[page_id],
            country=country,
        )

        # Count active ads
        active_count = 0
        total_count = 0
        for raw_ad in raw_ads:
            total_count += 1
            if raw_ad.get("is_active", True):
                active_count += 1

        # Determine tier
        tier = PageAdsTier.from_count(active_count)

        # Update page
        updated_page = page.update_ads_count(
            active=active_count,
            total=max(total_count, page.total_ads_count),
        )

        # Transition to ACTIVE if has ads and was verified
        if active_count > 0 and page.state.status == PageStatus.VERIFIED_SHOPIFY:
            updated_page = updated_page.transition_state(PageStatus.ACTIVE)

        await self._page_repo.save(updated_page)

        self._logger.info(
            "Active ads count computed",
            page_id=page_id,
            active_count=active_count,
            tier=tier.value,
            previous_count=previous_count,
        )

        return PageAdsCountResult(
            page_id=page_id,
            active_ads_count=active_count,
            tier=tier,
            previous_count=previous_count,
        )

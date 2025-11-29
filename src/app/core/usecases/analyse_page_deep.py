"""Analyse Page Deep Use Case.

Performs deep analysis of a page's ads and triggers website analysis.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
import uuid

from ..domain import (
    Ad,
    AdStatus,
    AdPlatform,
    Country,
    Scan,
    ScanType,
    ScanResult,
    ScanId,
    Url,
    InvalidUrlError,
    EntityNotFoundError,
)
from ..ports import (
    MetaAdsPort,
    AdsRepository,
    ScanRepository,
    PageRepository,
    TaskDispatcherPort,
    LoggingPort,
)


@dataclass(frozen=True)
class AnalysePageDeepResult:
    """Result of the analyse page deep use case.

    Attributes:
        page_id: The page identifier.
        ads_found: Number of ads found.
        ads_saved: Number of ads saved.
        destination_url: Best destination URL found.
        website_analysis_dispatched: Whether website analysis was triggered.
    """

    page_id: str
    ads_found: int
    ads_saved: int
    destination_url: Url | None
    website_analysis_dispatched: bool


class AnalysePageDeepUseCase:
    """Use case for deep page analysis.

    This use case:
    1. Fetches detailed ads via MetaAdsPort
    2. Saves all ads to AdsRepository
    3. Extracts the best destination URL
    4. Dispatches website analysis task
    5. Updates scan progress
    """

    def __init__(
        self,
        meta_ads_port: MetaAdsPort,
        ads_repository: AdsRepository,
        scan_repository: ScanRepository,
        page_repository: PageRepository,
        task_dispatcher: TaskDispatcherPort,
        logger: LoggingPort,
    ) -> None:
        self._meta_ads = meta_ads_port
        self._ads_repo = ads_repository
        self._scan_repo = scan_repository
        self._page_repo = page_repository
        self._task_dispatcher = task_dispatcher
        self._logger = logger

    async def execute(
        self,
        page_id: str,
        country: Country,
        scan_id: ScanId,
    ) -> AnalysePageDeepResult:
        """Execute the deep page analysis use case.

        Args:
            page_id: The page identifier.
            country: Target country for filtering.
            scan_id: The scan operation identifier.

        Returns:
            AnalysePageDeepResult with analysis results.

        Raises:
            EntityNotFoundError: If page does not exist.
        """
        self._logger.info(
            "Starting deep page analysis",
            page_id=page_id,
            country=str(country),
            scan_id=str(scan_id),
        )

        # Verify page exists
        page = await self._page_repo.get(page_id)
        if page is None:
            raise EntityNotFoundError("Page", page_id)

        # Create and start scan
        scan = Scan.create(
            page_id=page_id,
            scan_type=ScanType.FULL,
        )
        # Override with provided scan_id
        scan = Scan(
            id=scan_id,
            page_id=page_id,
            scan_type=ScanType.FULL,
            status=scan.status,
            created_at=scan.created_at,
            updated_at=scan.updated_at,
        )
        scan = scan.start()
        await self._scan_repo.save_scan(scan)

        try:
            # Fetch detailed ads
            raw_ads = await self._meta_ads.get_ads_details(
                page_id=page_id,
                country=country,
            )

            # Convert to Ad entities
            ads: list[Ad] = []
            destination_urls: list[tuple[Url, int]] = []  # (url, priority)

            for raw_ad in raw_ads:
                ad = self._convert_detailed_ad(raw_ad, page_id)
                if ad:
                    ads.append(ad)

                    # Extract destination URL with priority
                    url = self._extract_destination_url(raw_ad)
                    if url:
                        # Higher priority for link_title, lower for caption
                        priority = 2 if "link_title" in raw_ad else 1
                        destination_urls.append((url, priority))

            # Save ads
            if ads:
                await self._ads_repo.save_many(ads)

            # Determine best destination URL
            best_url: Url | None = None
            if destination_urls:
                # Sort by priority (highest first) and take first
                destination_urls.sort(key=lambda x: -x[1])
                best_url = destination_urls[0][0]

            # Dispatch website analysis if we have a URL
            website_dispatched = False
            if best_url:
                await self._task_dispatcher.dispatch_analyse_website(
                    page_id=page_id,
                    url=best_url,
                )
                website_dispatched = True

            # Complete scan
            result = ScanResult(
                ads_found=len(ads),
                new_ads=len(ads),  # All are new in this context
                is_shopify=None,  # Will be determined by website analysis
            )
            scan = scan.complete(result)
            await self._scan_repo.save_scan(scan)

            self._logger.info(
                "Deep page analysis completed",
                page_id=page_id,
                ads_found=len(ads),
                destination_url=str(best_url) if best_url else None,
                website_dispatched=website_dispatched,
            )

            return AnalysePageDeepResult(
                page_id=page_id,
                ads_found=len(ads),
                ads_saved=len(ads),
                destination_url=best_url,
                website_analysis_dispatched=website_dispatched,
            )

        except Exception as e:
            # Record scan failure
            scan = scan.fail(str(e))
            await self._scan_repo.save_scan(scan)
            self._logger.error(
                "Deep page analysis failed",
                page_id=page_id,
                error=str(e),
            )
            raise

    def _convert_detailed_ad(
        self,
        raw: dict[str, Any],
        page_id: str,
    ) -> Ad | None:
        """Convert a detailed raw ad dict to an Ad entity.

        Args:
            raw: Raw dictionary from Meta Ads API.
            page_id: The page identifier.

        Returns:
            Ad entity or None if conversion fails.
        """
        try:
            ad_id = raw.get("id") or str(uuid.uuid4())
            meta_ad_id = raw.get("ad_library_id", ad_id)

            # Parse URLs
            link_url = self._extract_destination_url(raw)
            image_url = self._parse_url(raw.get("image_url"))
            video_url = self._parse_url(raw.get("video_url"))

            # Parse platforms
            platforms: list[AdPlatform] = []
            for platform_str in raw.get("platforms", []):
                try:
                    platforms.append(AdPlatform(platform_str.lower()))
                except ValueError:
                    platforms.append(AdPlatform.UNKNOWN)

            # Parse dates
            started_at = self._parse_date(raw.get("start_date"))

            # Parse metrics
            impressions = raw.get("impressions", {})
            spend = raw.get("spend", {})

            ad = Ad(
                id=ad_id,
                page_id=page_id,
                meta_page_id=page_id,
                meta_ad_id=meta_ad_id,
                title=raw.get("ad_creative_title"),
                body=raw.get("ad_creative_body"),
                link_url=link_url,
                image_url=image_url,
                video_url=video_url,
                cta_type=raw.get("call_to_action_type"),
                status=AdStatus.ACTIVE if raw.get("is_active", True) else AdStatus.INACTIVE,
                platforms=platforms,
                started_at=started_at,
                impressions_lower=impressions.get("lower_bound"),
                impressions_upper=impressions.get("upper_bound"),
                spend_lower=spend.get("lower_bound"),
                spend_upper=spend.get("upper_bound"),
                currency=raw.get("currency"),
            )

            return ad

        except Exception:
            return None

    def _extract_destination_url(self, raw: dict[str, Any]) -> Url | None:
        """Extract the best destination URL from raw ad data.

        Priority: link_url > link_title > link_caption

        Args:
            raw: Raw ad dictionary.

        Returns:
            Url or None if not found.
        """
        for field in ["link_url", "link_title", "link_caption"]:
            url_str = raw.get(field)
            if url_str:
                url = self._parse_url(url_str)
                if url:
                    return url
        return None

    def _parse_url(self, url_str: str | None) -> Url | None:
        """Parse a URL string to Url value object.

        Args:
            url_str: URL string or None.

        Returns:
            Url or None if invalid.
        """
        if not url_str:
            return None
        try:
            return Url(url_str)
        except InvalidUrlError:
            return None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse a date string to datetime.

        Args:
            date_str: ISO date string or None.

        Returns:
            datetime or None if invalid.
        """
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

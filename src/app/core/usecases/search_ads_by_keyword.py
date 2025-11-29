"""Search Ads By Keyword Use Case.

Searches for ads by keyword and groups them by page.
"""

from dataclasses import dataclass
from typing import Any
import uuid

from ..domain import (
    Ad,
    AdStatus,
    Country,
    Language,
    ScanId,
    Url,
    KeywordRun,
    KeywordRunResult,
    InvalidUrlError,
)
from ..ports import (
    MetaAdsPort,
    PageRepository,
    KeywordRunRepository,
    LoggingPort,
)


@dataclass(frozen=True)
class SearchAdsResult:
    """Result of the search ads by keyword use case.

    Attributes:
        pages: List of unique page IDs found.
        count_ads: Total number of ads found.
        scan_id: The scan identifier.
        new_pages: Number of pages not previously seen.
    """

    pages: list[str]
    count_ads: int
    scan_id: ScanId
    new_pages: int = 0


class SearchAdsByKeywordUseCase:
    """Use case for searching ads by keyword.

    This use case:
    1. Validates the keyword
    2. Calls MetaAdsPort to search for ads
    3. Converts raw dicts to Ad entities
    4. Deduplicates ads
    5. Groups by page_id
    6. Filters out blacklisted pages
    7. Records the KeywordRun
    8. Returns aggregated results
    """

    def __init__(
        self,
        meta_ads_port: MetaAdsPort,
        page_repository: PageRepository,
        keyword_run_repository: KeywordRunRepository,
        logger: LoggingPort,
    ) -> None:
        self._meta_ads = meta_ads_port
        self._page_repo = page_repository
        self._keyword_run_repo = keyword_run_repository
        self._logger = logger

    async def execute(
        self,
        keyword: str,
        country: Country,
        language: Language | None = None,
        scan_id: ScanId | None = None,
        limit: int = 1000,
    ) -> SearchAdsResult:
        """Execute the search ads by keyword use case.

        Args:
            keyword: The search keyword (must not be empty).
            country: Target country for the search.
            language: Optional language filter.
            scan_id: Optional scan identifier (generated if not provided).
            limit: Maximum number of ads to fetch.

        Returns:
            SearchAdsResult with pages found and ad count.

        Raises:
            ValueError: If keyword is empty.
        """
        # Validate keyword
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("Keyword cannot be empty")

        # Generate scan_id if not provided
        if scan_id is None:
            scan_id = ScanId.generate()

        self._logger.info(
            "Starting keyword search",
            keyword=keyword,
            country=str(country),
            scan_id=str(scan_id),
        )

        # Create keyword run
        keyword_run = KeywordRun.create(
            keyword=keyword,
            country=country,
            page_limit=limit,
        )
        keyword_run = keyword_run.start()

        try:
            # Search for ads
            raw_ads = await self._meta_ads.search_ads_by_keyword(
                keyword=keyword,
                country=country,
                language=language,
                limit=limit,
            )

            # Convert to Ad entities and deduplicate
            ads_by_id: dict[str, Ad] = {}
            for raw_ad in raw_ads:
                ad = self._convert_raw_ad(raw_ad)
                if ad and ad.id not in ads_by_id:
                    ads_by_id[ad.id] = ad

            # Group by page_id
            pages_with_ads: dict[str, list[Ad]] = {}
            for ad in ads_by_id.values():
                if ad.page_id not in pages_with_ads:
                    pages_with_ads[ad.page_id] = []
                pages_with_ads[ad.page_id].append(ad)

            # Filter blacklisted pages
            filtered_pages: list[str] = []
            for page_id in pages_with_ads.keys():
                is_blacklisted = await self._page_repo.is_blacklisted(page_id)
                if not is_blacklisted:
                    filtered_pages.append(page_id)

            # Count new pages
            new_pages_count = 0
            for page_id in filtered_pages:
                exists = await self._page_repo.exists(page_id)
                if not exists:
                    new_pages_count += 1

            # Complete keyword run
            result = KeywordRunResult(
                total_ads_found=len(ads_by_id),
                unique_pages_found=len(filtered_pages),
                new_pages_found=new_pages_count,
                ads_processed=len(ads_by_id),
            )
            keyword_run = keyword_run.complete(result)
            await self._keyword_run_repo.save(keyword_run)

            self._logger.info(
                "Keyword search completed",
                keyword=keyword,
                ads_found=len(ads_by_id),
                pages_found=len(filtered_pages),
                new_pages=new_pages_count,
            )

            return SearchAdsResult(
                pages=filtered_pages,
                count_ads=len(ads_by_id),
                scan_id=scan_id,
                new_pages=new_pages_count,
            )

        except Exception as e:
            # Record failure
            keyword_run = keyword_run.fail(str(e))
            await self._keyword_run_repo.save(keyword_run)
            self._logger.error(
                "Keyword search failed",
                keyword=keyword,
                error=str(e),
            )
            raise

    def _convert_raw_ad(self, raw: dict[str, Any]) -> Ad | None:
        """Convert a raw ad dict from Meta API to an Ad entity.

        Args:
            raw: Raw dictionary from Meta Ads API.

        Returns:
            Ad entity or None if conversion fails.
        """
        try:
            ad_id = raw.get("id") or str(uuid.uuid4())
            page_id = raw.get("page_id", "")
            meta_page_id = raw.get("page_id", "")
            meta_ad_id = raw.get("ad_library_id", ad_id)

            if not page_id:
                self._logger.warning(
                    "Skipping ad without page_id",
                    raw_ad_id=raw.get("id"),
                )
                return None

            # Parse link URL if present
            link_url = None
            link_str = raw.get("link_url") or raw.get("link_caption")
            if link_str:
                try:
                    link_url = Url(link_str)
                except InvalidUrlError:
                    pass

            # Determine status
            status = AdStatus.ACTIVE
            if raw.get("is_active") is False:
                status = AdStatus.INACTIVE

            return Ad.create(
                id=ad_id,
                page_id=page_id,
                meta_page_id=meta_page_id,
                meta_ad_id=meta_ad_id,
                status=status,
            )

        except (KeyError, TypeError, AttributeError) as exc:
            self._logger.warning(
                "Failed to convert raw ad to domain entity",
                raw_ad_id=raw.get("id"),
                error=str(exc),
            )
            return None

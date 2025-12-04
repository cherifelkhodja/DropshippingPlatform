"""Search Ads By Keyword Use Case.

Searches for ads by keyword, creates pages, and saves everything to database.
"""

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
import re
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
from ..domain.entities.page import Page
from ..ports import (
    MetaAdsPort,
    PageRepository,
    KeywordRunRepository,
    AdsRepository,
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
    3. Groups ads by meta_page_id
    4. Filters out blacklisted pages
    5. Creates new pages with extracted URLs
    6. Saves pages and ads to database
    7. Records the KeywordRun
    8. Returns aggregated results
    """

    def __init__(
        self,
        meta_ads_port: MetaAdsPort,
        page_repository: PageRepository,
        keyword_run_repository: KeywordRunRepository,
        ads_repository: AdsRepository,
        logger: LoggingPort,
    ) -> None:
        self._meta_ads = meta_ads_port
        self._page_repo = page_repository
        self._keyword_run_repo = keyword_run_repository
        self._ads_repo = ads_repository
        self._logger = logger

    async def execute(
        self,
        keyword: str,
        country: Country,
        language: Language | None = None,
        scan_id: ScanId | None = None,
        limit: int = 1000,
    ) -> SearchAdsResult:
        """Execute the search ads by keyword use case."""
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

            # Group raw ads by meta_page_id
            raw_ads_list = list(raw_ads)
            ads_by_meta_page: dict[str, list[dict[str, Any]]] = {}
            for raw_ad in raw_ads_list:
                meta_page_id = raw_ad.get("page_id", "")
                if meta_page_id:
                    if meta_page_id not in ads_by_meta_page:
                        ads_by_meta_page[meta_page_id] = []
                    ads_by_meta_page[meta_page_id].append(raw_ad)

            # Filter blacklisted pages (by meta_page_id in future, for now skip)
            filtered_meta_pages = list(ads_by_meta_page.keys())

            self._logger.info(
                "Grouped ads by page",
                total_ads=len(raw_ads_list),
                unique_pages=len(filtered_meta_pages),
            )

            # Process each page
            new_pages_count = 0
            all_ads_to_save: list[Ad] = []
            saved_page_ids: list[str] = []

            pages_without_url = 0
            pages_with_invalid_url = 0

            for meta_page_id in filtered_meta_pages:
                page_ads = ads_by_meta_page[meta_page_id]

                try:
                    # Check if page already exists
                    existing_page = await self._page_repo.get_by_meta_page_id(meta_page_id)

                    if existing_page:
                        # Update ads count and save
                        page = existing_page.update_ads_count(
                            active=len(page_ads),
                            total=existing_page.total_ads_count + len(page_ads),
                        )
                        await self._page_repo.save(page)
                        page_uuid = page.id
                    else:
                        # Extract URL from ads
                        url_str = self._extract_best_url(page_ads)
                        page_name = page_ads[0].get("page_name", "") if page_ads else ""

                        if url_str:
                            # Try to create Url value object
                            try:
                                url_obj = Url(url_str)
                            except InvalidUrlError as url_err:
                                self._logger.debug(
                                    "Invalid URL format",
                                    meta_page_id=meta_page_id,
                                    url_str=url_str,
                                    error=str(url_err),
                                )
                                pages_with_invalid_url += 1
                                continue

                            # Create new page
                            page_uuid = str(uuid.uuid4())
                            page = Page.create(
                                id=page_uuid,
                                url=url_obj,
                                country=country,
                                meta_page_id=meta_page_id,
                                active_ads_count=len(page_ads),
                            )
                            await self._page_repo.save(page)
                            new_pages_count += 1
                        else:
                            # No URL found, skip this page
                            pages_without_url += 1
                            continue

                    saved_page_ids.append(page_uuid)

                    # Convert ads for this page
                    for raw_ad in page_ads:
                        ad = self._convert_raw_ad(raw_ad, page_uuid)
                        if ad:
                            all_ads_to_save.append(ad)

                except Exception as e:
                    self._logger.warning(
                        "Failed to process page",
                        meta_page_id=meta_page_id,
                        error=str(e),
                    )
                    continue

            if pages_without_url > 0 or pages_with_invalid_url > 0:
                self._logger.info(
                    "Pages skipped",
                    pages_without_url=pages_without_url,
                    pages_with_invalid_url=pages_with_invalid_url,
                )

            self._logger.info(
                "Processed pages",
                saved_pages=len(saved_page_ids),
                new_pages=new_pages_count,
                ads_to_save=len(all_ads_to_save),
            )

            # Save all ads in batch
            if all_ads_to_save:
                try:
                    await self._ads_repo.save_many(all_ads_to_save)
                    self._logger.info(
                        "Saved ads to database",
                        ads_count=len(all_ads_to_save),
                    )
                except Exception as e:
                    self._logger.error(
                        "Failed to save ads",
                        error=str(e),
                    )

            # Complete keyword run
            result = KeywordRunResult(
                total_ads_found=len(raw_ads_list),
                unique_pages_found=len(saved_page_ids),
                new_pages_found=new_pages_count,
                ads_processed=len(all_ads_to_save),
            )
            keyword_run = keyword_run.complete(result)
            await self._keyword_run_repo.save(keyword_run)

            self._logger.info(
                "Keyword search completed",
                keyword=keyword,
                ads_found=len(raw_ads_list),
                pages_found=len(saved_page_ids),
                new_pages=new_pages_count,
                ads_saved=len(all_ads_to_save),
            )

            return SearchAdsResult(
                pages=saved_page_ids,
                count_ads=len(raw_ads_list),
                scan_id=scan_id,
                new_pages=new_pages_count,
            )

        except Exception as e:
            self._logger.error(
                "Keyword search failed",
                keyword=keyword,
                error=str(e),
            )
            # Try to record failure, but don't fail if this fails too
            try:
                keyword_run = keyword_run.fail(str(e))
                await self._keyword_run_repo.save(keyword_run)
            except Exception as save_error:
                self._logger.error(
                    "Failed to save keyword run failure",
                    error=str(save_error),
                )
            raise

    def _extract_best_url(self, ads: list[dict[str, Any]]) -> str | None:
        """Extract the most common URL from ads.

        Looks in ad_creative_link_captions, ad_creative_link_titles,
        ad_creative_link_descriptions, and page_name as fallback.

        Args:
            ads: List of raw ad dictionaries.

        Returns:
            Most common URL or None if no valid URL found.
        """
        urls: list[str] = []

        for ad in ads:
            # Try link captions first (often contains display URL like "example.com")
            captions = ad.get("ad_creative_link_captions", [])
            if isinstance(captions, list):
                urls.extend(captions)
            elif isinstance(captions, str) and captions:
                urls.append(captions)

            # Try link titles
            titles = ad.get("ad_creative_link_titles", [])
            if isinstance(titles, list):
                urls.extend(titles)
            elif isinstance(titles, str) and titles:
                urls.append(titles)

            # Try link descriptions (sometimes contains URL)
            descriptions = ad.get("ad_creative_link_descriptions", [])
            if isinstance(descriptions, list):
                urls.extend(descriptions)
            elif isinstance(descriptions, str) and descriptions:
                urls.append(descriptions)

        # Clean and validate URLs
        valid_urls: list[str] = []
        for url in urls:
            if not url or not isinstance(url, str):
                continue
            cleaned = self._clean_url(url)
            if cleaned:
                valid_urls.append(cleaned)

        if not valid_urls:
            # Fallback: try to extract domain from page_name
            # Some page names are actually domains like "example.com"
            for ad in ads:
                page_name = ad.get("page_name", "")
                if page_name and isinstance(page_name, str):
                    cleaned = self._clean_url(page_name)
                    if cleaned:
                        valid_urls.append(cleaned)
                        break

        if not valid_urls:
            return None

        # Return most common URL
        counter = Counter(valid_urls)
        most_common = counter.most_common(1)
        return most_common[0][0] if most_common else None

    def _clean_url(self, text: str) -> str | None:
        """Clean and validate a URL from ad text.

        Args:
            text: Raw text that might contain a URL.

        Returns:
            Cleaned URL or None if invalid.
        """
        if not text:
            return None

        text = text.strip()

        # Skip obvious non-URLs (common CTA text)
        lower_text = text.lower()
        skip_patterns = [
            "shop now", "learn more", "sign up", "get started",
            "buy now", "order now", "subscribe", "contact us",
            "voir plus", "en savoir plus", "acheter", "commander",
            "s'inscrire", "nous contacter", "decouvrir",
        ]
        if lower_text in skip_patterns:
            return None

        # If it's already a full URL
        if text.startswith(("http://", "https://")):
            try:
                parsed = urlparse(text)
                if parsed.netloc:
                    return f"{parsed.scheme}://{parsed.netloc}"
            except Exception:
                pass

        # Try to extract domain from text
        # Match patterns like "example.com", "www.example.com", "shop.example.co.uk"
        # More permissive pattern to catch more domains
        domain_pattern = r"(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,})"
        match = re.search(domain_pattern, text)
        if match:
            domain = match.group(1)
            # Validate it looks like a real domain (has at least one dot and valid TLD)
            if "." in domain and len(domain.split(".")[-1]) >= 2:
                return f"https://{domain}"

        return None

    def _convert_raw_ad(self, raw: dict[str, Any], page_uuid: str) -> Ad | None:
        """Convert a raw ad dict from Meta API to an Ad entity.

        Args:
            raw: Raw dictionary from Meta Ads API.
            page_uuid: The internal page UUID to link to.

        Returns:
            Ad entity or None if conversion fails.
        """
        try:
            ad_id = str(uuid.uuid4())  # Generate internal UUID
            meta_page_id = raw.get("page_id", "")
            meta_ad_id = raw.get("id", "")

            if not meta_ad_id:
                return None

            # Extract creative content
            bodies = raw.get("ad_creative_bodies", [])
            body = bodies[0] if isinstance(bodies, list) and bodies else ""

            titles = raw.get("ad_creative_link_titles", [])
            title = titles[0] if isinstance(titles, list) and titles else ""

            captions = raw.get("ad_creative_link_captions", [])
            link_caption = captions[0] if isinstance(captions, list) and captions else ""

            # Normalize link_url to ensure it has a protocol
            link_url = None
            if link_caption:
                if link_caption.startswith(("http://", "https://")):
                    link_url = link_caption
                else:
                    # Add https:// prefix if missing
                    link_url = f"https://{link_caption}"

            snapshot_url = raw.get("ad_snapshot_url", "")

            # Platforms
            platforms = raw.get("publisher_platforms", [])
            if isinstance(platforms, str):
                platforms = [platforms]

            # Status
            status = AdStatus.ACTIVE

            return Ad.create(
                id=ad_id,
                page_id=page_uuid,
                meta_page_id=meta_page_id,
                meta_ad_id=meta_ad_id,
                status=status,
                title=title,
                body=body,
                link_url=link_url,
                image_url=snapshot_url,
                platforms=platforms if isinstance(platforms, list) else [],
            )

        except Exception as exc:
            self._logger.warning(
                "Failed to convert raw ad to domain entity",
                raw_ad_id=raw.get("id"),
                error=str(exc),
            )
            return None

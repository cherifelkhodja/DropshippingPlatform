"""Extract Product Count Use Case.

Extracts product count from website sitemaps.
"""

from dataclasses import dataclass

from ..domain import (
    Url,
    Country,
    PageStatus,
    EntityNotFoundError,
    SitemapNotFoundError,
)
from ..ports import (
    SitemapPort,
    PageRepository,
    LoggingPort,
)


@dataclass(frozen=True)
class ExtractProductCountResult:
    """Result of the extract product count use case.

    Attributes:
        page_id: The page identifier.
        product_count: Number of products found.
        sitemaps_found: Number of sitemaps discovered.
        previous_count: Previous product count.
    """

    page_id: str
    product_count: int
    sitemaps_found: int
    previous_count: int = 0


class ExtractProductCountUseCase:
    """Use case for extracting product count from sitemaps.

    This use case:
    1. Discovers sitemaps via SitemapPort
    2. Extracts product count
    3. Updates Page.product_count
    4. Updates Page.state
    """

    def __init__(
        self,
        sitemap_port: SitemapPort,
        page_repository: PageRepository,
        logger: LoggingPort,
    ) -> None:
        self._sitemap = sitemap_port
        self._page_repo = page_repository
        self._logger = logger

    async def execute(
        self,
        page_id: str,
        website_url: Url,
        country: Country,
    ) -> ExtractProductCountResult:
        """Execute the extract product count use case.

        Args:
            page_id: The page identifier.
            website_url: The website URL to analyze.
            country: Target country for filtering.

        Returns:
            ExtractProductCountResult with product count.

        Raises:
            EntityNotFoundError: If page does not exist.
            SitemapNotFoundError: If no sitemaps are found.
        """
        self._logger.info(
            "Starting product count extraction",
            page_id=page_id,
            url=str(website_url),
            country=str(country),
        )

        # Get page
        page = await self._page_repo.get(page_id)
        if page is None:
            raise EntityNotFoundError("Page", page_id)

        previous_count = int(page.product_count) if page.product_count else 0

        # Discover sitemaps
        try:
            sitemap_urls = await self._sitemap.get_sitemap_urls(website_url)
        except SitemapNotFoundError:
            self._logger.warning(
                "No sitemaps found",
                page_id=page_id,
                url=str(website_url),
            )
            # Return zero count but don't fail
            return ExtractProductCountResult(
                page_id=page_id,
                product_count=0,
                sitemaps_found=0,
                previous_count=previous_count,
            )

        if not sitemap_urls:
            self._logger.warning(
                "No sitemaps found",
                page_id=page_id,
                url=str(website_url),
            )
            return ExtractProductCountResult(
                page_id=page_id,
                product_count=0,
                sitemaps_found=0,
                previous_count=previous_count,
            )

        # Extract product count
        product_count = await self._sitemap.extract_product_count(
            sitemap_urls=sitemap_urls,
            country=country,
        )

        # Update page
        from ..domain import Page

        updated_page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state,
            country=page.country,
            language=page.language,
            currency=page.currency,
            category=page.category,
            product_count=product_count,
            is_shopify=page.is_shopify,
            shopify_profile_id=page.shopify_profile_id,
            active_ads_count=page.active_ads_count,
            total_ads_count=page.total_ads_count,
            score=page.score,
            first_seen_at=page.first_seen_at,
            last_scanned_at=page.last_scanned_at,
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

        # Transition to ACTIVE if verified and has products
        if page.state.status == PageStatus.VERIFIED_SHOPIFY and int(product_count) > 0:
            updated_page = updated_page.transition_state(PageStatus.ACTIVE)

        await self._page_repo.save(updated_page)

        self._logger.info(
            "Product count extraction completed",
            page_id=page_id,
            product_count=int(product_count),
            sitemaps_found=len(sitemap_urls),
            previous_count=previous_count,
        )

        return ExtractProductCountResult(
            page_id=page_id,
            product_count=int(product_count),
            sitemaps_found=len(sitemap_urls),
            previous_count=previous_count,
        )

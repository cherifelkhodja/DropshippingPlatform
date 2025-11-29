"""Sitemap Port.

Interface for sitemap parsing and product counting.
"""

from typing import Protocol

from ..domain.value_objects import Url, Country, ProductCount


class SitemapPort(Protocol):
    """Port interface for sitemap operations.

    This port defines the contract for discovering and parsing
    sitemaps to extract product URLs and count products.
    """

    async def get_sitemap_urls(
        self,
        website: Url,
    ) -> list[Url]:
        """Discover sitemap URLs for a website.

        Looks for sitemap.xml, robots.txt sitemap references,
        and common sitemap patterns (e.g., sitemap_products.xml).

        Args:
            website: The website URL to discover sitemaps for.

        Returns:
            List of discovered sitemap URLs.

        Raises:
            SitemapNotFoundError: If no relevant sitemap is found.
            ScrapingError: On network or parsing errors.
        """
        ...

    async def extract_product_count(
        self,
        sitemap_urls: list[Url],
        country: Country,
    ) -> ProductCount:
        """Extract the total product count from sitemaps.

        Parses the provided sitemap URLs and counts product entries,
        optionally filtering by country/locale if the sitemap contains
        localized URLs.

        Args:
            sitemap_urls: List of sitemap URLs to parse.
            country: Target country for filtering (if applicable).

        Returns:
            ProductCount representing the total number of products.

        Raises:
            SitemapParsingError: If sitemaps cannot be parsed.
            ScrapingError: On network errors.
        """
        ...

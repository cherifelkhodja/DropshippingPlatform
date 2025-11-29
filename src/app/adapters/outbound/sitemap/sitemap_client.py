"""Sitemap Client.

Implementation of SitemapPort for sitemap discovery and product counting.
"""

import re

import aiohttp
from lxml import etree

from src.app.core.domain.errors import (
    ScrapingError,
    SitemapNotFoundError,
    SitemapParsingError,
)
from src.app.core.domain.value_objects import Country, ProductCount, Url
from src.app.core.ports.logging_port import LoggingPort
from src.app.infrastructure.http.base_http_client import BaseHttpClient


# XML namespaces commonly used in sitemaps
SITEMAP_NAMESPACES = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "xhtml": "http://www.w3.org/1999/xhtml",
}

# Patterns to identify product sitemaps (prioritized order)
PRODUCT_SITEMAP_PATTERNS = [
    re.compile(
        r"sitemap_products_[a-z]{2}_\d+\.xml", re.IGNORECASE
    ),  # sitemap_products_fr_1.xml
    re.compile(r"sitemap_products_\d+\.xml", re.IGNORECASE),  # sitemap_products_1.xml
    re.compile(r"sitemap_products\.xml", re.IGNORECASE),  # sitemap_products.xml
    re.compile(r"products.*sitemap.*\.xml", re.IGNORECASE),  # products-sitemap.xml
    re.compile(r"sitemap.*products.*\.xml", re.IGNORECASE),  # sitemap-products.xml
]

# Patterns to identify product URLs in sitemap entries
PRODUCT_URL_PATTERNS = [
    re.compile(r"/products/", re.IGNORECASE),
    re.compile(r"/product/", re.IGNORECASE),
    re.compile(r"/p/", re.IGNORECASE),
    re.compile(r"/shop/", re.IGNORECASE),
]


class SitemapClient:
    """Sitemap parser implementing SitemapPort.

    Discovers sitemaps and extracts product counts using lxml.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        logger: LoggingPort,
    ) -> None:
        """Initialize sitemap client.

        Args:
            session: aiohttp client session.
            logger: Logging port for structured logging.
        """
        self._http = BaseHttpClient(session=session, logger=logger)
        self._logger = logger

    async def get_sitemap_urls(
        self,
        website: Url,
    ) -> list[Url]:
        """Discover sitemap URLs for a website.

        Looks for sitemap.xml and parses sitemap index to find product sitemaps.

        Args:
            website: The website URL to discover sitemaps for.

        Returns:
            List of discovered sitemap URLs, prioritized for products.

        Raises:
            SitemapNotFoundError: If no relevant sitemap is found.
            ScrapingError: On network or parsing errors.
        """
        self._logger.info(
            "Discovering sitemaps",
            website=website.value,
        )

        base_url = self._get_base_url(website)
        sitemap_urls: list[str] = []

        # Try common sitemap locations
        sitemap_locations = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemaps.xml",
        ]

        for sitemap_url in sitemap_locations:
            try:
                discovered = await self._fetch_and_parse_sitemap_index(sitemap_url)
                if discovered:
                    sitemap_urls.extend(discovered)
                    break
            except (ScrapingError, SitemapParsingError):
                continue

        if not sitemap_urls:
            self._logger.warning(
                "No sitemaps found",
                website=website.value,
            )
            raise SitemapNotFoundError(website=website.value)

        # Prioritize product sitemaps
        prioritized = self._prioritize_product_sitemaps(sitemap_urls)

        self._logger.info(
            "Sitemaps discovered",
            website=website.value,
            total_count=len(sitemap_urls),
            prioritized_count=len(prioritized),
        )

        return [Url(value=url) for url in prioritized]

    async def extract_product_count(
        self,
        sitemap_urls: list[Url],
        country: Country,
    ) -> ProductCount:
        """Extract the total product count from sitemaps.

        Args:
            sitemap_urls: List of sitemap URLs to parse.
            country: Target country for filtering (used for locale matching).

        Returns:
            ProductCount representing the total number of products.

        Raises:
            SitemapParsingError: If sitemaps cannot be parsed.
            ScrapingError: On network errors.
        """
        self._logger.info(
            "Extracting product count",
            sitemap_count=len(sitemap_urls),
            country=country.code,
        )

        total_products = 0
        country_code_lower = country.code.lower()

        for sitemap_url in sitemap_urls:
            try:
                product_urls = await self._extract_urls_from_sitemap(sitemap_url.value)

                # Count URLs that look like product pages
                for url in product_urls:
                    if self._is_product_url(url):
                        # Optionally filter by country/locale in URL
                        if self._matches_country(url, country_code_lower):
                            total_products += 1

            except (ScrapingError, SitemapParsingError) as exc:
                self._logger.warning(
                    "Failed to parse sitemap",
                    sitemap_url=sitemap_url.value,
                    error=str(exc),
                )
                continue

        self._logger.info(
            "Product count extracted",
            total_products=total_products,
            country=country.code,
        )

        return ProductCount(value=total_products)

    async def _fetch_and_parse_sitemap_index(
        self,
        sitemap_url: str,
    ) -> list[str]:
        """Fetch and parse a sitemap index to get individual sitemap URLs.

        Args:
            sitemap_url: URL of the sitemap or sitemap index.

        Returns:
            List of sitemap URLs found.

        Raises:
            ScrapingError: On network errors.
            SitemapParsingError: On XML parsing errors.
        """
        response = await self._http.get(
            url=sitemap_url,
            timeout_seconds=15,
            headers={"Accept": "application/xml, text/xml"},
        )

        async with response:
            content = await response.text()

        return self._parse_sitemap_xml(content, sitemap_url)

    async def _extract_urls_from_sitemap(
        self,
        sitemap_url: str,
    ) -> list[str]:
        """Extract all URLs from a sitemap.

        Args:
            sitemap_url: URL of the sitemap.

        Returns:
            List of URLs found in the sitemap.

        Raises:
            ScrapingError: On network errors.
            SitemapParsingError: On XML parsing errors.
        """
        response = await self._http.get(
            url=sitemap_url,
            timeout_seconds=15,
            headers={"Accept": "application/xml, text/xml"},
        )

        async with response:
            content = await response.text()

        return self._parse_url_entries(content, sitemap_url)

    def _parse_sitemap_xml(
        self,
        content: str,
        source_url: str,
    ) -> list[str]:
        """Parse sitemap XML content to extract sitemap URLs.

        Args:
            content: XML content string.
            source_url: Source URL for error reporting.

        Returns:
            List of sitemap URLs found.

        Raises:
            SitemapParsingError: On XML parsing errors.
        """
        try:
            root = etree.fromstring(content.encode("utf-8"))
        except etree.XMLSyntaxError as exc:
            raise SitemapParsingError(
                sitemap_url=source_url,
                reason=f"Invalid XML: {exc}",
            ) from exc

        urls: list[str] = []

        # Try sitemap index format (<sitemapindex>/<sitemap>/<loc>)
        for sitemap in root.findall(".//sm:sitemap/sm:loc", SITEMAP_NAMESPACES):
            if sitemap.text:
                urls.append(sitemap.text.strip())

        # Also try without namespace (some sitemaps don't use namespace)
        if not urls:
            for sitemap in root.findall(".//sitemap/loc"):
                if sitemap.text:
                    urls.append(sitemap.text.strip())

        # If no sitemap index entries, treat as regular sitemap and return the URL itself
        if not urls:
            # Check if this is a urlset (regular sitemap)
            urlset = root.find(".//sm:url", SITEMAP_NAMESPACES) or root.find(".//url")
            if urlset is not None:
                urls.append(source_url)

        return urls

    def _parse_url_entries(
        self,
        content: str,
        source_url: str,
    ) -> list[str]:
        """Parse sitemap XML to extract URL entries.

        Args:
            content: XML content string.
            source_url: Source URL for error reporting.

        Returns:
            List of page URLs found.

        Raises:
            SitemapParsingError: On XML parsing errors.
        """
        try:
            root = etree.fromstring(content.encode("utf-8"))
        except etree.XMLSyntaxError as exc:
            raise SitemapParsingError(
                sitemap_url=source_url,
                reason=f"Invalid XML: {exc}",
            ) from exc

        urls: list[str] = []

        # Try with namespace
        for loc in root.findall(".//sm:url/sm:loc", SITEMAP_NAMESPACES):
            if loc.text:
                urls.append(loc.text.strip())

        # Try without namespace
        if not urls:
            for loc in root.findall(".//url/loc"):
                if loc.text:
                    urls.append(loc.text.strip())

        return urls

    def _prioritize_product_sitemaps(
        self,
        sitemap_urls: list[str],
    ) -> list[str]:
        """Sort sitemap URLs to prioritize product sitemaps.

        Args:
            sitemap_urls: List of sitemap URLs.

        Returns:
            Sorted list with product sitemaps first.
        """
        prioritized: list[str] = []
        other: list[str] = []

        for url in sitemap_urls:
            is_product_sitemap = any(
                pattern.search(url) for pattern in PRODUCT_SITEMAP_PATTERNS
            )
            if is_product_sitemap:
                prioritized.append(url)
            else:
                other.append(url)

        return prioritized + other

    def _is_product_url(self, url: str) -> bool:
        """Check if a URL appears to be a product page.

        Args:
            url: URL to check.

        Returns:
            True if URL looks like a product page.
        """
        return any(pattern.search(url) for pattern in PRODUCT_URL_PATTERNS)

    def _matches_country(self, url: str, country_code: str) -> bool:
        """Check if URL matches the target country/locale.

        Args:
            url: URL to check.
            country_code: Lowercase country code.

        Returns:
            True if URL matches country or has no country indicator.
        """
        # URLs without country codes always match
        url_lower = url.lower()

        # Check for common locale patterns
        locale_patterns = [
            f"/{country_code}/",
            f"/{country_code}-",
            f"_{country_code}_",
            f"_{country_code}.",
            f".{country_code}/",
        ]

        # If URL has any locale indicator, it should match the target
        has_locale = any(
            f"/{code}/" in url_lower or f"_{code}_" in url_lower
            for code in ["fr", "en", "de", "es", "it", "nl", "pt"]
        )

        if not has_locale:
            return True

        return any(pattern in url_lower for pattern in locale_patterns)

    def _get_base_url(self, url: Url) -> str:
        """Extract base URL (protocol + domain) from a URL.

        Args:
            url: Full URL.

        Returns:
            Base URL string.
        """
        value = url.value
        # Remove trailing slash
        if value.endswith("/"):
            value = value[:-1]

        # Extract protocol + domain
        parts = value.split("/")
        if len(parts) >= 3:
            return f"{parts[0]}//{parts[2]}"

        return value

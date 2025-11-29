"""Analyse Website Use Case.

Analyzes a website to detect Shopify and extract store information.
"""

from dataclasses import dataclass
import re
import uuid

from ..domain import (
    Page,
    PageStatus,
    ShopifyProfile,
    ShopifyTheme,
    ShopifyApp,
    Url,
    Country,
    Currency,
    Category,
    PaymentMethod,
    PaymentMethods,
    EntityNotFoundError,
)
from ..ports import (
    HtmlScraperPort,
    PageRepository,
    TaskDispatcherPort,
    LoggingPort,
)


@dataclass(frozen=True)
class AnalyseWebsiteResult:
    """Result of the analyse website use case.

    Attributes:
        page_id: The page identifier.
        is_shopify: Whether the site is a Shopify store.
        shop_name: Detected shop name.
        theme_name: Detected theme name.
        currency: Detected currency.
        category: Detected category.
        payment_methods: Detected payment methods.
        sitemap_count_dispatched: Whether sitemap counting was triggered.
    """

    page_id: str
    is_shopify: bool
    shop_name: str | None = None
    theme_name: str | None = None
    currency: str | None = None
    category: str | None = None
    payment_methods: list[str] | None = None
    sitemap_count_dispatched: bool = False


class AnalyseWebsiteUseCase:
    """Use case for analyzing a website.

    This use case:
    1. Fetches HTML and headers via HtmlScraperPort
    2. Detects if it's a Shopify store
    3. Extracts: theme, currency, payment methods, category
    4. Creates/updates ShopifyProfile
    5. Dispatches sitemap product counting
    6. Saves Page with metadata
    """

    # Shopify detection patterns
    SHOPIFY_PATTERNS = [
        r'cdn\.shopify\.com',
        r'Shopify\.theme',
        r'shopify-section',
        r'shopify\.com/services',
        r'myshopify\.com',
        r'"shopify"',
        r'Shopify\.checkout',
    ]

    # Theme detection patterns
    THEME_PATTERNS = [
        (r'Shopify\.theme\s*=\s*\{[^}]*"name"\s*:\s*"([^"]+)"', 'name'),
        (r'theme-([a-zA-Z0-9-]+)', 'class'),
        (r'data-theme="([^"]+)"', 'data'),
    ]

    # Currency detection patterns
    CURRENCY_PATTERNS = [
        r'"currency"\s*:\s*"([A-Z]{3})"',
        r'data-currency="([A-Z]{3})"',
        r'Shopify\.currency\.active\s*=\s*"([A-Z]{3})"',
    ]

    # Payment method patterns
    PAYMENT_PATTERNS = {
        PaymentMethod.PAYPAL: [r'paypal', r'pp-button'],
        PaymentMethod.APPLE_PAY: [r'apple.?pay', r'apple-pay-button'],
        PaymentMethod.GOOGLE_PAY: [r'google.?pay', r'gpay'],
        PaymentMethod.SHOP_PAY: [r'shop.?pay', r'shopify.?pay'],
        PaymentMethod.KLARNA: [r'klarna'],
        PaymentMethod.AFTERPAY: [r'afterpay', r'clearpay'],
        PaymentMethod.AFFIRM: [r'affirm'],
        PaymentMethod.CREDIT_CARD: [r'credit.?card', r'visa', r'mastercard', r'amex'],
    }

    # Category detection patterns
    CATEGORY_PATTERNS = {
        "fashion": [r'fashion', r'clothing', r'apparel', r'wear', r'dress'],
        "beauty": [r'beauty', r'cosmetic', r'skincare', r'makeup'],
        "electronics": [r'electronic', r'gadget', r'tech', r'phone'],
        "home": [r'home', r'furniture', r'decor', r'kitchen'],
        "jewelry": [r'jewelry', r'jewellery', r'ring', r'necklace'],
        "sports": [r'sport', r'fitness', r'gym', r'athletic'],
        "pets": [r'pet', r'dog', r'cat', r'animal'],
        "kids": [r'kid', r'baby', r'child', r'toy'],
    }

    def __init__(
        self,
        html_scraper: HtmlScraperPort,
        page_repository: PageRepository,
        task_dispatcher: TaskDispatcherPort,
        logger: LoggingPort,
    ) -> None:
        self._scraper = html_scraper
        self._page_repo = page_repository
        self._task_dispatcher = task_dispatcher
        self._logger = logger

    async def execute(
        self,
        page_id: str,
        url: Url,
    ) -> AnalyseWebsiteResult:
        """Execute the website analysis use case.

        Args:
            page_id: The page identifier.
            url: The website URL to analyze.

        Returns:
            AnalyseWebsiteResult with analysis results.

        Raises:
            EntityNotFoundError: If page does not exist.
            ScrapingError: If HTML cannot be fetched.
        """
        self._logger.info(
            "Starting website analysis",
            page_id=page_id,
            url=str(url),
        )

        # Get page
        page = await self._page_repo.get(page_id)
        if page is None:
            raise EntityNotFoundError("Page", page_id)

        # Fetch HTML and headers
        html = await self._scraper.fetch_html(url)
        headers = await self._scraper.fetch_headers(url)

        # Detect Shopify
        is_shopify = self._detect_shopify(html, headers)

        # Initialize result values
        shop_name: str | None = None
        theme_name: str | None = None
        currency_code: str | None = None
        category_name: str | None = None
        payment_methods_list: list[str] = []
        sitemap_dispatched = False

        if is_shopify:
            # Extract Shopify-specific information
            shop_name = self._extract_shop_name(html, url)
            theme_name = self._extract_theme(html)
            currency_code = self._extract_currency(html)
            category_name = self._detect_category(html)
            payment_methods_list = self._detect_payment_methods(html)

            # Update page as Shopify
            profile_id = str(uuid.uuid4())
            updated_page = page.mark_as_shopify(profile_id)

            # Set currency if detected
            if currency_code:
                try:
                    currency = Currency(currency_code)
                    updated_page = Page(
                        id=updated_page.id,
                        url=updated_page.url,
                        domain=updated_page.domain,
                        state=updated_page.state,
                        country=updated_page.country,
                        language=updated_page.language,
                        currency=currency,
                        category=updated_page.category,
                        product_count=updated_page.product_count,
                        is_shopify=updated_page.is_shopify,
                        shopify_profile_id=updated_page.shopify_profile_id,
                        active_ads_count=updated_page.active_ads_count,
                        total_ads_count=updated_page.total_ads_count,
                        score=updated_page.score,
                        first_seen_at=updated_page.first_seen_at,
                        last_scanned_at=updated_page.last_scanned_at,
                        created_at=updated_page.created_at,
                        updated_at=updated_page.updated_at,
                    )
                except Exception:
                    pass

            # Set category if detected
            if category_name:
                try:
                    category = Category(category_name)
                    updated_page = Page(
                        id=updated_page.id,
                        url=updated_page.url,
                        domain=updated_page.domain,
                        state=updated_page.state,
                        country=updated_page.country,
                        language=updated_page.language,
                        currency=updated_page.currency,
                        category=category,
                        product_count=updated_page.product_count,
                        is_shopify=updated_page.is_shopify,
                        shopify_profile_id=updated_page.shopify_profile_id,
                        active_ads_count=updated_page.active_ads_count,
                        total_ads_count=updated_page.total_ads_count,
                        score=updated_page.score,
                        first_seen_at=updated_page.first_seen_at,
                        last_scanned_at=updated_page.last_scanned_at,
                        created_at=updated_page.created_at,
                        updated_at=updated_page.updated_at,
                    )
                except Exception:
                    pass

            await self._page_repo.save(updated_page)

            # Dispatch sitemap counting
            country = page.country or Country("US")
            await self._task_dispatcher.dispatch_sitemap_count(
                page_id=page_id,
                website=url,
                country=country,
            )
            sitemap_dispatched = True

        else:
            # Mark as not Shopify
            updated_page = page.mark_as_not_shopify()
            await self._page_repo.save(updated_page)

        self._logger.info(
            "Website analysis completed",
            page_id=page_id,
            is_shopify=is_shopify,
            shop_name=shop_name,
            theme=theme_name,
        )

        return AnalyseWebsiteResult(
            page_id=page_id,
            is_shopify=is_shopify,
            shop_name=shop_name,
            theme_name=theme_name,
            currency=currency_code,
            category=category_name,
            payment_methods=payment_methods_list if payment_methods_list else None,
            sitemap_count_dispatched=sitemap_dispatched,
        )

    def _detect_shopify(self, html: str, headers: dict[str, str]) -> bool:
        """Detect if the site is a Shopify store.

        Args:
            html: Page HTML content.
            headers: Response headers.

        Returns:
            True if Shopify is detected.
        """
        # Check headers for Shopify indicators
        server = headers.get("server", "").lower()
        if "shopify" in server:
            return True

        x_shopify = headers.get("x-shopify-stage")
        if x_shopify:
            return True

        # Check HTML patterns
        html_lower = html.lower()
        for pattern in self.SHOPIFY_PATTERNS:
            if re.search(pattern, html, re.IGNORECASE):
                return True

        return False

    def _extract_shop_name(self, html: str, url: Url) -> str | None:
        """Extract the shop name from HTML.

        Args:
            html: Page HTML content.
            url: The website URL.

        Returns:
            Shop name or None.
        """
        # Try to find shop name in meta tags
        patterns = [
            r'<meta[^>]*property="og:site_name"[^>]*content="([^"]+)"',
            r'<meta[^>]*name="application-name"[^>]*content="([^"]+)"',
            r'"shop_name"\s*:\s*"([^"]+)"',
            r'<title>([^<|]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) < 100:
                    return name

        # Fallback to domain
        return url.domain

    def _extract_theme(self, html: str) -> str | None:
        """Extract the Shopify theme name.

        Args:
            html: Page HTML content.

        Returns:
            Theme name or None.
        """
        for pattern, _ in self.THEME_PATTERNS:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_currency(self, html: str) -> str | None:
        """Extract the store currency.

        Args:
            html: Page HTML content.

        Returns:
            Currency code or None.
        """
        for pattern in self.CURRENCY_PATTERNS:
            match = re.search(pattern, html)
            if match:
                return match.group(1)

        return None

    def _detect_payment_methods(self, html: str) -> list[str]:
        """Detect available payment methods.

        Args:
            html: Page HTML content.

        Returns:
            List of detected payment method names.
        """
        detected: list[str] = []
        html_lower = html.lower()

        for method, patterns in self.PAYMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, html_lower):
                    detected.append(method.value)
                    break

        return detected

    def _detect_category(self, html: str) -> str | None:
        """Detect the store category from content.

        Args:
            html: Page HTML content.

        Returns:
            Category name or None.
        """
        html_lower = html.lower()
        category_scores: dict[str, int] = {}

        for category, patterns in self.CATEGORY_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, html_lower))
                score += matches

            if score > 0:
                category_scores[category] = score

        if category_scores:
            # Return category with highest score
            return max(category_scores, key=lambda k: category_scores[k])

        return None

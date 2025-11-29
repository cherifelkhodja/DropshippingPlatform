"""Shopify Profile Entity.

Represents detailed information about a Shopify store.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from ..value_objects import (
    Url,
    Country,
    Language,
    Currency,
    PaymentMethods,
    ProductCount,
    Category,
)


@dataclass
class ShopifyTheme:
    """Value object representing a Shopify theme.

    Attributes:
        name: Theme name.
        version: Theme version (if available).
        is_custom: Whether it's a custom theme.
    """

    name: str
    version: Optional[str] = None
    is_custom: bool = False


@dataclass
class ShopifyApp:
    """Value object representing a detected Shopify app.

    Attributes:
        name: App name.
        slug: App identifier/slug.
        category: App category (e.g., "marketing", "analytics").
    """

    name: str
    slug: Optional[str] = None
    category: Optional[str] = None


@dataclass
class ShopifyProfile:
    """Entity representing a Shopify store profile.

    A ShopifyProfile contains detailed information about a Shopify store,
    including its theme, apps, payment methods, and other characteristics.

    Attributes:
        id: Unique identifier for the profile.
        page_id: Reference to the associated Page entity.
        shop_name: Name of the Shopify store.
        shop_url: Main URL of the store.
        myshopify_domain: The .myshopify.com domain.
        country: Primary country of operation.
        language: Primary language.
        currency: Primary currency.
        category: Main product category.
        product_count: Number of products.
        theme: Detected Shopify theme.
        apps: List of detected apps.
        payment_methods: Accepted payment methods.
        has_reviews: Whether the store has product reviews.
        has_wishlist: Whether the store has wishlist functionality.
        has_live_chat: Whether the store has live chat.
        has_loyalty_program: Whether the store has a loyalty program.
        facebook_pixel_id: Detected Facebook Pixel ID.
        google_analytics_id: Detected Google Analytics ID.
        tiktok_pixel_id: Detected TikTok Pixel ID.
        estimated_monthly_revenue: Estimated monthly revenue range.
        trust_score: Computed trust/quality score.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    id: str
    page_id: str
    shop_name: str
    shop_url: Url
    myshopify_domain: Optional[str] = None
    country: Optional[Country] = None
    language: Optional[Language] = None
    currency: Optional[Currency] = None
    category: Optional[Category] = None
    product_count: ProductCount = field(default_factory=ProductCount.zero)
    theme: Optional[ShopifyTheme] = None
    apps: list[ShopifyApp] = field(default_factory=list)
    payment_methods: PaymentMethods = field(default_factory=PaymentMethods.empty)
    has_reviews: bool = False
    has_wishlist: bool = False
    has_live_chat: bool = False
    has_loyalty_program: bool = False
    facebook_pixel_id: Optional[str] = None
    google_analytics_id: Optional[str] = None
    tiktok_pixel_id: Optional[str] = None
    estimated_monthly_revenue: Optional[str] = None
    trust_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        id: str,
        page_id: str,
        shop_name: str,
        shop_url: Url,
    ) -> "ShopifyProfile":
        """Factory method to create a new ShopifyProfile.

        Args:
            id: Unique identifier.
            page_id: Associated Page ID.
            shop_name: Name of the store.
            shop_url: Store URL.

        Returns:
            A new ShopifyProfile instance.
        """
        now = datetime.utcnow()
        return cls(
            id=id,
            page_id=page_id,
            shop_name=shop_name,
            shop_url=shop_url,
            created_at=now,
            updated_at=now,
        )

    def update_product_count(self, count: ProductCount) -> "ShopifyProfile":
        """Update the product count.

        Args:
            count: New product count.

        Returns:
            Updated ShopifyProfile instance.
        """
        return ShopifyProfile(
            id=self.id,
            page_id=self.page_id,
            shop_name=self.shop_name,
            shop_url=self.shop_url,
            myshopify_domain=self.myshopify_domain,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=count,
            theme=self.theme,
            apps=self.apps,
            payment_methods=self.payment_methods,
            has_reviews=self.has_reviews,
            has_wishlist=self.has_wishlist,
            has_live_chat=self.has_live_chat,
            has_loyalty_program=self.has_loyalty_program,
            facebook_pixel_id=self.facebook_pixel_id,
            google_analytics_id=self.google_analytics_id,
            tiktok_pixel_id=self.tiktok_pixel_id,
            estimated_monthly_revenue=self.estimated_monthly_revenue,
            trust_score=self.trust_score,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def update_theme(self, theme: ShopifyTheme) -> "ShopifyProfile":
        """Update the detected theme.

        Args:
            theme: The detected theme.

        Returns:
            Updated ShopifyProfile instance.
        """
        return ShopifyProfile(
            id=self.id,
            page_id=self.page_id,
            shop_name=self.shop_name,
            shop_url=self.shop_url,
            myshopify_domain=self.myshopify_domain,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            theme=theme,
            apps=self.apps,
            payment_methods=self.payment_methods,
            has_reviews=self.has_reviews,
            has_wishlist=self.has_wishlist,
            has_live_chat=self.has_live_chat,
            has_loyalty_program=self.has_loyalty_program,
            facebook_pixel_id=self.facebook_pixel_id,
            google_analytics_id=self.google_analytics_id,
            tiktok_pixel_id=self.tiktok_pixel_id,
            estimated_monthly_revenue=self.estimated_monthly_revenue,
            trust_score=self.trust_score,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def add_app(self, app: ShopifyApp) -> "ShopifyProfile":
        """Add a detected app.

        Args:
            app: The detected app.

        Returns:
            Updated ShopifyProfile instance.
        """
        new_apps = self.apps + [app]
        return ShopifyProfile(
            id=self.id,
            page_id=self.page_id,
            shop_name=self.shop_name,
            shop_url=self.shop_url,
            myshopify_domain=self.myshopify_domain,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            theme=self.theme,
            apps=new_apps,
            payment_methods=self.payment_methods,
            has_reviews=self.has_reviews,
            has_wishlist=self.has_wishlist,
            has_live_chat=self.has_live_chat,
            has_loyalty_program=self.has_loyalty_program,
            facebook_pixel_id=self.facebook_pixel_id,
            google_analytics_id=self.google_analytics_id,
            tiktok_pixel_id=self.tiktok_pixel_id,
            estimated_monthly_revenue=self.estimated_monthly_revenue,
            trust_score=self.trust_score,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def update_payment_methods(self, methods: PaymentMethods) -> "ShopifyProfile":
        """Update payment methods.

        Args:
            methods: The payment methods.

        Returns:
            Updated ShopifyProfile instance.
        """
        return ShopifyProfile(
            id=self.id,
            page_id=self.page_id,
            shop_name=self.shop_name,
            shop_url=self.shop_url,
            myshopify_domain=self.myshopify_domain,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            theme=self.theme,
            apps=self.apps,
            payment_methods=methods,
            has_reviews=self.has_reviews,
            has_wishlist=self.has_wishlist,
            has_live_chat=self.has_live_chat,
            has_loyalty_program=self.has_loyalty_program,
            facebook_pixel_id=self.facebook_pixel_id,
            google_analytics_id=self.google_analytics_id,
            tiktok_pixel_id=self.tiktok_pixel_id,
            estimated_monthly_revenue=self.estimated_monthly_revenue,
            trust_score=self.trust_score,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def update_trust_score(self, score: float) -> "ShopifyProfile":
        """Update the trust score.

        Args:
            score: New trust score.

        Returns:
            Updated ShopifyProfile instance.
        """
        return ShopifyProfile(
            id=self.id,
            page_id=self.page_id,
            shop_name=self.shop_name,
            shop_url=self.shop_url,
            myshopify_domain=self.myshopify_domain,
            country=self.country,
            language=self.language,
            currency=self.currency,
            category=self.category,
            product_count=self.product_count,
            theme=self.theme,
            apps=self.apps,
            payment_methods=self.payment_methods,
            has_reviews=self.has_reviews,
            has_wishlist=self.has_wishlist,
            has_live_chat=self.has_live_chat,
            has_loyalty_program=self.has_loyalty_program,
            facebook_pixel_id=self.facebook_pixel_id,
            google_analytics_id=self.google_analytics_id,
            tiktok_pixel_id=self.tiktok_pixel_id,
            estimated_monthly_revenue=self.estimated_monthly_revenue,
            trust_score=score,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def has_tracking_pixels(self) -> bool:
        """Check if any tracking pixels are detected."""
        return any(
            [
                self.facebook_pixel_id,
                self.google_analytics_id,
                self.tiktok_pixel_id,
            ]
        )

    def is_well_equipped(self) -> bool:
        """Check if the store has good e-commerce features."""
        features = [
            self.has_reviews,
            self.payment_methods.has_digital_wallets(),
            self.has_tracking_pixels(),
            len(self.apps) >= 3,
        ]
        return sum(features) >= 3

    def get_app_count(self) -> int:
        """Get the number of detected apps."""
        return len(self.apps)

    def has_app(self, app_name: str) -> bool:
        """Check if a specific app is installed.

        Args:
            app_name: Name of the app to check.

        Returns:
            True if the app is detected.
        """
        return any(app.name.lower() == app_name.lower() for app in self.apps)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ShopifyProfile):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

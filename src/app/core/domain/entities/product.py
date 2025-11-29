"""Product Entity.

Represents a product from a Shopify store's catalog.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Product:
    """Entity representing a product in a store's catalog.

    A Product represents an item from a Shopify store that can be
    linked to advertising campaigns for analytics and insights.

    Attributes:
        id: Unique identifier for the product.
        page_id: Reference to the parent Page (store).
        handle: Shopify product handle (URL slug).
        title: Product title/name.
        url: Full URL to the product page.
        price_min: Minimum price across variants.
        price_max: Maximum price across variants.
        currency: Currency code (e.g., "EUR", "USD").
        available: Whether the product is currently available.
        tags: List of product tags/labels.
        vendor: Product vendor/brand name.
        image_url: URL to the main product image.
        product_type: Shopify product type classification.
        created_at: When the record was created.
        updated_at: When the record was last updated.
        raw_data: Original JSON data from Shopify (for future use).
    """

    id: str
    page_id: str
    handle: str
    title: str
    url: str
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    currency: Optional[str] = None
    available: bool = True
    tags: list[str] = field(default_factory=list)
    vendor: Optional[str] = None
    image_url: Optional[str] = None
    product_type: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: Optional[dict] = None

    @classmethod
    def create(
        cls,
        id: str,
        page_id: str,
        handle: str,
        title: str,
        url: str,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        currency: Optional[str] = None,
        available: bool = True,
        tags: Optional[list[str]] = None,
        vendor: Optional[str] = None,
        image_url: Optional[str] = None,
        product_type: Optional[str] = None,
        raw_data: Optional[dict] = None,
    ) -> "Product":
        """Factory method to create a new Product.

        Args:
            id: Unique identifier.
            page_id: Parent page (store) identifier.
            handle: Shopify product handle.
            title: Product title.
            url: Product page URL.
            price_min: Minimum price (optional).
            price_max: Maximum price (optional).
            currency: Currency code (optional).
            available: Availability status.
            tags: Product tags (optional).
            vendor: Vendor name (optional).
            image_url: Main image URL (optional).
            product_type: Product type (optional).
            raw_data: Raw JSON data (optional).

        Returns:
            A new Product instance.
        """
        now = datetime.utcnow()
        return cls(
            id=id,
            page_id=page_id,
            handle=handle,
            title=title,
            url=url,
            price_min=price_min,
            price_max=price_max,
            currency=currency,
            available=available,
            tags=tags or [],
            vendor=vendor,
            image_url=image_url,
            product_type=product_type,
            created_at=now,
            updated_at=now,
            raw_data=raw_data,
        )

    @classmethod
    def from_shopify_json(
        cls,
        id: str,
        page_id: str,
        base_url: str,
        data: dict,
    ) -> "Product":
        """Create a Product from Shopify products.json data.

        Args:
            id: Unique identifier for the product.
            page_id: Parent page (store) identifier.
            base_url: Base URL of the store (e.g., "https://store.com").
            data: Product data from Shopify products.json.

        Returns:
            A new Product instance.
        """
        handle = data.get("handle", "")
        title = data.get("title", "")
        url = f"{base_url.rstrip('/')}/products/{handle}"

        # Extract price range from variants
        variants = data.get("variants", [])
        prices: list[float] = []
        for variant in variants:
            price_str = variant.get("price")
            if price_str:
                try:
                    prices.append(float(price_str))
                except (ValueError, TypeError):
                    pass

        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None

        # Check availability from variants
        available = any(
            variant.get("available", False) for variant in variants
        )

        # Extract tags
        tags_raw = data.get("tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        else:
            tags = list(tags_raw) if tags_raw else []

        # Extract image URL
        images = data.get("images", [])
        image_url = images[0].get("src") if images else None

        return cls.create(
            id=id,
            page_id=page_id,
            handle=handle,
            title=title,
            url=url,
            price_min=price_min,
            price_max=price_max,
            currency=None,  # Not available in products.json
            available=available,
            tags=tags,
            vendor=data.get("vendor"),
            image_url=image_url,
            product_type=data.get("product_type"),
            raw_data=data,
        )

    def update_availability(self, available: bool) -> "Product":
        """Update the product's availability status.

        Args:
            available: New availability status.

        Returns:
            Updated Product instance.
        """
        return Product(
            id=self.id,
            page_id=self.page_id,
            handle=self.handle,
            title=self.title,
            url=self.url,
            price_min=self.price_min,
            price_max=self.price_max,
            currency=self.currency,
            available=available,
            tags=self.tags,
            vendor=self.vendor,
            image_url=self.image_url,
            product_type=self.product_type,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            raw_data=self.raw_data,
        )

    def update_pricing(
        self,
        price_min: Optional[float],
        price_max: Optional[float],
        currency: Optional[str] = None,
    ) -> "Product":
        """Update the product's pricing information.

        Args:
            price_min: New minimum price.
            price_max: New maximum price.
            currency: New currency code (optional).

        Returns:
            Updated Product instance.
        """
        return Product(
            id=self.id,
            page_id=self.page_id,
            handle=self.handle,
            title=self.title,
            url=self.url,
            price_min=price_min,
            price_max=price_max,
            currency=currency or self.currency,
            available=self.available,
            tags=self.tags,
            vendor=self.vendor,
            image_url=self.image_url,
            product_type=self.product_type,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            raw_data=self.raw_data,
        )

    def is_in_stock(self) -> bool:
        """Check if the product is currently in stock."""
        return self.available

    def has_price(self) -> bool:
        """Check if the product has pricing information."""
        return self.price_min is not None

    def get_price_range_display(self) -> str:
        """Get a display string for the price range.

        Returns:
            Formatted price range string or empty string if no prices.
        """
        if self.price_min is None:
            return ""

        currency = self.currency or ""
        if self.price_max and self.price_max != self.price_min:
            return f"{currency}{self.price_min:.2f} - {currency}{self.price_max:.2f}"
        return f"{currency}{self.price_min:.2f}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Product):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

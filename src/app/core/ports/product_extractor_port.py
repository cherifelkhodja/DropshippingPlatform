"""Product Extractor Port.

Interface for extracting products from e-commerce stores.
"""

from dataclasses import dataclass
from typing import Protocol

from ..domain.entities import Product


@dataclass(frozen=True)
class ProductExtractionResult:
    """Result of a product extraction operation.

    Attributes:
        products: List of extracted Product entities.
        total_found: Total number of products found in the source.
        source: Source of extraction (e.g., "products.json", "sitemap").
        error: Error message if extraction partially failed.
    """

    products: list[Product]
    total_found: int
    source: str
    error: str | None = None


class ProductExtractorPort(Protocol):
    """Port interface for product extraction operations.

    This port defines the contract for extracting product catalogs
    from e-commerce stores (primarily Shopify).
    """

    async def extract_products(
        self,
        page_id: str,
        store_url: str,
    ) -> ProductExtractionResult:
        """Extract products from a store's catalog.

        For Shopify stores, this typically fetches /products.json
        and parses the product data.

        Args:
            page_id: The page identifier to associate products with.
            store_url: The base URL of the store.

        Returns:
            ProductExtractionResult containing extracted products.

        Raises:
            ExtractionError: On network or parsing errors.
        """
        ...

    async def is_supported(self, store_url: str) -> bool:
        """Check if the store is supported for product extraction.

        Args:
            store_url: The base URL of the store.

        Returns:
            True if products can be extracted from this store.
        """
        ...

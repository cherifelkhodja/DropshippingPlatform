"""Product Extractor Package.

Implementations of ProductExtractorPort for extracting product catalogs.
"""

from src.app.adapters.outbound.product_extractor.shopify_product_extractor import (
    ShopifyProductExtractor,
)

__all__ = [
    "ShopifyProductExtractor",
]

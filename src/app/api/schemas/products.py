"""Product API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProductResponse(BaseModel):
    """Single product response."""

    id: str = Field(description="Product identifier")
    page_id: str = Field(description="Parent page identifier")
    handle: str = Field(description="Product handle (URL slug)")
    title: str = Field(description="Product title")
    url: str = Field(description="Product page URL")
    price_min: float | None = Field(default=None, description="Minimum price")
    price_max: float | None = Field(default=None, description="Maximum price")
    currency: str | None = Field(default=None, description="Currency code")
    available: bool = Field(description="Whether product is available")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    vendor: str | None = Field(default=None, description="Product vendor/brand")
    image_url: str | None = Field(default=None, description="Main product image URL")
    product_type: str | None = Field(default=None, description="Product type")
    created_at: datetime = Field(description="When product was first synced")
    updated_at: datetime = Field(description="When product was last updated")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "prod-12345",
                    "page_id": "page-12345",
                    "handle": "awesome-t-shirt",
                    "title": "Awesome T-Shirt",
                    "url": "https://example-store.com/products/awesome-t-shirt",
                    "price_min": 29.99,
                    "price_max": 34.99,
                    "currency": "USD",
                    "available": True,
                    "tags": ["clothing", "t-shirt", "summer"],
                    "vendor": "Example Brand",
                    "image_url": "https://cdn.shopify.com/...",
                    "product_type": "T-Shirts",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-03-20T15:45:00Z",
                }
            ]
        }
    }


class ProductListResponse(BaseModel):
    """Paginated product list response."""

    items: list[ProductResponse] = Field(description="List of products")
    total: int = Field(description="Total number of products for the page")
    page_id: str = Field(description="Parent page identifier")
    limit: int = Field(description="Maximum items returned")
    offset: int = Field(description="Offset for pagination")


class SyncProductsResponse(BaseModel):
    """Response from product sync operation."""

    page_id: str = Field(description="Page identifier")
    products_synced: int = Field(description="Number of products synced")
    products_extracted: int = Field(description="Number of products extracted from source")
    is_shopify: bool = Field(description="Whether the page is a Shopify store")
    source: str | None = Field(default=None, description="Source of product data")
    error: str | None = Field(default=None, description="Error message if any")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "page-12345",
                    "products_synced": 150,
                    "products_extracted": 150,
                    "is_shopify": True,
                    "source": "products.json",
                    "error": None,
                }
            ]
        }
    }

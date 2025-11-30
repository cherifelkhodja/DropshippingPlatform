"""Shopify Product Extractor.

Implementation of ProductExtractorPort for extracting products from Shopify stores.
"""

import json
import uuid

import aiohttp

from src.app.core.domain.entities.product import Product
from src.app.core.domain.errors import ScrapingError
from src.app.core.ports.logging_port import LoggingPort
from src.app.core.ports.product_extractor_port import ProductExtractionResult
from src.app.infrastructure.http.base_http_client import BaseHttpClient


# Maximum products per page in Shopify's products.json
SHOPIFY_PRODUCTS_PER_PAGE = 250

# Maximum pages to fetch (safety limit)
MAX_PAGES_TO_FETCH = 20


class ShopifyProductExtractor:
    """Shopify product catalog extractor implementing ProductExtractorPort.

    Extracts products from Shopify stores using the /products.json endpoint.
    This endpoint is publicly available on most Shopify stores.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        logger: LoggingPort,
    ) -> None:
        """Initialize Shopify product extractor.

        Args:
            session: aiohttp client session.
            logger: Logging port for structured logging.
        """
        self._http = BaseHttpClient(session=session, logger=logger)
        self._logger = logger

    async def extract_products(
        self,
        page_id: str,
        store_url: str,
    ) -> ProductExtractionResult:
        """Extract products from a Shopify store's catalog.

        Fetches products from /products.json endpoint, handling pagination
        if there are more than 250 products.

        Args:
            page_id: The page identifier to associate products with.
            store_url: The base URL of the store.

        Returns:
            ProductExtractionResult containing extracted products.

        Raises:
            ScrapingError: On network or parsing errors.
        """
        self._logger.info(
            "Starting product extraction",
            page_id=page_id,
            store_url=store_url,
        )

        base_url = self._normalize_url(store_url)
        all_products: list[Product] = []
        page = 1
        error_message: str | None = None

        try:
            while page <= MAX_PAGES_TO_FETCH:
                products_url = f"{base_url}/products.json?limit={SHOPIFY_PRODUCTS_PER_PAGE}&page={page}"

                self._logger.debug(
                    "Fetching products page",
                    page=page,
                    url=products_url,
                )

                try:
                    response = await self._http.get(
                        url=products_url,
                        timeout_seconds=30,
                        headers={"Accept": "application/json"},
                    )

                    async with response:
                        content = await response.text()
                        data = json.loads(content)

                except ScrapingError as exc:
                    # If first page fails, propagate the error
                    if page == 1:
                        raise
                    # If subsequent pages fail, log and stop pagination
                    self._logger.warning(
                        "Failed to fetch products page",
                        page=page,
                        error=str(exc),
                    )
                    error_message = f"Pagination stopped at page {page}: {exc}"
                    break

                except json.JSONDecodeError as exc:
                    if page == 1:
                        raise ScrapingError(
                            url=products_url,
                            reason=f"Invalid JSON response: {exc}",
                        ) from exc
                    error_message = f"Invalid JSON at page {page}"
                    break

                products_data = data.get("products", [])
                if not products_data:
                    # No more products
                    break

                # Convert to Product entities
                for product_data in products_data:
                    try:
                        product = Product.from_shopify_json(
                            id=str(uuid.uuid4()),
                            page_id=page_id,
                            base_url=base_url,
                            data=product_data,
                        )
                        all_products.append(product)
                    except Exception as exc:
                        self._logger.warning(
                            "Failed to parse product",
                            handle=product_data.get("handle", "unknown"),
                            error=str(exc),
                        )
                        continue

                # Check if we got a full page (might be more)
                if len(products_data) < SHOPIFY_PRODUCTS_PER_PAGE:
                    break

                page += 1

        except ScrapingError:
            raise
        except Exception as exc:
            self._logger.error(
                "Product extraction failed",
                page_id=page_id,
                store_url=store_url,
                error=str(exc),
            )
            raise ScrapingError(
                url=store_url,
                reason=f"Product extraction failed: {exc}",
            ) from exc

        self._logger.info(
            "Product extraction completed",
            page_id=page_id,
            products_extracted=len(all_products),
            pages_fetched=page,
        )

        return ProductExtractionResult(
            products=all_products,
            total_found=len(all_products),
            source="products.json",
            error=error_message,
        )

    async def is_supported(self, store_url: str) -> bool:
        """Check if the store supports product extraction via products.json.

        Args:
            store_url: The base URL of the store.

        Returns:
            True if products.json is accessible.
        """
        base_url = self._normalize_url(store_url)
        products_url = f"{base_url}/products.json?limit=1"

        try:
            response = await self._http.get(
                url=products_url,
                timeout_seconds=10,
                headers={"Accept": "application/json"},
            )

            async with response:
                content = await response.text()
                data = json.loads(content)

            # Check if response has products key (Shopify format)
            return "products" in data

        except (ScrapingError, json.JSONDecodeError):
            return False
        except Exception:
            return False

    def _normalize_url(self, url: str) -> str:
        """Normalize store URL to base format.

        Args:
            url: Store URL (may have trailing slash, path, etc.)

        Returns:
            Normalized base URL (https://domain).
        """
        # Remove trailing slash
        url = url.rstrip("/")

        # Remove any path components
        if "://" in url:
            parts = url.split("/")
            if len(parts) >= 3:
                return f"{parts[0]}//{parts[2]}"

        return url

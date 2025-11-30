"""Sync Products For Page Use Case.

Synchronizes product catalog for a Shopify store.
"""

from dataclasses import dataclass

from ..domain.entities import Product
from ..domain.errors import EntityNotFoundError
from ..ports import (
    PageRepository,
    ProductRepository,
    ProductExtractorPort,
    LoggingPort,
)


@dataclass(frozen=True)
class SyncProductsResult:
    """Result of the sync products use case.

    Attributes:
        page_id: The page identifier.
        products_synced: Number of products synced.
        products_extracted: Number of products extracted from source.
        is_shopify: Whether the page is a Shopify store.
        source: Source of product data (e.g., "products.json").
        error: Error message if partial failure occurred.
    """

    page_id: str
    products_synced: int
    products_extracted: int
    is_shopify: bool
    source: str | None = None
    error: str | None = None


class SyncProductsForPageUseCase:
    """Use case for synchronizing products for a page.

    This use case:
    1. Verifies the page exists and is a Shopify store
    2. Extracts products from the store's catalog
    3. Upserts products to the database
    4. Returns sync statistics
    """

    def __init__(
        self,
        page_repository: PageRepository,
        product_repository: ProductRepository,
        product_extractor: ProductExtractorPort,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case.

        Args:
            page_repository: Repository for page data.
            product_repository: Repository for product data.
            product_extractor: Port for extracting products from stores.
            logger: Logger for structured logging.
        """
        self._page_repo = page_repository
        self._product_repo = product_repository
        self._product_extractor = product_extractor
        self._logger = logger

    async def execute(self, page_id: str) -> SyncProductsResult:
        """Synchronize products for a page.

        Args:
            page_id: The page identifier to sync products for.

        Returns:
            SyncProductsResult with sync statistics.

        Raises:
            EntityNotFoundError: If the page does not exist.
        """
        self._logger.info(
            "Starting product sync",
            page_id=page_id,
        )

        # 1. Get the page
        page = await self._page_repo.get(page_id)
        if page is None:
            self._logger.error(
                "Page not found",
                page_id=page_id,
            )
            raise EntityNotFoundError("Page", page_id)

        # 2. Check if it's a Shopify store
        if not page.is_shopify:
            self._logger.info(
                "Page is not a Shopify store, skipping sync",
                page_id=page_id,
                domain=page.domain,
            )
            return SyncProductsResult(
                page_id=page_id,
                products_synced=0,
                products_extracted=0,
                is_shopify=False,
                error="Page is not a Shopify store",
            )

        # 3. Check if product extraction is supported
        store_url = page.url.value
        is_supported = await self._product_extractor.is_supported(store_url)
        if not is_supported:
            self._logger.warning(
                "Product extraction not supported for store",
                page_id=page_id,
                store_url=store_url,
            )
            return SyncProductsResult(
                page_id=page_id,
                products_synced=0,
                products_extracted=0,
                is_shopify=True,
                error="Product extraction not supported (products.json not accessible)",
            )

        # 4. Extract products from the store
        extraction_result = await self._product_extractor.extract_products(
            page_id=page_id,
            store_url=store_url,
        )

        products_extracted = len(extraction_result.products)
        self._logger.info(
            "Products extracted",
            page_id=page_id,
            products_extracted=products_extracted,
            source=extraction_result.source,
        )

        if products_extracted == 0:
            return SyncProductsResult(
                page_id=page_id,
                products_synced=0,
                products_extracted=0,
                is_shopify=True,
                source=extraction_result.source,
                error=extraction_result.error or "No products found",
            )

        # 5. Upsert products to database
        await self._product_repo.upsert_many(extraction_result.products)

        self._logger.info(
            "Product sync completed",
            page_id=page_id,
            products_synced=products_extracted,
            source=extraction_result.source,
        )

        return SyncProductsResult(
            page_id=page_id,
            products_synced=products_extracted,
            products_extracted=products_extracted,
            is_shopify=True,
            source=extraction_result.source,
            error=extraction_result.error,
        )

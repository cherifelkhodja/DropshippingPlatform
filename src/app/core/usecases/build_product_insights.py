"""Build Product Insights Use Case.

Computes product insights by matching products with ads for a given page.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..domain.entities.product import Product
from ..domain.entities.product_insights import (
    ProductInsights,
    PageProductInsights,
    AdMatch,
)
from ..domain.services.product_ad_matcher import (
    MatchConfig,
    match_product_to_ads,
)
from ..domain.errors import EntityNotFoundError
from ..ports.repository_port import (
    PageRepository,
    ProductRepository,
    AdsRepository,
)
from ..ports.logging_port import LoggingPort


@dataclass(frozen=True)
class BuildProductInsightsResult:
    """Result of building product insights.

    Attributes:
        page_id: The page identifier.
        insights: The computed PageProductInsights.
        products_analyzed: Number of products analyzed.
        ads_analyzed: Number of ads analyzed.
        matches_found: Total number of product-ad matches found.
        error: Error message if any.
    """

    page_id: str
    insights: PageProductInsights
    products_analyzed: int = 0
    ads_analyzed: int = 0
    matches_found: int = 0
    error: Optional[str] = None


class BuildProductInsightsForPageUseCase:
    """Use case for building product insights for a page.

    This use case:
    1. Fetches all products for a page
    2. Fetches all ads for the same page
    3. Matches products to ads using heuristics
    4. Returns aggregated insights

    The insights are computed on-the-fly and not persisted.
    """

    def __init__(
        self,
        page_repository: PageRepository,
        product_repository: ProductRepository,
        ads_repository: AdsRepository,
        logger: LoggingPort,
        match_config: Optional[MatchConfig] = None,
    ) -> None:
        """Initialize the use case.

        Args:
            page_repository: Repository for page entities.
            product_repository: Repository for product entities.
            ads_repository: Repository for ad entities.
            logger: Logging port for observability.
            match_config: Optional configuration for matching behavior.
        """
        self._page_repo = page_repository
        self._product_repo = product_repository
        self._ads_repo = ads_repository
        self._logger = logger
        self._match_config = match_config or MatchConfig()

    async def execute(
        self,
        page_id: str,
        max_products: int = 500,
    ) -> BuildProductInsightsResult:
        """Build product insights for a page.

        Args:
            page_id: The page identifier to build insights for.
            max_products: Maximum number of products to analyze.

        Returns:
            BuildProductInsightsResult with computed insights.

        Raises:
            EntityNotFoundError: If the page is not found.
        """
        self._logger.info(
            "Building product insights",
            page_id=page_id,
            max_products=max_products,
        )

        # Verify page exists
        page = await self._page_repo.get(page_id)
        if page is None:
            raise EntityNotFoundError("Page not found", page_id)

        # Get products for the page
        products = await self._product_repo.list_by_page(
            page_id,
            limit=max_products,
            offset=0,
        )

        if not products:
            self._logger.info(
                "No products found for page",
                page_id=page_id,
            )
            return BuildProductInsightsResult(
                page_id=page_id,
                insights=PageProductInsights(
                    page_id=page_id,
                    product_insights=[],
                    total_products=0,
                    total_ads=0,
                    computed_at=datetime.utcnow(),
                ),
                products_analyzed=0,
                ads_analyzed=0,
                matches_found=0,
                error="No products found for this page",
            )

        # Get ads for the page
        ads = await self._ads_repo.list_by_page(page_id)

        if not ads:
            self._logger.info(
                "No ads found for page",
                page_id=page_id,
                products_count=len(products),
            )
            # Return insights with products but no matches
            product_insights = [
                ProductInsights(
                    product=product,
                    matched_ads=[],
                    total_ads_analyzed=0,
                    computed_at=datetime.utcnow(),
                )
                for product in products
            ]
            return BuildProductInsightsResult(
                page_id=page_id,
                insights=PageProductInsights(
                    page_id=page_id,
                    product_insights=product_insights,
                    total_products=len(products),
                    total_ads=0,
                    computed_at=datetime.utcnow(),
                ),
                products_analyzed=len(products),
                ads_analyzed=0,
                matches_found=0,
                error="No ads found for this page",
            )

        self._logger.info(
            "Matching products to ads",
            page_id=page_id,
            products_count=len(products),
            ads_count=len(ads),
        )

        # Build insights for each product
        product_insights: list[ProductInsights] = []
        total_matches = 0

        for product in products:
            matches = match_product_to_ads(product, ads, self._match_config)
            total_matches += len(matches)

            insight = ProductInsights(
                product=product,
                matched_ads=matches,
                total_ads_analyzed=len(ads),
                computed_at=datetime.utcnow(),
            )
            product_insights.append(insight)

        # Build page-level insights
        page_insights = PageProductInsights(
            page_id=page_id,
            product_insights=product_insights,
            total_products=len(products),
            total_ads=len(ads),
            computed_at=datetime.utcnow(),
        )

        self._logger.info(
            "Product insights built",
            page_id=page_id,
            products_analyzed=len(products),
            ads_analyzed=len(ads),
            matches_found=total_matches,
            products_with_ads=page_insights.products_with_ads,
            promoted_count=page_insights.promoted_products_count,
        )

        return BuildProductInsightsResult(
            page_id=page_id,
            insights=page_insights,
            products_analyzed=len(products),
            ads_analyzed=len(ads),
            matches_found=total_matches,
        )

    async def execute_for_product(
        self,
        page_id: str,
        product_id: str,
    ) -> ProductInsights:
        """Build insights for a single product.

        Args:
            page_id: The page identifier.
            product_id: The product identifier.

        Returns:
            ProductInsights for the specified product.

        Raises:
            EntityNotFoundError: If page or product is not found.
        """
        self._logger.info(
            "Building insights for single product",
            page_id=page_id,
            product_id=product_id,
        )

        # Verify page exists
        page = await self._page_repo.get(page_id)
        if page is None:
            raise EntityNotFoundError("Page not found", page_id)

        # Get the product
        product = await self._product_repo.get_by_id(product_id)
        if product is None:
            raise EntityNotFoundError("Product not found", product_id)

        # Verify product belongs to page
        if product.page_id != page_id:
            raise EntityNotFoundError("Product not found for this page", product_id)

        # Get ads for the page
        ads = await self._ads_repo.list_by_page(page_id)

        # Match product to ads
        matches = match_product_to_ads(product, ads, self._match_config)

        self._logger.info(
            "Single product insights built",
            page_id=page_id,
            product_id=product_id,
            matches_found=len(matches),
        )

        return ProductInsights(
            product=product,
            matched_ads=matches,
            total_ads_analyzed=len(ads),
            computed_at=datetime.utcnow(),
        )

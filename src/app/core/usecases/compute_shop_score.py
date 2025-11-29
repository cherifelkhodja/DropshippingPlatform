"""Compute Shop Score Use Case.

Calculates a comprehensive shop score based on multiple factors:
- Ads activity (Meta ads)
- Shopify signals (store characteristics)
- Creative quality (ad content analysis)
- Catalog size (product count)
"""

import re
from dataclasses import dataclass
from uuid import uuid4

from ..domain.entities import Ad, Page, ShopScore
from ..domain.errors import EntityNotFoundError
from ..ports import AdsRepository, LoggingPort, PageRepository, ScoringRepository


# Constants for scoring weights
WEIGHT_ADS_ACTIVITY = 0.4
WEIGHT_SHOPIFY = 0.3
WEIGHT_CREATIVE_QUALITY = 0.2
WEIGHT_CATALOG = 0.1

# Strong currencies that indicate premium markets
STRONG_CURRENCIES = frozenset({"EUR", "USD", "GBP", "AUD"})

# CTA patterns for creative quality scoring
CTA_PATTERNS = frozenset(
    {"buy now", "shop now", "order now", "shop", "get yours", "grab yours"}
)


@dataclass(frozen=True)
class ComputeShopScoreResult:
    """Result of the compute shop score use case.

    Attributes:
        shop_score: The computed ShopScore entity.
        page_id: The page identifier.
        global_score: The final score (0-100).
        components: Dictionary of component sub-scores.
    """

    shop_score: ShopScore
    page_id: str
    global_score: float
    components: dict[str, float]


def _clamp(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def _calc_ads_activity_score(ads: list[Ad]) -> float:
    """Calculate the ads activity score component.

    Based on:
    - Number of ads (normalized to 50 as reference)
    - Country diversity (normalized to 5 countries)
    - Platform diversity (normalized to 3 platforms)

    Args:
        ads: List of Ad entities for the page.

    Returns:
        Score from 0 to 100.
    """
    if not ads:
        return 0.0

    ads_count = len(ads)

    # Collect unique countries and platforms across all ads
    all_countries: set[str] = set()
    all_platforms: set[str] = set()

    for ad in ads:
        for country in ad.countries:
            all_countries.add(country.code)
        for platform in ad.platforms:
            all_platforms.add(platform.value)

    # Normalize components (capped at 1.0)
    normalized_ads_count = min(ads_count / 50.0, 1.0)
    country_diversity = min(len(all_countries) / 5.0, 1.0)
    platform_diversity = min(len(all_platforms) / 3.0, 1.0)

    # Weighted combination
    ads_activity_raw = (
        0.6 * normalized_ads_count + 0.2 * country_diversity + 0.2 * platform_diversity
    )

    return _clamp(ads_activity_raw * 100.0)


def _calc_shopify_score(page: Page) -> float:
    """Calculate the Shopify signals score component.

    Based on:
    - Confirmed Shopify store (+30 points)
    - Strong currency (+20 points)
    - Has active ads (+20 points)
    - High total ads count (+10 points)
    - Base score (20 points)

    Args:
        page: The Page entity.

    Returns:
        Score from 0 to 100.
    """
    score = 20.0  # Base score

    # Confirmed Shopify store
    if page.is_shopify:
        score += 30.0

    # Strong currency
    if page.currency and page.currency.code in STRONG_CURRENCIES:
        score += 20.0

    # Has active ads (indicates active marketing)
    if page.active_ads_count > 0:
        score += 20.0

    # High total ads count (indicates established advertiser)
    if page.total_ads_count >= 10:
        score += 10.0

    return _clamp(score)


def _calc_creative_quality_score(ads: list[Ad]) -> float:
    """Calculate the creative quality score component.

    Based on analysis of ad text content:
    - Presence of percentage/discount indicators (+20 points)
    - Presence of emojis (+15 points)
    - Presence of CTA phrases (+25 points)
    - Has title and body text (+20 points)
    - Has CTA type defined (+20 points)

    Args:
        ads: List of Ad entities.

    Returns:
        Score from 0 to 100.
    """
    if not ads:
        return 0.0

    # Aggregate indicators across all ads
    has_percentage = False
    has_emoji = False
    has_cta_phrase = False
    has_text_content = False
    has_cta_type = False

    # Emoji pattern (common emoji unicode ranges)
    emoji_pattern = re.compile(
        r"[\U0001F300-\U0001F9FF"  # Miscellaneous Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F"  # Chess Symbols
        r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\U00002702-\U000027B0"  # Dingbats
        r"\U0001F600-\U0001F64F"  # Emoticons
        r"]"
    )

    for ad in ads:
        # Combine title and body for analysis
        text = ""
        if ad.title:
            text += ad.title.lower() + " "
        if ad.body:
            text += ad.body.lower()

        if text.strip():
            has_text_content = True

            # Check for percentage/discount
            if "%" in text or "off" in text or "sale" in text:
                has_percentage = True

            # Check for emojis
            if emoji_pattern.search(text):
                has_emoji = True

            # Check for CTA phrases
            for cta in CTA_PATTERNS:
                if cta in text:
                    has_cta_phrase = True
                    break

        # Check CTA type
        if ad.cta_type and ad.cta_type.strip():
            has_cta_type = True

    # Calculate score based on indicators
    score = 0.0
    if has_text_content:
        score += 20.0
    if has_percentage:
        score += 20.0
    if has_emoji:
        score += 15.0
    if has_cta_phrase:
        score += 25.0
    if has_cta_type:
        score += 20.0

    return _clamp(score)


def _calc_catalog_score(page: Page) -> float:
    """Calculate the catalog size score component.

    Based on product count, normalized to 200 products as reference.

    Args:
        page: The Page entity.

    Returns:
        Score from 0 to 100.
    """
    product_count = page.product_count.value

    if product_count <= 0:
        return 0.0

    # Normalize to 200 products (capped at 1.0)
    normalized = min(product_count / 200.0, 1.0)

    return _clamp(normalized * 100.0)


class ComputeShopScoreUseCase:
    """Use case for computing a comprehensive shop score.

    This use case:
    1. Retrieves page data and ads from repositories
    2. Calculates component sub-scores:
       - Ads Activity (40%): based on ads count, country/platform diversity
       - Shopify Score (30%): based on store characteristics
       - Creative Quality (20%): based on ad content analysis
       - Catalog Score (10%): based on product count
    3. Computes weighted global score (0-100)
    4. Creates and persists a ShopScore entity
    """

    def __init__(
        self,
        page_repository: PageRepository,
        ads_repository: AdsRepository,
        scoring_repository: ScoringRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case with required dependencies.

        Args:
            page_repository: Repository for Page entities.
            ads_repository: Repository for Ad entities.
            scoring_repository: Repository for ShopScore entities.
            logger: Logging port for structured logging.
        """
        self._page_repo = page_repository
        self._ads_repo = ads_repository
        self._scoring_repo = scoring_repository
        self._logger = logger

    async def execute(self, page_id: str) -> ComputeShopScoreResult:
        """Execute the compute shop score use case.

        Args:
            page_id: The unique page identifier.

        Returns:
            ComputeShopScoreResult with the computed score and components.

        Raises:
            EntityNotFoundError: If the page does not exist.
        """
        self._logger.info("Computing shop score", page_id=page_id)

        # 1. Retrieve page data
        page = await self._page_repo.get(page_id)
        if page is None:
            self._logger.error("Page not found for scoring", page_id=page_id)
            raise EntityNotFoundError("Page", page_id)

        # 2. Retrieve ads for the page
        ads = await self._ads_repo.list_by_page(page_id)

        self._logger.debug(
            "Retrieved data for scoring",
            page_id=page_id,
            ads_count=len(ads),
            product_count=page.product_count.value,
            is_shopify=page.is_shopify,
        )

        # 3. Calculate component scores
        ads_activity_score = _calc_ads_activity_score(ads)
        shopify_score = _calc_shopify_score(page)
        creative_quality_score = _calc_creative_quality_score(ads)
        catalog_score = _calc_catalog_score(page)

        # 4. Compute weighted global score
        global_score_raw = (
            WEIGHT_ADS_ACTIVITY * ads_activity_score
            + WEIGHT_SHOPIFY * shopify_score
            + WEIGHT_CREATIVE_QUALITY * creative_quality_score
            + WEIGHT_CATALOG * catalog_score
        )

        # Clamp and round to 2 decimal places
        global_score = round(_clamp(global_score_raw), 2)

        # 5. Build components dictionary
        components = {
            "ads_activity": round(ads_activity_score, 2),
            "shopify": round(shopify_score, 2),
            "creative_quality": round(creative_quality_score, 2),
            "catalog": round(catalog_score, 2),
        }

        # 6. Create ShopScore entity
        shop_score = ShopScore.create(
            id=str(uuid4()),
            page_id=page_id,
            score=global_score,
            components=components,
        )

        # 7. Persist the score
        await self._scoring_repo.save(shop_score)

        self._logger.info(
            "Shop score computed successfully",
            page_id=page_id,
            global_score=global_score,
            ads_activity=components["ads_activity"],
            shopify=components["shopify"],
            creative_quality=components["creative_quality"],
            catalog=components["catalog"],
        )

        return ComputeShopScoreResult(
            shop_score=shop_score,
            page_id=page_id,
            global_score=global_score,
            components=components,
        )

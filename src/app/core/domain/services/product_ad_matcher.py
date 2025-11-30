"""Product-Ad Matching Service.

Domain service for matching products to ads using various heuristics.
"""

import re
from dataclasses import dataclass
from typing import Optional
from difflib import SequenceMatcher

from ..entities.product import Product
from ..entities.ad import Ad
from ..entities.product_insights import AdMatch, MatchStrength
from ..config import (
    STRONG_MATCH_THRESHOLD,
    MEDIUM_MATCH_THRESHOLD,
    WEAK_MATCH_THRESHOLD,
    TEXT_SIMILARITY_THRESHOLD,
    DEFAULT_URL_MATCH_WEIGHT,
    DEFAULT_HANDLE_MATCH_WEIGHT,
    DEFAULT_TEXT_SIMILARITY_WEIGHT,
)


@dataclass(frozen=True)
class MatchConfig:
    """Configuration for matching behavior.

    Attributes:
        url_match_weight: Weight for URL-based matches (0-1).
        handle_match_weight: Weight for handle-based matches (0-1).
        text_similarity_weight: Weight for text similarity matches (0-1).
        text_similarity_threshold: Minimum similarity for text matching.
        min_score_threshold: Minimum score to consider a match valid.
    """

    url_match_weight: float = DEFAULT_URL_MATCH_WEIGHT
    handle_match_weight: float = DEFAULT_HANDLE_MATCH_WEIGHT
    text_similarity_weight: float = DEFAULT_TEXT_SIMILARITY_WEIGHT
    text_similarity_threshold: float = TEXT_SIMILARITY_THRESHOLD
    min_score_threshold: float = WEAK_MATCH_THRESHOLD


def normalize_text(text: str) -> str:
    """Normalize text for comparison.

    Converts to lowercase, removes extra whitespace, and strips punctuation.

    Args:
        text: Text to normalize.

    Returns:
        Normalized text.
    """
    if not text:
        return ""
    # Convert to lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove special characters but keep spaces
    text = re.sub(r"[^\w\s]", " ", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def extract_handle_from_url(url: str) -> Optional[str]:
    """Extract product handle from a URL.

    Shopify URLs typically follow the pattern:
    https://store.com/products/product-handle

    Args:
        url: URL to extract handle from.

    Returns:
        Extracted handle or None if not found.
    """
    if not url:
        return None

    # Match /products/handle pattern
    match = re.search(r"/products/([^/?#]+)", url, re.IGNORECASE)
    if match:
        return match.group(1).lower()

    # Try to extract last path segment as fallback
    match = re.search(r"/([^/?#]+)/?(?:\?|#|$)", url)
    if match:
        return match.group(1).lower()

    return None


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two text strings.

    Uses SequenceMatcher for fuzzy string matching.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Similarity score from 0.0 to 1.0.
    """
    if not text1 or not text2:
        return 0.0

    # Normalize texts
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)

    if not norm1 or not norm2:
        return 0.0

    # Use SequenceMatcher for similarity
    return SequenceMatcher(None, norm1, norm2).ratio()


def check_url_match(product: Product, ad: Ad) -> tuple[bool, float, str]:
    """Check if product URL matches ad link URL (strong match).

    Args:
        product: Product to check.
        ad: Ad to check against.

    Returns:
        Tuple of (is_match, score, reason).
    """
    if not ad.link_url:
        return False, 0.0, ""

    ad_url = str(ad.link_url).lower()
    product_url = product.url.lower()
    product_handle = product.handle.lower()

    # Direct URL match
    if product_url in ad_url or ad_url in product_url:
        return True, 1.0, "URL direct match"

    # Handle in ad URL
    if product_handle and product_handle in ad_url:
        # Check if it's in the products path
        if f"/products/{product_handle}" in ad_url:
            return True, 1.0, "Product handle in ad URL path"
        # Handle appears in URL but not in standard path
        return True, 0.9, "Product handle found in ad URL"

    # Extract handle from ad URL and compare
    ad_handle = extract_handle_from_url(ad_url)
    if ad_handle and ad_handle == product_handle:
        return True, 0.95, "URL handles match"

    return False, 0.0, ""


def check_handle_match(product: Product, ad: Ad) -> tuple[bool, float, str]:
    """Check if product handle appears in ad text (medium match).

    Args:
        product: Product to check.
        ad: Ad to check against.

    Returns:
        Tuple of (is_match, score, reason).
    """
    product_handle = product.handle.lower()
    if not product_handle:
        return False, 0.0, ""

    # Combine ad text fields
    ad_text_parts = []
    if ad.title:
        ad_text_parts.append(ad.title.lower())
    if ad.body:
        ad_text_parts.append(ad.body.lower())

    ad_text = " ".join(ad_text_parts)
    if not ad_text:
        return False, 0.0, ""

    # Check for handle (with word boundaries for better matching)
    # Handle might be hyphenated like "awesome-t-shirt"
    handle_parts = product_handle.replace("-", " ").split()

    # Exact handle match in text
    if product_handle in ad_text:
        return True, 0.8, "Product handle in ad text"

    # Check if handle words appear together
    if len(handle_parts) > 1:
        # All handle parts must appear in order
        pattern = r"\b" + r"\s+".join(re.escape(part) for part in handle_parts) + r"\b"
        if re.search(pattern, ad_text):
            return True, 0.75, "Product handle words in ad text"

    # Check if handle appears as separate words
    handle_no_hyphen = product_handle.replace("-", " ")
    if handle_no_hyphen in ad_text:
        return True, 0.7, "Product handle (no hyphens) in ad text"

    return False, 0.0, ""


def check_text_similarity(
    product: Product,
    ad: Ad,
    threshold: float = TEXT_SIMILARITY_THRESHOLD,
) -> tuple[bool, float, str]:
    """Check text similarity between product and ad (weak match).

    Args:
        product: Product to check.
        ad: Ad to check against.
        threshold: Minimum similarity threshold.

    Returns:
        Tuple of (is_match, score, reason).
    """
    product_title = product.title or ""

    # Combine ad text
    ad_texts = []
    if ad.title:
        ad_texts.append(ad.title)
    if ad.body:
        ad_texts.append(ad.body)

    if not product_title or not ad_texts:
        return False, 0.0, ""

    # Calculate similarity against each ad text field
    best_similarity = 0.0
    best_field = ""

    for i, ad_text in enumerate(ad_texts):
        similarity = calculate_text_similarity(product_title, ad_text)
        if similarity > best_similarity:
            best_similarity = similarity
            best_field = "title" if i == 0 else "body"

    if best_similarity >= threshold:
        score = best_similarity * 0.5  # Scale down since it's a weak match
        return True, score, f"Text similarity ({best_similarity:.0%}) in ad {best_field}"

    return False, 0.0, ""


def match_product_to_ad(
    product: Product,
    ad: Ad,
    config: Optional[MatchConfig] = None,
) -> Optional[AdMatch]:
    """Match a product to an ad using all heuristics.

    Args:
        product: Product to match.
        ad: Ad to match against.
        config: Optional matching configuration.

    Returns:
        AdMatch if a match is found, None otherwise.
    """
    config = config or MatchConfig()

    reasons: list[str] = []
    total_score = 0.0
    strength = MatchStrength.NONE

    # 1. URL match (strong)
    url_match, url_score, url_reason = check_url_match(product, ad)
    if url_match:
        total_score = max(total_score, url_score * config.url_match_weight)
        reasons.append(url_reason)
        strength = MatchStrength.STRONG

    # 2. Handle match (medium)
    handle_match, handle_score, handle_reason = check_handle_match(product, ad)
    if handle_match:
        weighted_score = handle_score * config.handle_match_weight
        if weighted_score > total_score:
            total_score = weighted_score
        if strength == MatchStrength.NONE:
            strength = MatchStrength.MEDIUM
        reasons.append(handle_reason)

    # 3. Text similarity (weak)
    text_match, text_score, text_reason = check_text_similarity(
        product, ad, config.text_similarity_threshold
    )
    if text_match:
        weighted_score = text_score * config.text_similarity_weight
        if weighted_score > total_score:
            total_score = weighted_score
        if strength == MatchStrength.NONE:
            strength = MatchStrength.WEAK
        reasons.append(text_reason)

    # Check if we have a valid match
    if total_score < config.min_score_threshold or strength == MatchStrength.NONE:
        return None

    return AdMatch(
        ad=ad,
        score=min(total_score, 1.0),  # Cap at 1.0
        strength=strength,
        reasons=reasons,
    )


def match_product_to_ads(
    product: Product,
    ads: list[Ad],
    config: Optional[MatchConfig] = None,
) -> list[AdMatch]:
    """Match a product against a list of ads.

    Args:
        product: Product to match.
        ads: List of ads to match against.
        config: Optional matching configuration.

    Returns:
        List of AdMatch objects for all matching ads, sorted by score descending.
    """
    matches: list[AdMatch] = []

    for ad in ads:
        match = match_product_to_ad(product, ad, config)
        if match:
            matches.append(match)

    # Sort by score descending
    matches.sort(key=lambda m: m.score, reverse=True)
    return matches

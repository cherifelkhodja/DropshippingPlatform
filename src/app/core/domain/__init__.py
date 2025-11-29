"""Domain Layer for the Dropshipping Platform.

This module contains the core business logic, including:
- Entities: Objects with identity (Page, Ad, ShopifyProfile, Scan, KeywordRun)
- Value Objects: Immutable objects without identity (Url, Country, etc.)
- Domain Errors: Business rule violation exceptions

The domain layer has no dependencies on external frameworks or infrastructure.
"""

from .entities import (
    Page,
    Ad,
    AdStatus,
    AdPlatform,
    ShopifyProfile,
    ShopifyTheme,
    ShopifyApp,
    Scan,
    ScanType,
    ScanStatus,
    ScanResult,
    KeywordRun,
    KeywordRunStatus,
    KeywordRunResult,
    ShopScore,
    Watchlist,
    WatchlistItem,
)

from .value_objects import (
    Url,
    Country,
    Language,
    Currency,
    PaymentMethod,
    PaymentMethods,
    ProductCount,
    Category,
    PageState,
    PageStatus,
    ScanId,
)

from .errors import (
    # Base error
    DomainError,
    # Validation errors
    InvalidUrlError,
    InvalidCountryError,
    InvalidLanguageError,
    InvalidCurrencyError,
    InvalidProductCountError,
    InvalidPageStateError,
    InvalidCategoryError,
    InvalidScanIdError,
    InvalidPaymentMethodError,
    # Entity errors
    EntityNotFoundError,
    DuplicateEntityError,
    # Scraping errors
    ScrapingError,
    ScrapingTimeoutError,
    ScrapingBlockedError,
    # Sitemap errors
    SitemapNotFoundError,
    SitemapParsingError,
    # Repository errors
    RepositoryError,
    # Task errors
    TaskDispatchError,
    # Meta Ads API errors
    MetaAdsApiError,
    MetaAdsRateLimitError,
    MetaAdsAuthenticationError,
)

__all__ = [
    # Entities
    "Page",
    "Ad",
    "AdStatus",
    "AdPlatform",
    "ShopifyProfile",
    "ShopifyTheme",
    "ShopifyApp",
    "Scan",
    "ScanType",
    "ScanStatus",
    "ScanResult",
    "KeywordRun",
    "KeywordRunStatus",
    "KeywordRunResult",
    "ShopScore",
    "Watchlist",
    "WatchlistItem",
    # Value Objects
    "Url",
    "Country",
    "Language",
    "Currency",
    "PaymentMethod",
    "PaymentMethods",
    "ProductCount",
    "Category",
    "PageState",
    "PageStatus",
    "ScanId",
    # Errors - Base
    "DomainError",
    # Errors - Validation
    "InvalidUrlError",
    "InvalidCountryError",
    "InvalidLanguageError",
    "InvalidCurrencyError",
    "InvalidProductCountError",
    "InvalidPageStateError",
    "InvalidCategoryError",
    "InvalidScanIdError",
    "InvalidPaymentMethodError",
    # Errors - Entity
    "EntityNotFoundError",
    "DuplicateEntityError",
    # Errors - Scraping
    "ScrapingError",
    "ScrapingTimeoutError",
    "ScrapingBlockedError",
    # Errors - Sitemap
    "SitemapNotFoundError",
    "SitemapParsingError",
    # Errors - Repository
    "RepositoryError",
    # Errors - Task
    "TaskDispatchError",
    # Errors - Meta Ads API
    "MetaAdsApiError",
    "MetaAdsRateLimitError",
    "MetaAdsAuthenticationError",
]

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
    DomainError,
    InvalidUrlError,
    InvalidCountryError,
    InvalidLanguageError,
    InvalidCurrencyError,
    InvalidProductCountError,
    InvalidPageStateError,
    InvalidCategoryError,
    InvalidScanIdError,
    InvalidPaymentMethodError,
    EntityNotFoundError,
    DuplicateEntityError,
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
    # Errors
    "DomainError",
    "InvalidUrlError",
    "InvalidCountryError",
    "InvalidLanguageError",
    "InvalidCurrencyError",
    "InvalidProductCountError",
    "InvalidPageStateError",
    "InvalidCategoryError",
    "InvalidScanIdError",
    "InvalidPaymentMethodError",
    "EntityNotFoundError",
    "DuplicateEntityError",
]

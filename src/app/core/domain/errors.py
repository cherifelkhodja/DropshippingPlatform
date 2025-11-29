"""Domain errors for the Dropshipping Platform.

All business-related exceptions are defined here.
These errors represent domain rule violations and invalid states.
"""

from typing import Any


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(self, message: str, value: Any = None) -> None:
        self.message = message
        self.value = value
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.value is not None:
            return f"{self.message}: {self.value!r}"
        return self.message


class InvalidUrlError(DomainError):
    """Raised when a URL is invalid or malformed."""

    def __init__(self, url: str, reason: str = "Invalid URL format") -> None:
        super().__init__(message=reason, value=url)


class InvalidCountryError(DomainError):
    """Raised when a country code is invalid."""

    def __init__(self, country_code: str) -> None:
        super().__init__(
            message="Invalid ISO 3166-1 alpha-2 country code",
            value=country_code
        )


class InvalidLanguageError(DomainError):
    """Raised when a language code is invalid."""

    def __init__(self, language_code: str) -> None:
        super().__init__(
            message="Invalid ISO 639-1 language code",
            value=language_code
        )


class InvalidCurrencyError(DomainError):
    """Raised when a currency code is invalid."""

    def __init__(self, currency_code: str) -> None:
        super().__init__(
            message="Invalid ISO 4217 currency code",
            value=currency_code
        )


class InvalidProductCountError(DomainError):
    """Raised when a product count is invalid (negative or unreasonable)."""

    def __init__(self, count: int, reason: str = "Product count must be non-negative") -> None:
        super().__init__(message=reason, value=count)


class InvalidPageStateError(DomainError):
    """Raised when a page state transition is invalid."""

    def __init__(self, state: str) -> None:
        super().__init__(
            message="Invalid page state",
            value=state
        )


class InvalidCategoryError(DomainError):
    """Raised when a category is invalid or empty."""

    def __init__(self, category: str, reason: str = "Invalid category") -> None:
        super().__init__(message=reason, value=category)


class InvalidScanIdError(DomainError):
    """Raised when a scan ID format is invalid."""

    def __init__(self, scan_id: str) -> None:
        super().__init__(
            message="Invalid scan ID format (expected UUID)",
            value=scan_id
        )


class InvalidPaymentMethodError(DomainError):
    """Raised when a payment method is invalid."""

    def __init__(self, method: str) -> None:
        super().__init__(
            message="Invalid payment method",
            value=method
        )


class EntityNotFoundError(DomainError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            message=f"{entity_type} not found",
            value=entity_id
        )


class DuplicateEntityError(DomainError):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        super().__init__(
            message=f"{entity_type} already exists",
            value=entity_id
        )


# =============================================================================
# Infrastructure/Port-related Errors
# These errors are raised by adapter implementations but defined in domain
# to maintain the dependency direction (adapters depend on domain).
# =============================================================================


class ScrapingError(DomainError):
    """Base error for scraping operations."""

    def __init__(self, url: str, reason: str = "Scraping failed") -> None:
        super().__init__(message=reason, value=url)


class ScrapingTimeoutError(ScrapingError):
    """Raised when a scraping request times out."""

    def __init__(self, url: str, timeout_seconds: int) -> None:
        super().__init__(
            url=url,
            reason=f"Request timed out after {timeout_seconds} seconds"
        )


class ScrapingBlockedError(ScrapingError):
    """Raised when scraping is blocked (403, captcha, etc.)."""

    def __init__(self, url: str, status_code: int | None = None) -> None:
        reason = "Request blocked"
        if status_code:
            reason = f"Request blocked with status {status_code}"
        super().__init__(url=url, reason=reason)


class SitemapNotFoundError(DomainError):
    """Raised when no sitemap is found for a website."""

    def __init__(self, website: str) -> None:
        super().__init__(
            message="No sitemap found for website",
            value=website
        )


class SitemapParsingError(DomainError):
    """Raised when a sitemap cannot be parsed."""

    def __init__(self, sitemap_url: str, reason: str = "Failed to parse sitemap") -> None:
        super().__init__(message=reason, value=sitemap_url)


class RepositoryError(DomainError):
    """Base error for repository operations."""

    def __init__(self, operation: str, reason: str = "Database operation failed") -> None:
        super().__init__(message=reason, value=operation)


class TaskDispatchError(DomainError):
    """Raised when a task cannot be dispatched."""

    def __init__(self, task_name: str, reason: str = "Failed to dispatch task") -> None:
        super().__init__(message=reason, value=task_name)


class MetaAdsApiError(DomainError):
    """Base error for Meta Ads API operations."""

    def __init__(self, reason: str = "Meta Ads API error") -> None:
        super().__init__(message=reason)


class MetaAdsRateLimitError(MetaAdsApiError):
    """Raised when Meta Ads API rate limit is exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        reason = "Rate limit exceeded"
        if retry_after:
            reason = f"Rate limit exceeded, retry after {retry_after} seconds"
        super().__init__(reason=reason)


class MetaAdsAuthenticationError(MetaAdsApiError):
    """Raised when Meta Ads API authentication fails."""

    def __init__(self) -> None:
        super().__init__(reason="Authentication failed")

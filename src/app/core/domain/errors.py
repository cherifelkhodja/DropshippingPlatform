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

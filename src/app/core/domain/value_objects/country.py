"""Country Value Object.

Represents a validated ISO 3166-1 alpha-2 country code.
"""

from dataclasses import dataclass

from ..errors import InvalidCountryError


# ISO 3166-1 alpha-2 country codes (subset of most common ones)
VALID_COUNTRY_CODES: frozenset[str] = frozenset({
    # Europe
    "FR", "DE", "GB", "ES", "IT", "PT", "NL", "BE", "CH", "AT",
    "PL", "SE", "NO", "DK", "FI", "IE", "GR", "CZ", "RO", "HU",
    "SK", "BG", "HR", "SI", "LT", "LV", "EE", "LU", "MT", "CY",
    # North America
    "US", "CA", "MX",
    # South America
    "BR", "AR", "CL", "CO", "PE", "VE", "EC", "UY",
    # Asia
    "CN", "JP", "KR", "IN", "ID", "TH", "VN", "MY", "SG", "PH",
    "TW", "HK", "AE", "SA", "IL", "TR",
    # Oceania
    "AU", "NZ",
    # Africa
    "ZA", "EG", "NG", "MA", "KE",
})


@dataclass(frozen=True)
class Country:
    """Immutable country value object with ISO 3166-1 alpha-2 validation.

    Attributes:
        code: The two-letter country code (uppercase).
    """

    code: str

    def __post_init__(self) -> None:
        """Validate country code after initialization."""
        # Normalize to uppercase for comparison
        normalized = self.code.upper() if self.code else ""

        if not normalized:
            raise InvalidCountryError(self.code)

        if len(normalized) != 2:
            raise InvalidCountryError(self.code)

        if normalized not in VALID_COUNTRY_CODES:
            raise InvalidCountryError(self.code)

        # Use object.__setattr__ since dataclass is frozen
        object.__setattr__(self, 'code', normalized)

    def __str__(self) -> str:
        return self.code

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Country):
            return self.code == other.code
        return False

    def __hash__(self) -> int:
        return hash(self.code)

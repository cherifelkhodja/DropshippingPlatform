"""Currency Value Object.

Represents a validated ISO 4217 currency code.
"""

from dataclasses import dataclass

from ..errors import InvalidCurrencyError


# ISO 4217 currency codes (most common ones)
VALID_CURRENCY_CODES: frozenset[str] = frozenset(
    {
        "USD",  # US Dollar
        "EUR",  # Euro
        "GBP",  # British Pound
        "JPY",  # Japanese Yen
        "CNY",  # Chinese Yuan
        "CHF",  # Swiss Franc
        "CAD",  # Canadian Dollar
        "AUD",  # Australian Dollar
        "NZD",  # New Zealand Dollar
        "HKD",  # Hong Kong Dollar
        "SGD",  # Singapore Dollar
        "SEK",  # Swedish Krona
        "NOK",  # Norwegian Krone
        "DKK",  # Danish Krone
        "KRW",  # South Korean Won
        "INR",  # Indian Rupee
        "RUB",  # Russian Ruble
        "BRL",  # Brazilian Real
        "MXN",  # Mexican Peso
        "ZAR",  # South African Rand
        "TRY",  # Turkish Lira
        "PLN",  # Polish Zloty
        "THB",  # Thai Baht
        "IDR",  # Indonesian Rupiah
        "MYR",  # Malaysian Ringgit
        "PHP",  # Philippine Peso
        "CZK",  # Czech Koruna
        "ILS",  # Israeli Shekel
        "AED",  # UAE Dirham
        "SAR",  # Saudi Riyal
        "ARS",  # Argentine Peso
        "CLP",  # Chilean Peso
        "COP",  # Colombian Peso
        "VND",  # Vietnamese Dong
        "TWD",  # Taiwan Dollar
        "HUF",  # Hungarian Forint
        "RON",  # Romanian Leu
    }
)


@dataclass(frozen=True)
class Currency:
    """Immutable currency value object with ISO 4217 validation.

    Attributes:
        code: The three-letter currency code (uppercase).
    """

    code: str

    def __post_init__(self) -> None:
        """Validate currency code after initialization."""
        # Normalize to uppercase for comparison
        normalized = self.code.upper() if self.code else ""

        if not normalized:
            raise InvalidCurrencyError(self.code)

        if len(normalized) != 3:
            raise InvalidCurrencyError(self.code)

        if normalized not in VALID_CURRENCY_CODES:
            raise InvalidCurrencyError(self.code)

        # Use object.__setattr__ since dataclass is frozen
        object.__setattr__(self, "code", normalized)

    @property
    def symbol(self) -> str:
        """Get the currency symbol if available."""
        symbols: dict[str, str] = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CNY": "¥",
            "CHF": "CHF",
            "CAD": "C$",
            "AUD": "A$",
            "INR": "₹",
            "KRW": "₩",
            "BRL": "R$",
            "RUB": "₽",
            "TRY": "₺",
            "PLN": "zł",
            "ILS": "₪",
            "THB": "฿",
        }
        return symbols.get(self.code, self.code)

    def __str__(self) -> str:
        return self.code

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Currency):
            return self.code == other.code
        return False

    def __hash__(self) -> int:
        return hash(self.code)

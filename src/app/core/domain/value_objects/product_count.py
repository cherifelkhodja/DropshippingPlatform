"""Product Count Value Object.

Represents a validated count of products in a shop.
"""

from dataclasses import dataclass

from ..errors import InvalidProductCountError


@dataclass(frozen=True)
class ProductCount:
    """Immutable product count value object with validation.

    Attributes:
        value: The number of products (must be non-negative).
    """

    value: int

    # Maximum reasonable product count for a single shop
    MAX_PRODUCT_COUNT: int = 1_000_000

    def __post_init__(self) -> None:
        """Validate product count after initialization."""
        if not isinstance(self.value, int):
            raise InvalidProductCountError(
                self.value,
                "Product count must be an integer"
            )

        if self.value < 0:
            raise InvalidProductCountError(
                self.value,
                "Product count cannot be negative"
            )

        if self.value > self.MAX_PRODUCT_COUNT:
            raise InvalidProductCountError(
                self.value,
                f"Product count exceeds maximum ({self.MAX_PRODUCT_COUNT})"
            )

    @classmethod
    def zero(cls) -> "ProductCount":
        """Create a ProductCount with value zero."""
        return cls(value=0)

    @classmethod
    def unknown(cls) -> "ProductCount":
        """Create a ProductCount representing unknown (zero)."""
        return cls(value=0)

    def is_empty(self) -> bool:
        """Check if the product count is zero."""
        return self.value == 0

    def is_small_catalog(self, threshold: int = 50) -> bool:
        """Check if this represents a small product catalog."""
        return self.value <= threshold

    def is_large_catalog(self, threshold: int = 1000) -> bool:
        """Check if this represents a large product catalog."""
        return self.value >= threshold

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __add__(self, other: "ProductCount") -> "ProductCount":
        return ProductCount(self.value + other.value)

    def __lt__(self, other: "ProductCount") -> bool:
        return self.value < other.value

    def __le__(self, other: "ProductCount") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "ProductCount") -> bool:
        return self.value > other.value

    def __ge__(self, other: "ProductCount") -> bool:
        return self.value >= other.value

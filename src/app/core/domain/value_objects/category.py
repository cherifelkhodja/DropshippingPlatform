"""Category Value Object.

Represents a validated product or shop category.
"""

from dataclasses import dataclass

from ..errors import InvalidCategoryError


# Predefined categories for dropshipping products
VALID_CATEGORIES: frozenset[str] = frozenset({
    # Fashion & Apparel
    "fashion",
    "clothing",
    "shoes",
    "accessories",
    "jewelry",
    "watches",
    "bags",
    # Beauty & Health
    "beauty",
    "cosmetics",
    "skincare",
    "health",
    "wellness",
    "fitness",
    # Electronics
    "electronics",
    "phones",
    "computers",
    "gadgets",
    "audio",
    "gaming",
    # Home & Garden
    "home",
    "furniture",
    "decor",
    "garden",
    "kitchen",
    "lighting",
    # Sports & Outdoors
    "sports",
    "outdoors",
    "camping",
    "cycling",
    # Kids & Baby
    "kids",
    "baby",
    "toys",
    # Pets
    "pets",
    "pet_supplies",
    # Automotive
    "automotive",
    "car_accessories",
    # Food & Beverages
    "food",
    "beverages",
    # Books & Media
    "books",
    "media",
    # Art & Crafts
    "art",
    "crafts",
    # Office & Business
    "office",
    "business",
    # Other
    "general",
    "other",
    "uncategorized",
})


@dataclass(frozen=True)
class Category:
    """Immutable category value object with validation.

    Attributes:
        value: The category name (lowercase, validated).
    """

    value: str

    def __post_init__(self) -> None:
        """Validate category after initialization."""
        if not self.value:
            raise InvalidCategoryError("", "Category cannot be empty")

        normalized = self.value.lower().strip()

        if len(normalized) < 2:
            raise InvalidCategoryError(
                self.value,
                "Category must be at least 2 characters"
            )

        if len(normalized) > 50:
            raise InvalidCategoryError(
                self.value,
                "Category must not exceed 50 characters"
            )

        # Allow custom categories, but normalize them
        object.__setattr__(self, 'value', normalized)

    @classmethod
    def uncategorized(cls) -> "Category":
        """Create an uncategorized Category."""
        return cls(value="uncategorized")

    def is_predefined(self) -> bool:
        """Check if this is a predefined category."""
        return self.value in VALID_CATEGORIES

    def is_fashion_related(self) -> bool:
        """Check if this category is fashion-related."""
        fashion_categories = {
            "fashion", "clothing", "shoes", "accessories",
            "jewelry", "watches", "bags"
        }
        return self.value in fashion_categories

    def is_electronics_related(self) -> bool:
        """Check if this category is electronics-related."""
        electronics_categories = {
            "electronics", "phones", "computers", "gadgets",
            "audio", "gaming"
        }
        return self.value in electronics_categories

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Category):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

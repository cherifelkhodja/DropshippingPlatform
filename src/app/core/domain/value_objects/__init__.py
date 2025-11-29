"""Value Objects for the Dropshipping Platform domain.

Value objects are immutable objects that represent domain concepts
with no identity. They are compared by their attribute values.
"""

from .url import Url
from .country import Country, VALID_COUNTRY_CODES
from .language import Language, VALID_LANGUAGE_CODES
from .currency import Currency, VALID_CURRENCY_CODES
from .payment_methods import PaymentMethod, PaymentMethods
from .product_count import ProductCount
from .category import Category, VALID_CATEGORIES
from .page_state import PageState, PageStatus, VALID_TRANSITIONS
from .scan_id import ScanId

__all__ = [
    # URL
    "Url",
    # Country
    "Country",
    "VALID_COUNTRY_CODES",
    # Language
    "Language",
    "VALID_LANGUAGE_CODES",
    # Currency
    "Currency",
    "VALID_CURRENCY_CODES",
    # Payment Methods
    "PaymentMethod",
    "PaymentMethods",
    # Product Count
    "ProductCount",
    # Category
    "Category",
    "VALID_CATEGORIES",
    # Page State
    "PageState",
    "PageStatus",
    "VALID_TRANSITIONS",
    # Scan ID
    "ScanId",
]

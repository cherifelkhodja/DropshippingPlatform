"""Payment Methods Value Object.

Represents a collection of payment methods accepted by a shop.
"""

from dataclasses import dataclass
from enum import Enum

from ..errors import InvalidPaymentMethodError


class PaymentMethod(Enum):
    """Enumeration of supported payment methods."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    SHOP_PAY = "shop_pay"
    KLARNA = "klarna"
    AFTERPAY = "afterpay"
    AFFIRM = "affirm"
    BANK_TRANSFER = "bank_transfer"
    COD = "cod"  # Cash on Delivery
    CRYPTO = "crypto"
    IDEAL = "ideal"
    SOFORT = "sofort"
    BANCONTACT = "bancontact"
    GIROPAY = "giropay"
    EPS = "eps"
    PRZELEWY24 = "przelewy24"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"

    @classmethod
    def from_string(cls, value: str) -> "PaymentMethod":
        """Create PaymentMethod from string value.

        Args:
            value: The payment method string.

        Returns:
            The corresponding PaymentMethod enum.

        Raises:
            InvalidPaymentMethodError: If the value is not a valid payment method.
        """
        normalized = value.lower().strip()
        for method in cls:
            if method.value == normalized:
                return method
        raise InvalidPaymentMethodError(value)


@dataclass(frozen=True)
class PaymentMethods:
    """Immutable collection of payment methods.

    Attributes:
        methods: A frozenset of PaymentMethod enums.
    """

    methods: frozenset[PaymentMethod]

    def __post_init__(self) -> None:
        """Validate payment methods after initialization."""
        if not isinstance(self.methods, frozenset):
            # Convert to frozenset if needed
            object.__setattr__(self, 'methods', frozenset(self.methods))

    @classmethod
    def from_strings(cls, values: list[str]) -> "PaymentMethods":
        """Create PaymentMethods from a list of string values.

        Args:
            values: List of payment method strings.

        Returns:
            A new PaymentMethods instance.
        """
        methods = frozenset(PaymentMethod.from_string(v) for v in values)
        return cls(methods=methods)

    @classmethod
    def empty(cls) -> "PaymentMethods":
        """Create an empty PaymentMethods instance."""
        return cls(methods=frozenset())

    def contains(self, method: PaymentMethod) -> bool:
        """Check if a payment method is supported."""
        return method in self.methods

    def has_buy_now_pay_later(self) -> bool:
        """Check if any buy-now-pay-later option is available."""
        bnpl_methods = {
            PaymentMethod.KLARNA,
            PaymentMethod.AFTERPAY,
            PaymentMethod.AFFIRM,
        }
        return bool(self.methods & bnpl_methods)

    def has_digital_wallets(self) -> bool:
        """Check if any digital wallet option is available."""
        wallet_methods = {
            PaymentMethod.PAYPAL,
            PaymentMethod.APPLE_PAY,
            PaymentMethod.GOOGLE_PAY,
            PaymentMethod.SHOP_PAY,
        }
        return bool(self.methods & wallet_methods)

    def __len__(self) -> int:
        return len(self.methods)

    def __iter__(self):
        return iter(self.methods)

    def __str__(self) -> str:
        return ", ".join(sorted(m.value for m in self.methods))

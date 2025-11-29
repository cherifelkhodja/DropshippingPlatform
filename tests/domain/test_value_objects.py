"""Tests for Domain Value Objects.

Tests validation, immutability, and behavior of all value objects.
"""

import pytest
import uuid

from src.app.core.domain import (
    # Value Objects
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
    # Errors
    InvalidUrlError,
    InvalidCountryError,
    InvalidLanguageError,
    InvalidCurrencyError,
    InvalidPaymentMethodError,
    InvalidProductCountError,
    InvalidPageStateError,
    InvalidCategoryError,
    InvalidScanIdError,
)


# =============================================================================
# URL Tests
# =============================================================================


class TestUrl:
    """Tests for Url value object."""

    def test_valid_https_url(self) -> None:
        """Test creation with valid HTTPS URL."""
        url = Url("https://example.com")
        assert url.value == "https://example.com"
        assert url.domain == "example.com"
        assert url.is_https is True

    def test_valid_http_url(self) -> None:
        """Test creation with valid HTTP URL."""
        url = Url("http://example.com")
        assert url.value == "http://example.com"
        assert url.is_https is False

    def test_url_with_path(self) -> None:
        """Test URL with path extraction."""
        url = Url("https://example.com/products/item-1")
        assert url.domain == "example.com"
        assert url.path == "/products/item-1"

    def test_url_with_port(self) -> None:
        """Test URL with port."""
        url = Url("https://example.com:8080/path")
        assert url.domain == "example.com"

    def test_empty_url_raises_error(self) -> None:
        """Test that empty URL raises InvalidUrlError."""
        with pytest.raises(InvalidUrlError):
            Url("")

    def test_invalid_url_format_raises_error(self) -> None:
        """Test that invalid URL format raises InvalidUrlError."""
        with pytest.raises(InvalidUrlError):
            Url("not-a-url")

    def test_url_without_protocol_raises_error(self) -> None:
        """Test that URL without protocol raises InvalidUrlError."""
        with pytest.raises(InvalidUrlError):
            Url("example.com")

    def test_url_is_immutable(self) -> None:
        """Test that URL is immutable (frozen dataclass)."""
        url = Url("https://example.com")
        with pytest.raises(AttributeError):
            url.value = "https://other.com"  # type: ignore

    def test_url_str_representation(self) -> None:
        """Test string representation of URL."""
        url = Url("https://example.com")
        assert str(url) == "https://example.com"


# =============================================================================
# Country Tests
# =============================================================================


class TestCountry:
    """Tests for Country value object."""

    def test_valid_country_code(self) -> None:
        """Test creation with valid country code."""
        country = Country("US")
        assert country.code == "US"

    def test_valid_country_code_lowercase(self) -> None:
        """Test that lowercase codes are normalized."""
        country = Country("fr")
        assert country.code == "FR"

    def test_multiple_valid_countries(self) -> None:
        """Test various valid country codes."""
        for code in ["US", "FR", "DE", "GB", "JP", "CN", "BR"]:
            country = Country(code)
            assert country.code == code.upper()

    def test_empty_country_code_raises_error(self) -> None:
        """Test that empty country code raises InvalidCountryError."""
        with pytest.raises(InvalidCountryError):
            Country("")

    def test_invalid_country_code_raises_error(self) -> None:
        """Test that invalid country code raises InvalidCountryError."""
        with pytest.raises(InvalidCountryError):
            Country("XX")

    def test_too_long_country_code_raises_error(self) -> None:
        """Test that code longer than 2 chars raises error."""
        with pytest.raises(InvalidCountryError):
            Country("USA")

    def test_country_equality(self) -> None:
        """Test country equality comparison."""
        c1 = Country("US")
        c2 = Country("us")
        c3 = Country("FR")
        assert c1 == c2
        assert c1 != c3

    def test_country_hash(self) -> None:
        """Test that countries can be used in sets."""
        countries = {Country("US"), Country("us"), Country("FR")}
        assert len(countries) == 2


# =============================================================================
# Language Tests
# =============================================================================


class TestLanguage:
    """Tests for Language value object."""

    def test_valid_language_code(self) -> None:
        """Test creation with valid language code."""
        lang = Language("en")
        assert lang.code == "en"

    def test_valid_language_code_uppercase(self) -> None:
        """Test that uppercase codes are normalized."""
        lang = Language("EN")
        assert lang.code == "en"

    def test_multiple_valid_languages(self) -> None:
        """Test various valid language codes."""
        for code in ["en", "fr", "de", "es", "ja", "zh"]:
            lang = Language(code)
            assert lang.code == code.lower()

    def test_empty_language_code_raises_error(self) -> None:
        """Test that empty language code raises InvalidLanguageError."""
        with pytest.raises(InvalidLanguageError):
            Language("")

    def test_invalid_language_code_raises_error(self) -> None:
        """Test that invalid language code raises InvalidLanguageError."""
        with pytest.raises(InvalidLanguageError):
            Language("xx")

    def test_language_equality(self) -> None:
        """Test language equality comparison."""
        l1 = Language("en")
        l2 = Language("EN")
        assert l1 == l2


# =============================================================================
# Currency Tests
# =============================================================================


class TestCurrency:
    """Tests for Currency value object."""

    def test_valid_currency_code(self) -> None:
        """Test creation with valid currency code."""
        currency = Currency("USD")
        assert currency.code == "USD"

    def test_valid_currency_code_lowercase(self) -> None:
        """Test that lowercase codes are normalized."""
        currency = Currency("usd")
        assert currency.code == "USD"

    def test_currency_symbol(self) -> None:
        """Test currency symbol property."""
        assert Currency("USD").symbol == "$"
        assert Currency("EUR").symbol == "€"
        assert Currency("GBP").symbol == "£"

    def test_multiple_valid_currencies(self) -> None:
        """Test various valid currency codes."""
        for code in ["USD", "EUR", "GBP", "JPY", "CNY", "BRL"]:
            currency = Currency(code)
            assert currency.code == code.upper()

    def test_empty_currency_code_raises_error(self) -> None:
        """Test that empty currency code raises InvalidCurrencyError."""
        with pytest.raises(InvalidCurrencyError):
            Currency("")

    def test_invalid_currency_code_raises_error(self) -> None:
        """Test that invalid currency code raises InvalidCurrencyError."""
        with pytest.raises(InvalidCurrencyError):
            Currency("XXX")

    def test_wrong_length_currency_code_raises_error(self) -> None:
        """Test that code not 3 chars raises error."""
        with pytest.raises(InvalidCurrencyError):
            Currency("US")


# =============================================================================
# PaymentMethods Tests
# =============================================================================


class TestPaymentMethods:
    """Tests for PaymentMethods value object."""

    def test_create_from_strings(self) -> None:
        """Test creation from string list."""
        methods = PaymentMethods.from_strings(["paypal", "credit_card"])
        assert len(methods) == 2
        assert methods.contains(PaymentMethod.PAYPAL)
        assert methods.contains(PaymentMethod.CREDIT_CARD)

    def test_empty_payment_methods(self) -> None:
        """Test empty payment methods."""
        methods = PaymentMethods.empty()
        assert len(methods) == 0

    def test_has_buy_now_pay_later(self) -> None:
        """Test BNPL detection."""
        with_bnpl = PaymentMethods.from_strings(["klarna", "paypal"])
        without_bnpl = PaymentMethods.from_strings(["paypal", "credit_card"])
        assert with_bnpl.has_buy_now_pay_later() is True
        assert without_bnpl.has_buy_now_pay_later() is False

    def test_has_digital_wallets(self) -> None:
        """Test digital wallet detection."""
        with_wallet = PaymentMethods.from_strings(["apple_pay", "credit_card"])
        without_wallet = PaymentMethods.from_strings(["credit_card", "bank_transfer"])
        assert with_wallet.has_digital_wallets() is True
        assert without_wallet.has_digital_wallets() is False

    def test_invalid_payment_method_raises_error(self) -> None:
        """Test that invalid payment method raises error."""
        with pytest.raises(InvalidPaymentMethodError):
            PaymentMethods.from_strings(["invalid_method"])

    def test_payment_method_from_string(self) -> None:
        """Test PaymentMethod enum from string."""
        method = PaymentMethod.from_string("paypal")
        assert method == PaymentMethod.PAYPAL


# =============================================================================
# ProductCount Tests
# =============================================================================


class TestProductCount:
    """Tests for ProductCount value object."""

    def test_valid_product_count(self) -> None:
        """Test creation with valid count."""
        count = ProductCount(100)
        assert count.value == 100
        assert int(count) == 100

    def test_zero_product_count(self) -> None:
        """Test zero count (boundary)."""
        count = ProductCount(0)
        assert count.value == 0
        assert count.is_empty() is True

    def test_max_product_count(self) -> None:
        """Test maximum count (boundary)."""
        count = ProductCount(1_000_000)
        assert count.value == 1_000_000

    def test_negative_count_raises_error(self) -> None:
        """Test that negative count raises InvalidProductCountError."""
        with pytest.raises(InvalidProductCountError):
            ProductCount(-1)

    def test_exceeds_max_raises_error(self) -> None:
        """Test that count exceeding max raises error."""
        with pytest.raises(InvalidProductCountError):
            ProductCount(1_000_001)

    def test_small_catalog_detection(self) -> None:
        """Test small catalog detection."""
        small = ProductCount(10)
        large = ProductCount(100)
        assert small.is_small_catalog() is True
        assert large.is_small_catalog() is False

    def test_large_catalog_detection(self) -> None:
        """Test large catalog detection."""
        small = ProductCount(500)
        large = ProductCount(1500)
        assert small.is_large_catalog() is False
        assert large.is_large_catalog() is True

    def test_product_count_addition(self) -> None:
        """Test adding product counts."""
        c1 = ProductCount(50)
        c2 = ProductCount(30)
        result = c1 + c2
        assert result.value == 80

    def test_product_count_comparison(self) -> None:
        """Test comparison operators."""
        c1 = ProductCount(50)
        c2 = ProductCount(100)
        assert c1 < c2
        assert c2 > c1
        assert c1 <= c1
        assert c2 >= c2


# =============================================================================
# Category Tests
# =============================================================================


class TestCategory:
    """Tests for Category value object."""

    def test_valid_category(self) -> None:
        """Test creation with valid category."""
        cat = Category("fashion")
        assert cat.value == "fashion"

    def test_category_normalized_to_lowercase(self) -> None:
        """Test that category is normalized to lowercase."""
        cat = Category("FASHION")
        assert cat.value == "fashion"

    def test_empty_category_raises_error(self) -> None:
        """Test that empty category raises InvalidCategoryError."""
        with pytest.raises(InvalidCategoryError):
            Category("")

    def test_too_short_category_raises_error(self) -> None:
        """Test that single char category raises error."""
        with pytest.raises(InvalidCategoryError):
            Category("a")

    def test_too_long_category_raises_error(self) -> None:
        """Test that category over 50 chars raises error."""
        with pytest.raises(InvalidCategoryError):
            Category("a" * 51)

    def test_is_predefined(self) -> None:
        """Test predefined category detection."""
        predefined = Category("fashion")
        custom = Category("custom_category")
        assert predefined.is_predefined() is True
        assert custom.is_predefined() is False

    def test_is_fashion_related(self) -> None:
        """Test fashion category detection."""
        fashion = Category("clothing")
        other = Category("electronics")
        assert fashion.is_fashion_related() is True
        assert other.is_fashion_related() is False

    def test_uncategorized_factory(self) -> None:
        """Test uncategorized factory method."""
        cat = Category.uncategorized()
        assert cat.value == "uncategorized"


# =============================================================================
# PageState Tests
# =============================================================================


class TestPageState:
    """Tests for PageState value object."""

    def test_initial_state(self) -> None:
        """Test initial state creation."""
        state = PageState.initial()
        assert state.status == PageStatus.DISCOVERED

    def test_from_string(self) -> None:
        """Test creation from string."""
        state = PageState.from_string("active")
        assert state.status == PageStatus.ACTIVE

    def test_valid_transition(self) -> None:
        """Test valid state transition."""
        state = PageState.initial()  # DISCOVERED
        new_state = state.transition_to(PageStatus.PENDING_ANALYSIS)
        assert new_state.status == PageStatus.PENDING_ANALYSIS

    def test_invalid_transition_raises_error(self) -> None:
        """Test that invalid transition raises InvalidPageStateError."""
        state = PageState.initial()  # DISCOVERED
        with pytest.raises(InvalidPageStateError):
            state.transition_to(PageStatus.ACTIVE)  # Can't go directly

    def test_can_transition_to(self) -> None:
        """Test transition possibility check."""
        state = PageState.initial()
        assert state.can_transition_to(PageStatus.PENDING_ANALYSIS) is True
        assert state.can_transition_to(PageStatus.ACTIVE) is False

    def test_is_terminal(self) -> None:
        """Test terminal state detection."""
        deleted = PageState(status=PageStatus.DELETED)
        active = PageState(status=PageStatus.ACTIVE)
        assert deleted.is_terminal() is True
        assert active.is_terminal() is False

    def test_is_active(self) -> None:
        """Test active state detection."""
        active = PageState(status=PageStatus.ACTIVE)
        pending = PageState(status=PageStatus.PENDING_ANALYSIS)
        assert active.is_active() is True
        assert pending.is_active() is False

    def test_is_error(self) -> None:
        """Test error state detection."""
        error = PageState(status=PageStatus.ERROR)
        unreachable = PageState(status=PageStatus.UNREACHABLE)
        active = PageState(status=PageStatus.ACTIVE)
        assert error.is_error() is True
        assert unreachable.is_error() is True
        assert active.is_error() is False

    def test_requires_analysis(self) -> None:
        """Test analysis requirement detection."""
        discovered = PageState(status=PageStatus.DISCOVERED)
        pending = PageState(status=PageStatus.PENDING_ANALYSIS)
        active = PageState(status=PageStatus.ACTIVE)
        assert discovered.requires_analysis() is True
        assert pending.requires_analysis() is True
        assert active.requires_analysis() is False

    def test_invalid_string_raises_error(self) -> None:
        """Test that invalid string raises InvalidPageStateError."""
        with pytest.raises(InvalidPageStateError):
            PageState.from_string("invalid_state")


# =============================================================================
# ScanId Tests
# =============================================================================


class TestScanId:
    """Tests for ScanId value object."""

    def test_generate_creates_valid_uuid(self) -> None:
        """Test that generate creates valid UUID v4."""
        scan_id = ScanId.generate()
        # Should be able to parse as UUID
        uuid.UUID(scan_id.value)

    def test_valid_uuid_string(self) -> None:
        """Test creation with valid UUID string."""
        valid_uuid = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        scan_id = ScanId(valid_uuid)
        assert scan_id.value == valid_uuid

    def test_uuid_normalized_to_lowercase(self) -> None:
        """Test that UUID is normalized to lowercase."""
        upper_uuid = "A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D"
        scan_id = ScanId(upper_uuid)
        assert scan_id.value == upper_uuid.lower()

    def test_empty_uuid_raises_error(self) -> None:
        """Test that empty UUID raises InvalidScanIdError."""
        with pytest.raises(InvalidScanIdError):
            ScanId("")

    def test_invalid_uuid_format_raises_error(self) -> None:
        """Test that invalid UUID format raises InvalidScanIdError."""
        with pytest.raises(InvalidScanIdError):
            ScanId("not-a-uuid")

    def test_wrong_uuid_version_raises_error(self) -> None:
        """Test that non-v4 UUID raises InvalidScanIdError."""
        # UUID v1 format
        with pytest.raises(InvalidScanIdError):
            ScanId("a1b2c3d4-e5f6-1a7b-8c9d-0e1f2a3b4c5d")

    def test_scan_id_equality(self) -> None:
        """Test ScanId equality comparison."""
        id1 = ScanId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
        id2 = ScanId("A1B2C3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")
        id3 = ScanId.generate()
        assert id1 == id2
        assert id1 != id3

    def test_scan_id_hash(self) -> None:
        """Test that ScanIds can be used in sets."""
        id1 = ScanId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
        id2 = ScanId("a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d")
        scan_ids = {id1, id2}
        assert len(scan_ids) == 1

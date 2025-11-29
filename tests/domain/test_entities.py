"""Tests for Domain Entities.

Tests creation, state transitions, and behavior of all entities.
"""

import pytest
from datetime import datetime, timedelta

from src.app.core.domain import (
    # Entities
    Page,
    Ad,
    AdStatus,
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
    # Value Objects
    Url,
    Country,
    Category,
    PageStatus,
    ProductCount,
    PaymentMethods,
)


# =============================================================================
# Page Entity Tests
# =============================================================================


class TestPage:
    """Tests for Page entity."""

    def test_create_page(self) -> None:
        """Test basic page creation."""
        url = Url("https://example-store.com")
        page = Page.create(
            id="page-123",
            url=url,
            country=Country("US"),
            category=Category("fashion"),
        )
        assert page.id == "page-123"
        assert page.url == url
        assert page.domain == "example-store.com"
        assert page.state.status == PageStatus.DISCOVERED
        assert page.is_shopify is False

    def test_page_domain_extracted_from_url(self) -> None:
        """Test that domain is extracted from URL."""
        url = Url("https://my-shop.example.com/products")
        page = Page.create(id="page-1", url=url)
        assert page.domain == "my-shop.example.com"

    def test_mark_as_shopify(self) -> None:
        """Test marking page as Shopify store."""
        url = Url("https://example.com")
        page = Page.create(id="page-1", url=url)
        # First transition to analyzed
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state.transition_to(PageStatus.PENDING_ANALYSIS),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state.transition_to(PageStatus.ANALYZING),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state.transition_to(PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

        updated = page.mark_as_shopify("profile-123")
        assert updated.is_shopify is True
        assert updated.shopify_profile_id == "profile-123"
        assert updated.state.status == PageStatus.VERIFIED_SHOPIFY

    def test_mark_as_not_shopify(self) -> None:
        """Test marking page as not Shopify."""
        url = Url("https://example.com")
        page = Page.create(id="page-1", url=url)
        # Transition to analyzed state
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state.transition_to(PageStatus.PENDING_ANALYSIS),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state.transition_to(PageStatus.ANALYZING),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )
        page = Page(
            id=page.id,
            url=page.url,
            domain=page.domain,
            state=page.state.transition_to(PageStatus.ANALYZED),
            created_at=page.created_at,
            updated_at=page.updated_at,
        )

        updated = page.mark_as_not_shopify()
        assert updated.is_shopify is False
        assert updated.state.status == PageStatus.NOT_SHOPIFY

    def test_update_ads_count(self) -> None:
        """Test updating ads count."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        updated = page.update_ads_count(active=10, total=25)
        assert updated.active_ads_count == 10
        assert updated.total_ads_count == 25
        assert updated.last_scanned_at is not None

    def test_update_score(self) -> None:
        """Test updating page score."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        updated = page.update_score(85.5)
        assert updated.score == 85.5

    def test_transition_state(self) -> None:
        """Test state transition."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        updated = page.transition_state(PageStatus.PENDING_ANALYSIS)
        assert updated.state.status == PageStatus.PENDING_ANALYSIS

    def test_is_active(self) -> None:
        """Test is_active method."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        assert page.is_active() is False

    def test_needs_analysis(self) -> None:
        """Test needs_analysis method."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        assert page.needs_analysis() is True

    def test_has_active_ads(self) -> None:
        """Test has_active_ads method."""
        page = Page.create(id="page-1", url=Url("https://example.com"))
        assert page.has_active_ads() is False
        updated = page.update_ads_count(active=5, total=10)
        assert updated.has_active_ads() is True

    def test_page_equality_by_id(self) -> None:
        """Test page equality is by ID."""
        page1 = Page.create(id="page-1", url=Url("https://example.com"))
        page2 = Page.create(id="page-1", url=Url("https://other.com"))
        page3 = Page.create(id="page-2", url=Url("https://example.com"))
        assert page1 == page2
        assert page1 != page3


# =============================================================================
# Ad Entity Tests
# =============================================================================


class TestAd:
    """Tests for Ad entity."""

    def test_create_ad(self) -> None:
        """Test basic ad creation."""
        ad = Ad.create(
            id="ad-123",
            page_id="page-456",
            meta_page_id="meta-789",
            meta_ad_id="meta-ad-123",
            status=AdStatus.ACTIVE,
        )
        assert ad.id == "ad-123"
        assert ad.page_id == "page-456"
        assert ad.status == AdStatus.ACTIVE
        assert ad.is_active() is True

    def test_mark_as_active(self) -> None:
        """Test marking ad as active."""
        ad = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            status=AdStatus.INACTIVE,
        )
        updated = ad.mark_as_active()
        assert updated.status == AdStatus.ACTIVE
        assert updated.ended_at is None

    def test_mark_as_inactive(self) -> None:
        """Test marking ad as inactive."""
        ad = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            status=AdStatus.ACTIVE,
        )
        updated = ad.mark_as_inactive()
        assert updated.status == AdStatus.INACTIVE
        assert updated.ended_at is not None

    def test_update_metrics(self) -> None:
        """Test updating ad metrics."""
        ad = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
        )
        updated = ad.update_metrics(
            impressions_lower=1000,
            impressions_upper=5000,
            spend_lower=100.0,
            spend_upper=500.0,
        )
        assert updated.impressions_lower == 1000
        assert updated.impressions_upper == 5000
        assert updated.spend_lower == 100.0
        assert updated.spend_upper == 500.0

    def test_is_video_ad(self) -> None:
        """Test video ad detection."""
        ad = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
        )
        assert ad.is_video_ad() is False

        ad_with_video = Ad(
            id="ad-2",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-2",
            video_url=Url("https://example.com/video.mp4"),
        )
        assert ad_with_video.is_video_ad() is True

    def test_has_link(self) -> None:
        """Test link detection."""
        ad = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
        )
        assert ad.has_link() is False

        ad_with_link = Ad(
            id="ad-2",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-2",
            link_url=Url("https://example.com/product"),
        )
        assert ad_with_link.has_link() is True

    def test_get_running_days(self) -> None:
        """Test running days calculation."""
        started = datetime.utcnow() - timedelta(days=10)
        ad = Ad(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            started_at=started,
        )
        days = ad.get_running_days()
        assert days == 10

    def test_get_running_days_no_start_date(self) -> None:
        """Test running days with no start date."""
        ad = Ad.create(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
        )
        assert ad.get_running_days() is None

    def test_get_estimated_impressions_avg(self) -> None:
        """Test average impressions calculation."""
        ad = Ad(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            impressions_lower=1000,
            impressions_upper=5000,
        )
        assert ad.get_estimated_impressions_avg() == 3000.0

    def test_get_estimated_spend_avg(self) -> None:
        """Test average spend calculation."""
        ad = Ad(
            id="ad-1",
            page_id="page-1",
            meta_page_id="meta-1",
            meta_ad_id="meta-ad-1",
            spend_lower=100.0,
            spend_upper=500.0,
        )
        assert ad.get_estimated_spend_avg() == 300.0

    def test_ad_equality_by_id(self) -> None:
        """Test ad equality is by ID."""
        ad1 = Ad.create(
            id="ad-1", page_id="page-1", meta_page_id="m1", meta_ad_id="ma1"
        )
        ad2 = Ad.create(
            id="ad-1", page_id="page-2", meta_page_id="m2", meta_ad_id="ma2"
        )
        assert ad1 == ad2


# =============================================================================
# ShopifyProfile Entity Tests
# =============================================================================


class TestShopifyProfile:
    """Tests for ShopifyProfile entity."""

    def test_create_profile(self) -> None:
        """Test basic profile creation."""
        url = Url("https://my-store.myshopify.com")
        profile = ShopifyProfile.create(
            id="profile-123",
            page_id="page-456",
            shop_name="My Store",
            shop_url=url,
        )
        assert profile.id == "profile-123"
        assert profile.shop_name == "My Store"
        assert len(profile.apps) == 0

    def test_update_product_count(self) -> None:
        """Test updating product count."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        updated = profile.update_product_count(ProductCount(150))
        assert updated.product_count.value == 150

    def test_update_theme(self) -> None:
        """Test updating theme."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        theme = ShopifyTheme(name="Dawn", version="2.0", is_custom=False)
        updated = profile.update_theme(theme)
        assert updated.theme == theme
        assert updated.theme.name == "Dawn"

    def test_add_app(self) -> None:
        """Test adding an app."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        app = ShopifyApp(name="Klaviyo", slug="klaviyo", category="marketing")
        updated = profile.add_app(app)
        assert len(updated.apps) == 1
        assert updated.has_app("Klaviyo") is True
        assert updated.has_app("Unknown") is False

    def test_update_payment_methods(self) -> None:
        """Test updating payment methods."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        methods = PaymentMethods.from_strings(["paypal", "apple_pay"])
        updated = profile.update_payment_methods(methods)
        assert len(updated.payment_methods) == 2

    def test_update_trust_score(self) -> None:
        """Test updating trust score."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        updated = profile.update_trust_score(92.5)
        assert updated.trust_score == 92.5

    def test_has_tracking_pixels(self) -> None:
        """Test tracking pixel detection."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        assert profile.has_tracking_pixels() is False

        profile_with_pixel = ShopifyProfile(
            id="p2",
            page_id="page-2",
            shop_name="Store",
            shop_url=Url("https://store.com"),
            facebook_pixel_id="123456",
        )
        assert profile_with_pixel.has_tracking_pixels() is True

    def test_is_well_equipped(self) -> None:
        """Test well-equipped store detection."""
        # Basic profile - not well equipped
        basic = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        assert basic.is_well_equipped() is False

    def test_get_app_count(self) -> None:
        """Test app count."""
        profile = ShopifyProfile.create(
            id="p1",
            page_id="page-1",
            shop_name="Store",
            shop_url=Url("https://store.com"),
        )
        profile = profile.add_app(ShopifyApp(name="App1"))
        profile = profile.add_app(ShopifyApp(name="App2"))
        assert profile.get_app_count() == 2


# =============================================================================
# Scan Entity Tests
# =============================================================================


class TestScan:
    """Tests for Scan entity."""

    def test_create_scan(self) -> None:
        """Test basic scan creation."""
        scan = Scan.create(
            page_id="page-123",
            scan_type=ScanType.FULL,
            priority=5,
        )
        assert scan.page_id == "page-123"
        assert scan.scan_type == ScanType.FULL
        assert scan.status == ScanStatus.PENDING
        assert scan.priority == 5

    def test_start_scan(self) -> None:
        """Test starting a scan."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.ADS_ONLY)
        started = scan.start()
        assert started.status == ScanStatus.RUNNING
        assert started.started_at is not None

    def test_complete_scan(self) -> None:
        """Test completing a scan."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        started = scan.start()
        result = ScanResult(ads_found=10, new_ads=5, is_shopify=True)
        completed = started.complete(result)
        assert completed.status == ScanStatus.COMPLETED
        assert completed.result == result
        assert completed.completed_at is not None

    def test_fail_scan(self) -> None:
        """Test failing a scan."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        started = scan.start()
        failed = started.fail("Network error")
        assert failed.status == ScanStatus.FAILED
        assert failed.error_message == "Network error"

    def test_retry_scan(self) -> None:
        """Test retrying a scan."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        started = scan.start()
        failed = started.fail("Error")
        retried = failed.retry()
        assert retried.status == ScanStatus.PENDING
        assert retried.retry_count == 1

    def test_can_retry(self) -> None:
        """Test retry eligibility."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        started = scan.start()
        failed = started.fail("Error")
        assert failed.can_retry() is True

        # Exhaust retries
        for _ in range(3):
            failed = failed.retry().start().fail("Error")
        assert failed.can_retry() is False

    def test_cancel_scan(self) -> None:
        """Test cancelling a scan."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        cancelled = scan.cancel()
        assert cancelled.status == ScanStatus.CANCELLED

    def test_timeout_scan(self) -> None:
        """Test timing out a scan."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        started = scan.start()
        timed_out = started.timeout()
        assert timed_out.status == ScanStatus.TIMEOUT
        assert timed_out.error_message == "Scan timed out"

    def test_scan_status_checks(self) -> None:
        """Test various status check methods."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        assert scan.is_pending() is True
        assert scan.is_running() is False

        started = scan.start()
        assert started.is_running() is True

        completed = started.complete(ScanResult())
        assert completed.is_completed() is True

        failed = scan.start().fail("Error")
        assert failed.is_failed() is True

    def test_get_duration_seconds(self) -> None:
        """Test duration calculation."""
        scan = Scan.create(page_id="page-1", scan_type=ScanType.FULL)
        assert scan.get_duration_seconds() is None

        started = scan.start()
        duration = started.get_duration_seconds()
        assert duration is not None
        assert duration >= 0


# =============================================================================
# KeywordRun Entity Tests
# =============================================================================


class TestKeywordRun:
    """Tests for KeywordRun entity."""

    def test_create_keyword_run(self) -> None:
        """Test basic keyword run creation."""
        run = KeywordRun.create(
            keyword="dropshipping",
            country=Country("US"),
            page_limit=100,
            priority=5,
        )
        assert run.keyword == "dropshipping"
        assert run.country.code == "US"
        assert run.page_limit == 100
        assert run.status == KeywordRunStatus.PENDING

    def test_empty_keyword_raises_error(self) -> None:
        """Test that empty keyword raises error."""
        with pytest.raises(ValueError):
            KeywordRun.create(keyword="", country=Country("US"))

    def test_keyword_trimmed(self) -> None:
        """Test that keyword is trimmed."""
        run = KeywordRun.create(keyword="  test  ", country=Country("US"))
        assert run.keyword == "test"

    def test_start_run(self) -> None:
        """Test starting a run."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        started = run.start()
        assert started.status == KeywordRunStatus.RUNNING
        assert started.started_at is not None

    def test_update_progress(self) -> None:
        """Test updating progress."""
        run = KeywordRun.create(keyword="test", country=Country("US"), page_limit=100)
        started = run.start()
        updated = started.update_progress(50)
        assert updated.pages_fetched == 50

    def test_complete_run(self) -> None:
        """Test completing a run."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        started = run.start()
        result = KeywordRunResult(
            total_ads_found=100,
            unique_pages_found=25,
            new_pages_found=10,
        )
        completed = started.complete(result)
        assert completed.status == KeywordRunStatus.COMPLETED
        assert completed.result == result

    def test_fail_run(self) -> None:
        """Test failing a run."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        started = run.start()
        failed = started.fail("API error")
        assert failed.status == KeywordRunStatus.FAILED
        assert failed.error_message == "API error"

    def test_rate_limit_run(self) -> None:
        """Test rate limiting a run."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        started = run.start()
        limited = started.rate_limit()
        assert limited.status == KeywordRunStatus.RATE_LIMITED
        assert limited.error_message == "Rate limit exceeded"

    def test_retry_run(self) -> None:
        """Test retrying a run."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        failed = run.start().fail("Error")
        retried = failed.retry()
        assert retried.status == KeywordRunStatus.PENDING
        assert retried.retry_count == 1
        assert retried.pages_fetched == 0

    def test_can_retry(self) -> None:
        """Test retry eligibility."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        failed = run.start().fail("Error")
        assert failed.can_retry() is True

        rate_limited = run.start().rate_limit()
        assert rate_limited.can_retry() is True

    def test_cancel_run(self) -> None:
        """Test cancelling a run."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        cancelled = run.cancel()
        assert cancelled.status == KeywordRunStatus.CANCELLED

    def test_get_progress_percentage(self) -> None:
        """Test progress percentage calculation."""
        run = KeywordRun.create(keyword="test", country=Country("US"), page_limit=100)
        started = run.start()
        updated = started.update_progress(50)
        assert updated.get_progress_percentage() == 50.0

    def test_get_duration_seconds(self) -> None:
        """Test duration calculation."""
        run = KeywordRun.create(keyword="test", country=Country("US"))
        assert run.get_duration_seconds() is None

        started = run.start()
        duration = started.get_duration_seconds()
        assert duration is not None


# =============================================================================
# ScanResult Tests
# =============================================================================


class TestScanResult:
    """Tests for ScanResult value object."""

    def test_scan_result_defaults(self) -> None:
        """Test ScanResult default values."""
        result = ScanResult()
        assert result.ads_found == 0
        assert result.new_ads == 0
        assert result.products_found == 0
        assert result.is_shopify is None
        assert result.has_errors() is False
        assert result.has_warnings() is False

    def test_scan_result_with_errors(self) -> None:
        """Test ScanResult with errors."""
        result = ScanResult(errors=["Error 1", "Error 2"])
        assert result.has_errors() is True

    def test_scan_result_with_warnings(self) -> None:
        """Test ScanResult with warnings."""
        result = ScanResult(warnings=["Warning 1"])
        assert result.has_warnings() is True


# =============================================================================
# KeywordRunResult Tests
# =============================================================================


class TestKeywordRunResult:
    """Tests for KeywordRunResult value object."""

    def test_keyword_run_result_defaults(self) -> None:
        """Test KeywordRunResult default values."""
        result = KeywordRunResult()
        assert result.total_ads_found == 0
        assert result.unique_pages_found == 0
        assert result.new_pages_found == 0
        assert result.has_results() is False

    def test_keyword_run_result_has_results(self) -> None:
        """Test has_results method."""
        result = KeywordRunResult(total_ads_found=10)
        assert result.has_results() is True

    def test_keyword_run_result_has_errors(self) -> None:
        """Test has_errors method."""
        result = KeywordRunResult(errors=["Error"])
        assert result.has_errors() is True

"""Pytest configuration and shared fixtures.

This module provides common fixtures and mock implementations
for testing the domain and use cases.
"""

import pytest
from typing import Any, Sequence
from unittest.mock import AsyncMock

from src.app.core.domain import (
    Page,
    Ad,
    AdStatus,
    Scan,
    ScanType,
    KeywordRun,
    ShopScore,
    Watchlist,
    WatchlistItem,
    Url,
    Country,
    Language,
    Currency,
    ScanId,
    ProductCount,
    Category,
)
from src.app.core.ports import (
    MetaAdsPort,
    HtmlScraperPort,
    SitemapPort,
)


# =============================================================================
# Domain Object Fixtures
# =============================================================================


@pytest.fixture
def valid_url() -> Url:
    """Return a valid URL."""
    return Url("https://example-store.com")


@pytest.fixture
def valid_country() -> Country:
    """Return a valid country."""
    return Country("US")


@pytest.fixture
def valid_language() -> Language:
    """Return a valid language."""
    return Language("en")


@pytest.fixture
def valid_currency() -> Currency:
    """Return a valid currency."""
    return Currency("USD")


@pytest.fixture
def valid_scan_id() -> ScanId:
    """Return a valid scan ID."""
    return ScanId.generate()


@pytest.fixture
def sample_page(valid_url: Url, valid_country: Country) -> Page:
    """Return a sample Page entity."""
    return Page.create(
        id="page-123",
        url=valid_url,
        country=valid_country,
        category=Category("fashion"),
    )


@pytest.fixture
def sample_ad() -> Ad:
    """Return a sample Ad entity."""
    return Ad.create(
        id="ad-123",
        page_id="page-123",
        meta_page_id="meta-page-123",
        meta_ad_id="meta-ad-123",
        status=AdStatus.ACTIVE,
    )


@pytest.fixture
def sample_scan(valid_scan_id: ScanId) -> Scan:
    """Return a sample Scan entity."""
    return Scan(
        id=valid_scan_id,
        page_id="page-123",
        scan_type=ScanType.FULL,
    )


@pytest.fixture
def sample_keyword_run(valid_country: Country) -> KeywordRun:
    """Return a sample KeywordRun entity."""
    return KeywordRun.create(
        keyword="dropshipping",
        country=valid_country,
        page_limit=100,
    )


# =============================================================================
# Mock Port Implementations
# =============================================================================


class FakeLoggingPort:
    """Fake logging port for testing."""

    def __init__(self) -> None:
        self.logs: list[dict[str, Any]] = []

    def info(self, msg: str, **context: Any) -> None:
        self.logs.append({"level": "info", "msg": msg, **context})

    def warning(self, msg: str, **context: Any) -> None:
        self.logs.append({"level": "warning", "msg": msg, **context})

    def error(self, msg: str, **context: Any) -> None:
        self.logs.append({"level": "error", "msg": msg, **context})

    def debug(self, msg: str, **context: Any) -> None:
        self.logs.append({"level": "debug", "msg": msg, **context})

    def critical(self, msg: str, **context: Any) -> None:
        self.logs.append({"level": "critical", "msg": msg, **context})


class FakePageRepository:
    """Fake page repository for testing."""

    def __init__(self) -> None:
        self.pages: dict[str, Page] = {}
        self._blacklisted_pages: set[str] = set()

    async def save(self, page: Page) -> None:
        self.pages[page.id] = page

    async def get(self, page_id: str) -> Page | None:
        return self.pages.get(page_id)

    async def exists(self, page_id: str) -> bool:
        return page_id in self.pages

    async def list_all(self) -> list[Page]:
        return list(self.pages.values())

    async def is_blacklisted(self, page_id: str) -> bool:
        return page_id in self._blacklisted_pages

    async def blacklist(self, page_id: str) -> None:
        self._blacklisted_pages.add(page_id)


class FakeAdsRepository:
    """Fake ads repository for testing."""

    def __init__(self) -> None:
        self.ads: list[Ad] = []

    async def save_many(self, ads: Sequence[Ad]) -> None:
        self.ads.extend(ads)

    async def list_by_page(self, page_id: str) -> list[Ad]:
        return [ad for ad in self.ads if ad.page_id == page_id]


class FakeScanRepository:
    """Fake scan repository for testing."""

    def __init__(self) -> None:
        self.scans: dict[str, Scan] = {}

    async def save_scan(self, scan: Scan) -> None:
        self.scans[str(scan.id)] = scan

    async def get_scan(self, scan_id: ScanId) -> Scan | None:
        return self.scans.get(str(scan_id))


class FakeKeywordRunRepository:
    """Fake keyword run repository for testing."""

    def __init__(self) -> None:
        self.runs: list[KeywordRun] = []

    async def save(self, run: KeywordRun) -> None:
        self.runs.append(run)

    async def list_recent(self, limit: int = 50) -> list[KeywordRun]:
        return sorted(
            self.runs,
            key=lambda r: r.created_at,
            reverse=True,
        )[:limit]


class FakeScoringRepository:
    """Fake scoring repository for testing."""

    def __init__(self) -> None:
        self.scores: list[ShopScore] = []
        # For ranked queries: store page info (page_id -> (url, country, name))
        self.page_info: dict[str, tuple[str | None, str | None, str | None]] = {}

    async def save(self, score: ShopScore) -> None:
        self.scores.append(score)

    async def get_latest_by_page_id(self, page_id: str) -> ShopScore | None:
        page_scores = [s for s in self.scores if s.page_id == page_id]
        if not page_scores:
            return None
        return sorted(page_scores, key=lambda s: s.created_at, reverse=True)[0]

    async def list_top(self, limit: int = 50, offset: int = 0) -> list[ShopScore]:
        sorted_scores = sorted(self.scores, key=lambda s: s.score, reverse=True)
        return sorted_scores[offset : offset + limit]

    async def count(self) -> int:
        return len(self.scores)

    async def list_ranked(
        self,
        criteria: "RankingCriteria",
    ) -> list["RankedShop"]:
        """Return ranked shops matching criteria."""
        from src.app.core.domain.entities.ranked_shop import RankedShop
        from src.app.core.domain.tiering import tier_to_score_range

        # Filter scores based on criteria
        filtered = self.scores.copy()

        if criteria.min_score is not None:
            filtered = [s for s in filtered if s.score >= criteria.min_score]

        if criteria.tier is not None:
            try:
                min_score, max_score = tier_to_score_range(criteria.tier)
                if criteria.tier == "XXL":
                    filtered = [s for s in filtered if s.score >= min_score]
                else:
                    filtered = [
                        s for s in filtered if min_score <= s.score < max_score
                    ]
            except ValueError:
                pass  # Invalid tier - skip filtering

        if criteria.country is not None:
            filtered = [
                s for s in filtered
                if s.page_id in self.page_info
                and self.page_info[s.page_id][1] == criteria.country
            ]

        # Sort by score DESC, then created_at DESC
        sorted_scores = sorted(
            filtered,
            key=lambda s: (s.score, s.created_at),
            reverse=True,
        )

        # Apply pagination
        paginated = sorted_scores[criteria.offset : criteria.offset + criteria.limit]

        # Convert to RankedShop
        result = []
        for score in paginated:
            info = self.page_info.get(score.page_id, (None, None, None))
            result.append(
                RankedShop(
                    page_id=score.page_id,
                    score=score.score,
                    tier=score.tier,
                    url=info[0],
                    country=info[1],
                    name=info[2],
                )
            )
        return result

    async def count_ranked(
        self,
        criteria: "RankingCriteria",
    ) -> int:
        """Count shops matching criteria (ignores limit/offset)."""
        from src.app.core.domain.tiering import tier_to_score_range

        filtered = self.scores.copy()

        if criteria.min_score is not None:
            filtered = [s for s in filtered if s.score >= criteria.min_score]

        if criteria.tier is not None:
            try:
                min_score, max_score = tier_to_score_range(criteria.tier)
                if criteria.tier == "XXL":
                    filtered = [s for s in filtered if s.score >= min_score]
                else:
                    filtered = [
                        s for s in filtered if min_score <= s.score < max_score
                    ]
            except ValueError:
                pass  # Invalid tier - skip filtering

        if criteria.country is not None:
            filtered = [
                s for s in filtered
                if s.page_id in self.page_info
                and self.page_info[s.page_id][1] == criteria.country
            ]

        return len(filtered)

    def set_page_info(
        self, page_id: str, url: str | None, country: str | None, name: str | None
    ) -> None:
        """Helper to set page info for testing ranked queries."""
        self.page_info[page_id] = (url, country, name)


class FakeTaskDispatcher:
    """Fake task dispatcher for testing."""

    def __init__(self) -> None:
        self.dispatched_tasks: list[dict[str, Any]] = []

    async def dispatch_scan_page(
        self,
        page_id: str,
        scan_id: ScanId,
        country: Country,
    ) -> None:
        self.dispatched_tasks.append(
            {
                "type": "scan_page",
                "page_id": page_id,
                "scan_id": str(scan_id),
                "country": str(country),
            }
        )

    async def dispatch_analyse_website(
        self,
        page_id: str,
        url: Url,
    ) -> None:
        self.dispatched_tasks.append(
            {
                "type": "analyse_website",
                "page_id": page_id,
                "url": str(url),
            }
        )

    async def dispatch_sitemap_count(
        self,
        page_id: str,
        website: Url,
        country: Country,
    ) -> None:
        self.dispatched_tasks.append(
            {
                "type": "sitemap_count",
                "page_id": page_id,
                "website": str(website),
                "country": str(country),
            }
        )

    async def dispatch_compute_shop_score(
        self,
        page_id: str,
    ) -> str:
        """Dispatch a compute shop score task."""
        import uuid
        task_id = str(uuid.uuid4())
        self.dispatched_tasks.append(
            {
                "type": "compute_shop_score",
                "page_id": page_id,
                "task_id": task_id,
            }
        )
        return task_id


class FakeWatchlistRepository:
    """Fake watchlist repository for testing."""

    def __init__(self) -> None:
        self.watchlists: dict[str, Watchlist] = {}
        self.items: list[WatchlistItem] = []

    async def create_watchlist(self, watchlist: Watchlist) -> Watchlist:
        self.watchlists[watchlist.id] = watchlist
        return watchlist

    async def get_watchlist(self, watchlist_id: str) -> Watchlist | None:
        return self.watchlists.get(watchlist_id)

    async def list_watchlists(
        self, limit: int = 50, offset: int = 0
    ) -> list[Watchlist]:
        sorted_watchlists = sorted(
            [w for w in self.watchlists.values() if w.is_active],
            key=lambda w: w.created_at,
            reverse=True,
        )
        return sorted_watchlists[offset : offset + limit]

    async def add_item(self, item: WatchlistItem) -> WatchlistItem:
        self.items.append(item)
        return item

    async def remove_item(self, watchlist_id: str, page_id: str) -> None:
        self.items = [
            i for i in self.items
            if not (i.watchlist_id == watchlist_id and i.page_id == page_id)
        ]

    async def list_items(self, watchlist_id: str) -> list[WatchlistItem]:
        return sorted(
            [i for i in self.items if i.watchlist_id == watchlist_id],
            key=lambda i: i.created_at,
        )

    async def is_page_in_watchlist(self, watchlist_id: str, page_id: str) -> bool:
        return any(
            i.watchlist_id == watchlist_id and i.page_id == page_id
            for i in self.items
        )


# =============================================================================
# Port Fixtures
# =============================================================================


@pytest.fixture
def fake_logger() -> FakeLoggingPort:
    """Return a fake logger."""
    return FakeLoggingPort()


@pytest.fixture
def fake_page_repo() -> FakePageRepository:
    """Return a fake page repository."""
    return FakePageRepository()


@pytest.fixture
def fake_ads_repo() -> FakeAdsRepository:
    """Return a fake ads repository."""
    return FakeAdsRepository()


@pytest.fixture
def fake_scan_repo() -> FakeScanRepository:
    """Return a fake scan repository."""
    return FakeScanRepository()


@pytest.fixture
def fake_keyword_run_repo() -> FakeKeywordRunRepository:
    """Return a fake keyword run repository."""
    return FakeKeywordRunRepository()


@pytest.fixture
def fake_scoring_repo() -> FakeScoringRepository:
    """Return a fake scoring repository."""
    return FakeScoringRepository()


@pytest.fixture
def fake_task_dispatcher() -> FakeTaskDispatcher:
    """Return a fake task dispatcher."""
    return FakeTaskDispatcher()


@pytest.fixture
def mock_meta_ads_port() -> AsyncMock:
    """Return a mocked MetaAdsPort."""
    mock = AsyncMock(spec=MetaAdsPort)
    mock.search_ads_by_keyword.return_value = []
    mock.get_ads_by_page.return_value = []
    mock.get_ads_details.return_value = []
    return mock


@pytest.fixture
def mock_html_scraper_port() -> AsyncMock:
    """Return a mocked HtmlScraperPort."""
    mock = AsyncMock(spec=HtmlScraperPort)
    mock.fetch_html.return_value = "<html></html>"
    mock.fetch_headers.return_value = {}
    return mock


@pytest.fixture
def mock_sitemap_port() -> AsyncMock:
    """Return a mocked SitemapPort."""
    mock = AsyncMock(spec=SitemapPort)
    mock.get_sitemap_urls.return_value = []
    mock.extract_product_count.return_value = ProductCount(0)
    return mock


@pytest.fixture
def fake_watchlist_repo() -> FakeWatchlistRepository:
    """Return a fake watchlist repository."""
    return FakeWatchlistRepository()

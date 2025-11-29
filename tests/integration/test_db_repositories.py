"""Integration tests for database repositories."""

from datetime import datetime
from uuid import uuid4

import pytest

from src.app.adapters.outbound.repositories import (
    PostgresAdsRepository,
    PostgresKeywordRunRepository,
    PostgresPageRepository,
    PostgresScanRepository,
)
from src.app.core.domain.entities.ad import Ad, AdStatus
from src.app.core.domain.entities.keyword_run import KeywordRun
from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.scan import Scan, ScanType
from src.app.core.domain.value_objects import Country, PageState, ScanId, Url

pytestmark = pytest.mark.integration


class TestPostgresPageRepository:
    """Tests for PostgresPageRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_page(self, db_session, unique_id):
        """Test saving and retrieving a page."""
        repo = PostgresPageRepository(db_session)

        page = Page(
            id=unique_id,
            url=Url(value="https://test-store.com"),
            domain="test-store.com",
            state=PageState.initial(),
            country=Country(code="US"),
            is_shopify=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await repo.save(page)
        retrieved = await repo.get(unique_id)

        assert retrieved is not None
        assert retrieved.id == unique_id
        assert retrieved.domain == "test-store.com"
        assert retrieved.is_shopify is True

    @pytest.mark.asyncio
    async def test_exists(self, db_session, unique_id):
        """Test checking page existence."""
        repo = PostgresPageRepository(db_session)

        page = Page(
            id=unique_id,
            url=Url(value="https://exists-test.com"),
            domain="exists-test.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert await repo.exists(unique_id) is False
        await repo.save(page)
        assert await repo.exists(unique_id) is True

    @pytest.mark.asyncio
    async def test_blacklist(self, db_session, unique_id):
        """Test blacklisting a page."""
        repo = PostgresPageRepository(db_session)

        assert await repo.is_blacklisted(unique_id) is False
        await repo.blacklist(unique_id)
        assert await repo.is_blacklisted(unique_id) is True

    @pytest.mark.asyncio
    async def test_list_all(self, db_session):
        """Test listing all pages."""
        repo = PostgresPageRepository(db_session)

        pages = await repo.list_all()
        assert isinstance(pages, list)


class TestPostgresAdsRepository:
    """Tests for PostgresAdsRepository."""

    @pytest.mark.asyncio
    async def test_save_many_and_list_by_page(self, db_session):
        """Test saving multiple ads and listing by page."""
        page_repo = PostgresPageRepository(db_session)
        ads_repo = PostgresAdsRepository(db_session)

        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value="https://ad-test-store.com"),
            domain="ad-test-store.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await page_repo.save(page)

        ads = [
            Ad(
                id=str(uuid4()),
                page_id=page_id,
                meta_page_id="meta_page_123",
                meta_ad_id=f"meta_ad_{i}",
                status=AdStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for i in range(3)
        ]

        await ads_repo.save_many(ads)
        retrieved = await ads_repo.list_by_page(page_id)

        assert len(retrieved) == 3


class TestPostgresScanRepository:
    """Tests for PostgresScanRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_scan(self, db_session):
        """Test saving and retrieving a scan."""
        page_repo = PostgresPageRepository(db_session)
        scan_repo = PostgresScanRepository(db_session)

        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value="https://scan-test-store.com"),
            domain="scan-test-store.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await page_repo.save(page)

        scan_id = ScanId.generate()
        scan = Scan(
            id=scan_id,
            page_id=page_id,
            scan_type=ScanType.FULL,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await scan_repo.save_scan(scan)
        retrieved = await scan_repo.get_scan(scan_id)

        assert retrieved is not None
        assert retrieved.id == scan_id
        assert retrieved.scan_type == ScanType.FULL


class TestPostgresKeywordRunRepository:
    """Tests for PostgresKeywordRunRepository."""

    @pytest.mark.asyncio
    async def test_save_and_list_recent(self, db_session):
        """Test saving and listing recent keyword runs."""
        repo = PostgresKeywordRunRepository(db_session)

        run = KeywordRun(
            id=ScanId.generate(),
            keyword="test keyword",
            country=Country(code="US"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        await repo.save(run)
        recent = await repo.list_recent(limit=10)

        assert len(recent) >= 1
        assert any(r.keyword == "test keyword" for r in recent)

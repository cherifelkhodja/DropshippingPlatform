"""Integration tests for PostgresScoringRepository."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from src.app.adapters.outbound.repositories import (
    PostgresPageRepository,
    PostgresScoringRepository,
)
from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.shop_score import ShopScore
from src.app.core.domain.value_objects import Url

pytestmark = pytest.mark.integration


class TestPostgresScoringRepository:
    """Tests for PostgresScoringRepository."""

    @pytest.mark.asyncio
    async def test_save_and_get_latest_by_page_id(self, db_session):
        """Test saving a score and retrieving it by page_id."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create a page first (required for FK)
        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value="https://score-test-store.com"),
            domain="score-test-store.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await page_repo.save(page)

        # Create and save a score
        score = ShopScore.create(
            id=str(uuid4()),
            page_id=page_id,
            score=75.5,
            components={
                "ads_activity": 80.0,
                "product_quality": 70.0,
                "site_health": 76.5,
            },
        )
        await scoring_repo.save(score)

        # Retrieve the latest score
        retrieved = await scoring_repo.get_latest_by_page_id(page_id)

        assert retrieved is not None
        assert retrieved.page_id == page_id
        assert retrieved.score == 75.5
        assert retrieved.components["ads_activity"] == 80.0
        assert retrieved.components["product_quality"] == 70.0
        assert retrieved.components["site_health"] == 76.5

    @pytest.mark.asyncio
    async def test_get_latest_returns_most_recent_score(self, db_session):
        """Test that get_latest_by_page_id returns the most recent score."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create a page
        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value="https://multi-score-store.com"),
            domain="multi-score-store.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await page_repo.save(page)

        # Create multiple scores with different timestamps
        now = datetime.utcnow()
        old_score = ShopScore(
            id=str(uuid4()),
            page_id=page_id,
            score=50.0,
            components={"version": 1.0},
            created_at=now - timedelta(hours=2),
        )
        medium_score = ShopScore(
            id=str(uuid4()),
            page_id=page_id,
            score=65.0,
            components={"version": 2.0},
            created_at=now - timedelta(hours=1),
        )
        newest_score = ShopScore(
            id=str(uuid4()),
            page_id=page_id,
            score=80.0,
            components={"version": 3.0},
            created_at=now,
        )

        # Save in random order
        await scoring_repo.save(medium_score)
        await scoring_repo.save(old_score)
        await scoring_repo.save(newest_score)

        # Should return the newest score
        retrieved = await scoring_repo.get_latest_by_page_id(page_id)

        assert retrieved is not None
        assert retrieved.score == 80.0
        assert retrieved.components["version"] == 3.0

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_for_unknown_page(self, db_session):
        """Test that get_latest_by_page_id returns None for unknown page."""
        scoring_repo = PostgresScoringRepository(db_session)

        unknown_page_id = str(uuid4())
        result = await scoring_repo.get_latest_by_page_id(unknown_page_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_top_returns_scores_ordered_by_score_desc(self, db_session):
        """Test that list_top returns scores ordered by score descending."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create multiple pages with different scores
        pages_and_scores = [
            ("https://low-score.com", "low-score.com", 25.0),
            ("https://medium-score.com", "medium-score.com", 55.0),
            ("https://high-score.com", "high-score.com", 95.0),
            ("https://mid-high-score.com", "mid-high-score.com", 75.0),
        ]

        for url, domain, score_value in pages_and_scores:
            page_id = str(uuid4())
            page = Page(
                id=page_id,
                url=Url(value=url),
                domain=domain,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await page_repo.save(page)

            score = ShopScore.create(
                id=str(uuid4()),
                page_id=page_id,
                score=score_value,
            )
            await scoring_repo.save(score)

        # Get top scores
        top_scores = await scoring_repo.list_top(limit=10)

        assert len(top_scores) >= 4
        # Verify ordering (highest first)
        scores = [s.score for s in top_scores[:4]]
        assert scores == sorted(scores, reverse=True)
        assert top_scores[0].score == 95.0

    @pytest.mark.asyncio
    async def test_list_top_respects_limit_and_offset(self, db_session):
        """Test that list_top respects limit and offset parameters."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create 5 pages with different scores
        created_scores = []
        for i in range(5):
            page_id = str(uuid4())
            page = Page(
                id=page_id,
                url=Url(value=f"https://page-{i}.com"),
                domain=f"page-{i}.com",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            await page_repo.save(page)

            score = ShopScore.create(
                id=str(uuid4()),
                page_id=page_id,
                score=float((i + 1) * 20),  # 20, 40, 60, 80, 100
            )
            await scoring_repo.save(score)
            created_scores.append(score.score)

        # Test limit
        top_2 = await scoring_repo.list_top(limit=2)
        assert len(top_2) == 2
        assert top_2[0].score == 100.0
        assert top_2[1].score == 80.0

        # Test offset
        offset_2 = await scoring_repo.list_top(limit=2, offset=2)
        assert len(offset_2) == 2
        assert offset_2[0].score == 60.0
        assert offset_2[1].score == 40.0

    @pytest.mark.asyncio
    async def test_score_clamping(self, db_session):
        """Test that scores are clamped to 0-100 range."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value="https://clamp-test.com"),
            domain="clamp-test.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await page_repo.save(page)

        # Test score above 100
        high_score = ShopScore.create(
            id=str(uuid4()),
            page_id=page_id,
            score=150.0,  # Should be clamped to 100
        )
        assert high_score.score == 100.0

        # Test score below 0
        low_score = ShopScore.create(
            id=str(uuid4()),
            page_id=page_id,
            score=-25.0,  # Should be clamped to 0
        )
        assert low_score.score == 0.0

        # Save and verify persistence
        await scoring_repo.save(high_score)
        retrieved = await scoring_repo.get_latest_by_page_id(page_id)
        assert retrieved is not None
        assert retrieved.score == 100.0

    @pytest.mark.asyncio
    async def test_components_stored_correctly(self, db_session):
        """Test that component sub-scores are stored and retrieved correctly."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value="https://components-test.com"),
            domain="components-test.com",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await page_repo.save(page)

        components = {
            "ads_activity_score": 85.5,
            "product_catalog_score": 72.3,
            "site_quality_score": 68.9,
            "social_presence_score": 91.2,
            "trust_indicators_score": 45.0,
        }

        score = ShopScore.create(
            id=str(uuid4()),
            page_id=page_id,
            score=72.58,
            components=components,
        )
        await scoring_repo.save(score)

        retrieved = await scoring_repo.get_latest_by_page_id(page_id)

        assert retrieved is not None
        assert len(retrieved.components) == 5
        for key, value in components.items():
            assert retrieved.components[key] == value

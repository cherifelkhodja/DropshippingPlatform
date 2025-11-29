"""Integration tests for PostgresScoringRepository ranking methods.

Tests for list_ranked and count_ranked methods that support
filtered and paginated ranking queries.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from src.app.adapters.outbound.repositories import (
    PostgresPageRepository,
    PostgresScoringRepository,
)
from src.app.core.domain.entities.page import Page
from src.app.core.domain.entities.shop_score import ShopScore
from src.app.core.domain.value_objects import Url, RankingCriteria

pytestmark = pytest.mark.integration


class TestPostgresScoringRepositoryRanking:
    """Tests for PostgresScoringRepository ranking methods."""

    async def _create_page_with_score(
        self,
        page_repo: PostgresPageRepository,
        scoring_repo: PostgresScoringRepository,
        url: str,
        domain: str,
        score_value: float,
        country: str | None = None,
    ) -> tuple[str, ShopScore]:
        """Helper to create a page with a score for testing.

        Args:
            page_repo: Page repository instance.
            scoring_repo: Scoring repository instance.
            url: The page URL.
            domain: The page domain.
            score_value: The score value (0-100).
            country: Optional country code (ISO 3166-1 alpha-2).

        Returns:
            Tuple of (page_id, ShopScore).
        """
        page_id = str(uuid4())
        page = Page(
            id=page_id,
            url=Url(value=url),
            domain=domain,
            country=country,
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

        return page_id, score

    @pytest.mark.asyncio
    async def test_list_ranked_global_ordering(self, db_session):
        """Test that list_ranked returns shops ordered by score descending."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create pages with different scores:
        # - Page A: high score (90), FR
        # - Page B: medium score (60), FR
        # - Page C: low score (20), US
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://high-score-fr.com", "high-score-fr.com",
            score_value=90.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://medium-score-fr.com", "medium-score-fr.com",
            score_value=60.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://low-score-us.com", "low-score-us.com",
            score_value=20.0, country="US",
        )

        # Query without filters
        criteria = RankingCriteria(limit=10, offset=0)
        results = await scoring_repo.list_ranked(criteria)

        # Verify ordering: highest score first
        assert len(results) == 3
        assert results[0].score == 90.0
        assert results[0].tier == "XXL"
        assert results[1].score == 60.0
        assert results[1].tier == "L"
        assert results[2].score == 20.0
        assert results[2].tier == "XS"

    @pytest.mark.asyncio
    async def test_list_ranked_with_min_score(self, db_session):
        """Test that list_ranked filters by min_score correctly."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create pages with scores: 90, 60, 20
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://high-score.com", "high-score.com",
            score_value=90.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://medium-score.com", "medium-score.com",
            score_value=60.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://low-score.com", "low-score.com",
            score_value=20.0, country="US",
        )

        # Filter by min_score=50 (should exclude the 20 score)
        criteria = RankingCriteria(limit=10, offset=0, min_score=50.0)
        results = await scoring_repo.list_ranked(criteria)

        # Only scores >= 50 should be returned
        assert len(results) == 2
        assert all(r.score >= 50.0 for r in results)
        assert results[0].score == 90.0
        assert results[1].score == 60.0

    @pytest.mark.asyncio
    async def test_list_ranked_with_country_filter(self, db_session):
        """Test that list_ranked filters by country correctly."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create pages with different countries
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://fr-shop-1.com", "fr-shop-1.com",
            score_value=90.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://fr-shop-2.com", "fr-shop-2.com",
            score_value=60.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://us-shop.com", "us-shop.com",
            score_value=80.0, country="US",
        )

        # Filter by country=FR
        criteria = RankingCriteria(limit=10, offset=0, country="FR")
        results = await scoring_repo.list_ranked(criteria)

        # Only FR shops should be returned
        assert len(results) == 2
        assert all(r.country == "FR" for r in results)
        assert results[0].score == 90.0
        assert results[1].score == 60.0

    @pytest.mark.asyncio
    async def test_list_ranked_with_tier_filter(self, db_session):
        """Test that list_ranked filters by tier correctly."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create pages with scores in different tiers:
        # - XXL: 90 (>= 85)
        # - XL: 75 (>= 70, < 85)
        # - L: 60 (>= 55, < 70)
        # - M: 45 (>= 40, < 55)
        # - S: 30 (>= 25, < 40)
        # - XS: 15 (< 25)
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://xxl-shop.com", "xxl-shop.com",
            score_value=90.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://xl-shop.com", "xl-shop.com",
            score_value=75.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://l-shop.com", "l-shop.com",
            score_value=60.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://m-shop.com", "m-shop.com",
            score_value=45.0, country="US",
        )

        # Filter by tier=XL (scores between 70 and 85)
        criteria = RankingCriteria(limit=10, offset=0, tier="XL")
        results = await scoring_repo.list_ranked(criteria)

        # Only XL tier shops should be returned
        assert len(results) == 1
        assert results[0].score == 75.0
        assert results[0].tier == "XL"

        # Filter by tier=XXL (scores >= 85)
        criteria_xxl = RankingCriteria(limit=10, offset=0, tier="XXL")
        results_xxl = await scoring_repo.list_ranked(criteria_xxl)

        assert len(results_xxl) == 1
        assert results_xxl[0].score == 90.0
        assert results_xxl[0].tier == "XXL"

    @pytest.mark.asyncio
    async def test_list_ranked_with_combined_filters(self, db_session):
        """Test that list_ranked applies multiple filters correctly."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create diverse test data
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://fr-high.com", "fr-high.com",
            score_value=90.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://fr-medium.com", "fr-medium.com",
            score_value=60.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://us-high.com", "us-high.com",
            score_value=85.0, country="US",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://us-low.com", "us-low.com",
            score_value=30.0, country="US",
        )

        # Filter by country=FR AND min_score=50
        criteria = RankingCriteria(limit=10, offset=0, country="FR", min_score=50.0)
        results = await scoring_repo.list_ranked(criteria)

        # Should return only FR shops with score >= 50
        assert len(results) == 2
        assert all(r.country == "FR" and r.score >= 50.0 for r in results)

    @pytest.mark.asyncio
    async def test_list_ranked_pagination(self, db_session):
        """Test that list_ranked respects limit and offset."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create 5 pages with different scores
        for i in range(5):
            await self._create_page_with_score(
                page_repo, scoring_repo,
                f"https://shop-{i}.com", f"shop-{i}.com",
                score_value=float(100 - i * 10),  # 100, 90, 80, 70, 60
                country="FR",
            )

        # Get first page (limit=2, offset=0)
        criteria_page1 = RankingCriteria(limit=2, offset=0)
        results_page1 = await scoring_repo.list_ranked(criteria_page1)

        assert len(results_page1) == 2
        assert results_page1[0].score == 100.0
        assert results_page1[1].score == 90.0

        # Get second page (limit=2, offset=2)
        criteria_page2 = RankingCriteria(limit=2, offset=2)
        results_page2 = await scoring_repo.list_ranked(criteria_page2)

        assert len(results_page2) == 2
        assert results_page2[0].score == 80.0
        assert results_page2[1].score == 70.0

        # Get third page (limit=2, offset=4) - should only have 1 result
        criteria_page3 = RankingCriteria(limit=2, offset=4)
        results_page3 = await scoring_repo.list_ranked(criteria_page3)

        assert len(results_page3) == 1
        assert results_page3[0].score == 60.0

    @pytest.mark.asyncio
    async def test_list_ranked_returns_page_info(self, db_session):
        """Test that list_ranked returns page information in RankedShop."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://example-shop.com/store", "example-shop.com",
            score_value=85.0, country="US",
        )

        criteria = RankingCriteria(limit=10, offset=0)
        results = await scoring_repo.list_ranked(criteria)

        assert len(results) == 1
        ranked_shop = results[0]

        # Verify all RankedShop fields are populated
        assert ranked_shop.page_id is not None
        assert ranked_shop.score == 85.0
        assert ranked_shop.tier == "XXL"
        assert ranked_shop.url == "https://example-shop.com/store"
        assert ranked_shop.country == "US"
        assert ranked_shop.name == "example-shop.com"  # domain used as name

    @pytest.mark.asyncio
    async def test_count_ranked_without_filters(self, db_session):
        """Test that count_ranked returns correct total count."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create 3 pages with scores
        for i in range(3):
            await self._create_page_with_score(
                page_repo, scoring_repo,
                f"https://shop-{i}.com", f"shop-{i}.com",
                score_value=float(50 + i * 20),  # 50, 70, 90
                country="FR" if i < 2 else "US",
            )

        # Count all (no filters)
        criteria = RankingCriteria(limit=10, offset=0)
        count = await scoring_repo.count_ranked(criteria)

        assert count == 3

    @pytest.mark.asyncio
    async def test_count_ranked_matches_filters(self, db_session):
        """Test that count_ranked applies filters correctly."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create pages with different scores and countries
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://fr-high.com", "fr-high.com",
            score_value=90.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://fr-low.com", "fr-low.com",
            score_value=30.0, country="FR",
        )
        await self._create_page_with_score(
            page_repo, scoring_repo,
            "https://us-high.com", "us-high.com",
            score_value=85.0, country="US",
        )

        # Count by country
        criteria_fr = RankingCriteria(limit=10, offset=0, country="FR")
        count_fr = await scoring_repo.count_ranked(criteria_fr)
        assert count_fr == 2

        criteria_us = RankingCriteria(limit=10, offset=0, country="US")
        count_us = await scoring_repo.count_ranked(criteria_us)
        assert count_us == 1

        # Count by min_score
        criteria_high = RankingCriteria(limit=10, offset=0, min_score=80.0)
        count_high = await scoring_repo.count_ranked(criteria_high)
        assert count_high == 2  # 90 and 85

        # Count by tier
        criteria_xxl = RankingCriteria(limit=10, offset=0, tier="XXL")
        count_xxl = await scoring_repo.count_ranked(criteria_xxl)
        assert count_xxl == 2  # 90 and 85 are both >= 85

        # Combined filters
        criteria_combined = RankingCriteria(
            limit=10, offset=0, country="FR", min_score=50.0
        )
        count_combined = await scoring_repo.count_ranked(criteria_combined)
        assert count_combined == 1  # Only fr-high (90) matches

    @pytest.mark.asyncio
    async def test_count_ranked_ignores_pagination(self, db_session):
        """Test that count_ranked ignores limit/offset parameters."""
        page_repo = PostgresPageRepository(db_session)
        scoring_repo = PostgresScoringRepository(db_session)

        # Create 5 pages
        for i in range(5):
            await self._create_page_with_score(
                page_repo, scoring_repo,
                f"https://shop-{i}.com", f"shop-{i}.com",
                score_value=float(50 + i * 10),
                country="FR",
            )

        # Count with small limit - should still return total
        criteria_small = RankingCriteria(limit=2, offset=0)
        count_small = await scoring_repo.count_ranked(criteria_small)
        assert count_small == 5  # Total, not affected by limit

        # Count with offset - should still return total
        criteria_offset = RankingCriteria(limit=10, offset=3)
        count_offset = await scoring_repo.count_ranked(criteria_offset)
        assert count_offset == 5  # Total, not affected by offset

    @pytest.mark.asyncio
    async def test_list_ranked_empty_result(self, db_session):
        """Test that list_ranked returns empty list when no matches."""
        scoring_repo = PostgresScoringRepository(db_session)

        # Query with filter that matches nothing
        criteria = RankingCriteria(limit=10, offset=0, country="ZZ")
        results = await scoring_repo.list_ranked(criteria)

        assert results == []

    @pytest.mark.asyncio
    async def test_count_ranked_zero_when_empty(self, db_session):
        """Test that count_ranked returns 0 when no matches."""
        scoring_repo = PostgresScoringRepository(db_session)

        # Query with filter that matches nothing
        criteria = RankingCriteria(limit=10, offset=0, country="ZZ")
        count = await scoring_repo.count_ranked(criteria)

        assert count == 0

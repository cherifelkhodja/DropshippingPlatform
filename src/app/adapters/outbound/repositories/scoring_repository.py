"""PostgreSQL Scoring Repository.

Implements ScoringRepository port with SQLAlchemy async operations.
"""

from uuid import UUID

from sqlalchemy import func, select, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.domain.entities.shop_score import ShopScore
from src.app.core.domain.entities.ranked_shop import RankedShop
from src.app.core.domain.errors import RepositoryError
from src.app.core.domain.value_objects.ranking import RankingCriteria, TIER_SCORE_RANGES
from src.app.infrastructure.db.mappers import shop_score_mapper
from src.app.infrastructure.db.models.shop_score_model import ShopScoreModel
from src.app.infrastructure.db.models.page_model import PageModel


class PostgresScoringRepository:
    """SQLAlchemy implementation of ScoringRepository port.

    Handles ShopScore entity persistence with PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save(self, score: ShopScore) -> None:
        """Save a shop score.

        Args:
            score: The ShopScore entity to save.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            model = shop_score_mapper.to_model(score)
            merged = await self._session.merge(model)
            self._session.add(merged)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RepositoryError(
                operation="save_score",
                reason=f"Failed to save shop score: {exc}",
            ) from exc

    async def get_latest_by_page_id(self, page_id: str) -> ShopScore | None:
        """Retrieve the most recent score for a page.

        Args:
            page_id: The unique page identifier.

        Returns:
            The most recent ShopScore for the page, or None if no scores exist.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = (
                select(ShopScoreModel)
                .where(ShopScoreModel.page_id == UUID(page_id))
                .order_by(ShopScoreModel.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return shop_score_mapper.to_domain(model)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="get_latest_score",
                reason=f"Failed to get latest score for page: {exc}",
            ) from exc

    async def list_top(self, limit: int = 50, offset: int = 0) -> list[ShopScore]:
        """List top-scoring pages.

        Returns the most recent score for each page, ordered by score descending.

        Args:
            limit: Maximum number of scores to return.
            offset: Number of scores to skip.

        Returns:
            List of ShopScore entities ordered by score descending.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Get all scores, order by score desc then created_at desc
            # This gives us a simple leaderboard of scores
            stmt = (
                select(ShopScoreModel)
                .order_by(
                    ShopScoreModel.score.desc(),
                    ShopScoreModel.created_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [shop_score_mapper.to_domain(model) for model in models]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_top_scores",
                reason=f"Failed to list top scores: {exc}",
            ) from exc

    async def count(self) -> int:
        """Count total number of shop scores.

        Returns:
            The total count of ShopScore entities.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            stmt = select(func.count()).select_from(ShopScoreModel)
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="count_scores",
                reason=f"Failed to count scores: {exc}",
            ) from exc

    def _build_ranking_filters(
        self, criteria: RankingCriteria
    ) -> list:
        """Build SQLAlchemy filter conditions from ranking criteria.

        Translates domain criteria into database filter conditions.
        Tier filtering is done by translating tier names to score ranges
        using the TIER_SCORE_RANGES mapping from the domain.

        Args:
            criteria: The ranking criteria with filter parameters.

        Returns:
            List of SQLAlchemy filter conditions.
        """
        filters = []

        # Filter by min_score
        if criteria.min_score is not None:
            filters.append(ShopScoreModel.score >= criteria.min_score)

        # Filter by tier (translate to score range)
        # Tiers are based on score ranges defined in TIER_SCORE_RANGES:
        # - XXL: 85-100
        # - XL: 70-85
        # - L: 55-70
        # - M: 40-55
        # - S: 25-40
        # - XS: 0-25
        if criteria.tier is not None:
            score_range = TIER_SCORE_RANGES.get(criteria.tier)
            if score_range:
                min_tier_score, max_tier_score = score_range
                filters.append(ShopScoreModel.score >= min_tier_score)
                # For XXL tier (85-100), max is 100 inclusive
                # For other tiers, max is exclusive (e.g., XL is >= 70 and < 85)
                if criteria.tier != "XXL":
                    filters.append(ShopScoreModel.score < max_tier_score)

        # Filter by country (requires join with PageModel)
        if criteria.country is not None:
            filters.append(PageModel.country == criteria.country)

        return filters

    def _row_to_ranked_shop(
        self,
        score_model: ShopScoreModel,
        page_model: PageModel | None,
    ) -> RankedShop:
        """Convert database row to RankedShop domain projection.

        Maps ORM models to the RankedShop read-model, computing the tier
        from the score value.

        Args:
            score_model: The ShopScoreModel from the database.
            page_model: The associated PageModel (may be None).

        Returns:
            A RankedShop projection instance.
        """
        # Compute tier from score (same logic as ShopScore.tier property)
        score = score_model.score
        if score >= 85.0:
            tier = "XXL"
        elif score >= 70.0:
            tier = "XL"
        elif score >= 55.0:
            tier = "L"
        elif score >= 40.0:
            tier = "M"
        elif score >= 25.0:
            tier = "S"
        else:
            tier = "XS"

        return RankedShop(
            page_id=str(score_model.page_id),
            score=score,
            tier=tier,
            url=page_model.url if page_model else None,
            country=page_model.country if page_model else None,
            name=page_model.domain if page_model else None,  # Using domain as name
        )

    async def list_ranked(
        self,
        criteria: RankingCriteria,
    ) -> list[RankedShop]:
        """Return a ranked list of shops matching the criteria.

        Queries shop scores joined with pages, applying filters from criteria
        (tier, min_score, country). Results are ordered by score descending,
        then by created_at descending for ties.

        Args:
            criteria: The ranking criteria including filters and pagination.

        Returns:
            List of RankedShop projections matching the criteria.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Build base query with join to pages for country filter and page info
            stmt = (
                select(ShopScoreModel, PageModel)
                .join(PageModel, ShopScoreModel.page_id == PageModel.id)
            )

            # Apply filters
            filters = self._build_ranking_filters(criteria)
            if filters:
                stmt = stmt.where(and_(*filters))

            # Apply ordering: score DESC, then created_at DESC for ties
            stmt = stmt.order_by(
                ShopScoreModel.score.desc(),
                ShopScoreModel.created_at.desc(),
            )

            # Apply pagination
            stmt = stmt.offset(criteria.offset).limit(criteria.limit)

            result = await self._session.execute(stmt)
            rows = result.all()

            return [
                self._row_to_ranked_shop(score_model, page_model)
                for score_model, page_model in rows
            ]
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="list_ranked",
                reason=f"Failed to list ranked shops: {exc}",
            ) from exc

    async def count_ranked(
        self,
        criteria: RankingCriteria,
    ) -> int:
        """Return total count of shops matching the criteria.

        Counts shops matching the same filters as list_ranked (tier, min_score,
        country) but ignores limit/offset for pagination purposes.

        Args:
            criteria: The ranking criteria including filters (limit/offset ignored).

        Returns:
            Total count of shops matching the filter criteria.

        Raises:
            RepositoryError: On database errors.
        """
        try:
            # Build count query with join to pages for country filter
            stmt = (
                select(func.count())
                .select_from(ShopScoreModel)
                .join(PageModel, ShopScoreModel.page_id == PageModel.id)
            )

            # Apply same filters as list_ranked
            filters = self._build_ranking_filters(criteria)
            if filters:
                stmt = stmt.where(and_(*filters))

            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as exc:
            raise RepositoryError(
                operation="count_ranked",
                reason=f"Failed to count ranked shops: {exc}",
            ) from exc

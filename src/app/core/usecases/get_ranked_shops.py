"""Get Ranked Shops Use Case.

Use case for retrieving ranked shops with filtering and pagination.
"""

from src.app.core.domain.entities.ranked_shop import RankedShopsResult
from src.app.core.domain.value_objects.ranking import RankingCriteria
from src.app.core.ports.logging_port import LoggingPort
from src.app.core.ports.repository_port import ScoringRepository


class GetRankedShopsUseCase:
    """Use case for retrieving ranked shops.

    Queries the scoring repository to get a paginated list of shops
    ordered by score, with optional filters for tier, min_score, and country.

    This use case orchestrates:
    - Logging of query criteria
    - Fetching ranked shops from repository
    - Counting total matching shops for pagination
    - Assembling the final paginated result
    """

    def __init__(
        self,
        scoring_repository: ScoringRepository,
        logger: LoggingPort,
    ) -> None:
        """Initialize the use case with dependencies.

        Args:
            scoring_repository: Repository for scoring data access.
            logger: Logging port for structured logging.
        """
        self._scoring_repository = scoring_repository
        self._logger = logger

    async def execute(self, criteria: RankingCriteria) -> RankedShopsResult:
        """Execute the get ranked shops use case.

        Fetches a paginated list of ranked shops matching the given criteria,
        along with the total count for pagination.

        Args:
            criteria: The ranking criteria including filters and pagination.

        Returns:
            RankedShopsResult containing the list of shops, total count,
            and pagination metadata.

        Raises:
            RepositoryError: On database errors.
        """
        # Log the query criteria
        self._logger.info(
            "Getting ranked shops",
            limit=criteria.limit,
            offset=criteria.offset,
            tier=criteria.tier,
            min_score=criteria.min_score,
            country=criteria.country,
        )

        # Fetch ranked shops from repository
        shops = await self._scoring_repository.list_ranked(criteria)

        # Get total count for pagination (same filters, no limit/offset)
        total = await self._scoring_repository.count_ranked(criteria)

        self._logger.debug(
            "Ranked shops retrieved",
            items_count=len(shops),
            total=total,
            limit=criteria.limit,
            offset=criteria.offset,
        )

        # Build and return the result
        return RankedShopsResult(
            items=shops,
            total=total,
            limit=criteria.limit,
            offset=criteria.offset,
        )

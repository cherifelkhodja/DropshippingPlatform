"""Keyword Run Entity.

Represents a keyword search operation in the Meta Ads Library.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from ..value_objects import Country, ScanId


class KeywordRunStatus(Enum):
    """Enumeration of keyword run statuses."""

    PENDING = "pending"  # Waiting to execute
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed with error
    CANCELLED = "cancelled"  # Cancelled
    RATE_LIMITED = "rate_limited"  # Hit rate limit


@dataclass
class KeywordRunResult:
    """Value object representing keyword run results.

    Attributes:
        total_ads_found: Total number of ads found.
        unique_pages_found: Number of unique pages/advertisers.
        new_pages_found: Number of newly discovered pages.
        ads_processed: Number of ads processed.
        errors: List of error messages.
    """

    total_ads_found: int = 0
    unique_pages_found: int = 0
    new_pages_found: int = 0
    ads_processed: int = 0
    errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_results(self) -> bool:
        """Check if any results were found."""
        return self.total_ads_found > 0


@dataclass
class KeywordRun:
    """Entity representing a keyword search run.

    A KeywordRun represents a single keyword search operation against
    the Meta Ads Library, tracking search parameters and results.

    Attributes:
        id: Unique identifier (ScanId).
        keyword: The search keyword.
        country: Target country for the search.
        status: Current run status.
        result: Run results (when completed).
        page_limit: Maximum pages to fetch.
        pages_fetched: Number of pages actually fetched.
        priority: Run priority (higher = more urgent).
        retry_count: Number of retry attempts.
        max_retries: Maximum allowed retries.
        error_message: Error message (if failed).
        started_at: When the run started.
        completed_at: When the run completed.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    id: ScanId
    keyword: str
    country: Country
    status: KeywordRunStatus = KeywordRunStatus.PENDING
    result: Optional[KeywordRunResult] = None
    page_limit: int = 100
    pages_fetched: int = 0
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate keyword after initialization."""
        if not self.keyword or not self.keyword.strip():
            raise ValueError("Keyword cannot be empty")

    @classmethod
    def create(
        cls,
        keyword: str,
        country: Country,
        page_limit: int = 100,
        priority: int = 0,
    ) -> "KeywordRun":
        """Factory method to create a new KeywordRun.

        Args:
            keyword: The search keyword.
            country: Target country.
            page_limit: Maximum pages to fetch.
            priority: Run priority.

        Returns:
            A new KeywordRun instance.
        """
        now = datetime.utcnow()
        return cls(
            id=ScanId.generate(),
            keyword=keyword.strip(),
            country=country,
            page_limit=page_limit,
            priority=priority,
            created_at=now,
            updated_at=now,
        )

    def start(self) -> "KeywordRun":
        """Mark the run as started.

        Returns:
            Updated KeywordRun instance.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=KeywordRunStatus.RUNNING,
            result=None,
            page_limit=self.page_limit,
            pages_fetched=0,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=None,
            started_at=datetime.utcnow(),
            completed_at=None,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def update_progress(self, pages_fetched: int) -> "KeywordRun":
        """Update the fetch progress.

        Args:
            pages_fetched: Number of pages fetched so far.

        Returns:
            Updated KeywordRun instance.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=self.status,
            result=self.result,
            page_limit=self.page_limit,
            pages_fetched=pages_fetched,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=self.error_message,
            started_at=self.started_at,
            completed_at=self.completed_at,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def complete(self, result: KeywordRunResult) -> "KeywordRun":
        """Mark the run as completed with results.

        Args:
            result: The run results.

        Returns:
            Updated KeywordRun instance.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=KeywordRunStatus.COMPLETED,
            result=result,
            page_limit=self.page_limit,
            pages_fetched=self.pages_fetched,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=None,
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def fail(self, error_message: str) -> "KeywordRun":
        """Mark the run as failed.

        Args:
            error_message: The error message.

        Returns:
            Updated KeywordRun instance.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=KeywordRunStatus.FAILED,
            result=self.result,
            page_limit=self.page_limit,
            pages_fetched=self.pages_fetched,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=error_message,
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def rate_limit(self) -> "KeywordRun":
        """Mark the run as rate limited.

        Returns:
            Updated KeywordRun instance.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=KeywordRunStatus.RATE_LIMITED,
            result=self.result,
            page_limit=self.page_limit,
            pages_fetched=self.pages_fetched,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message="Rate limit exceeded",
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def retry(self) -> "KeywordRun":
        """Create a retry attempt.

        Returns:
            Updated KeywordRun instance with incremented retry count.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=KeywordRunStatus.PENDING,
            result=None,
            page_limit=self.page_limit,
            pages_fetched=0,
            priority=self.priority,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
            error_message=None,
            started_at=None,
            completed_at=None,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def cancel(self) -> "KeywordRun":
        """Cancel the run.

        Returns:
            Updated KeywordRun instance.
        """
        return KeywordRun(
            id=self.id,
            keyword=self.keyword,
            country=self.country,
            status=KeywordRunStatus.CANCELLED,
            result=self.result,
            page_limit=self.page_limit,
            pages_fetched=self.pages_fetched,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=None,
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def can_retry(self) -> bool:
        """Check if the run can be retried."""
        return (
            self.status in {KeywordRunStatus.FAILED, KeywordRunStatus.RATE_LIMITED}
            and self.retry_count < self.max_retries
        )

    def is_pending(self) -> bool:
        """Check if the run is pending."""
        return self.status == KeywordRunStatus.PENDING

    def is_running(self) -> bool:
        """Check if the run is running."""
        return self.status == KeywordRunStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if the run completed successfully."""
        return self.status == KeywordRunStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if the run failed."""
        return self.status in {
            KeywordRunStatus.FAILED,
            KeywordRunStatus.RATE_LIMITED,
        }

    def get_progress_percentage(self) -> float:
        """Get the fetch progress as a percentage.

        Returns:
            Progress percentage (0-100).
        """
        if self.page_limit == 0:
            return 0.0
        return (self.pages_fetched / self.page_limit) * 100

    def get_duration_seconds(self) -> Optional[float]:
        """Get the run duration in seconds.

        Returns:
            Duration in seconds, or None if not applicable.
        """
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, KeywordRun):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

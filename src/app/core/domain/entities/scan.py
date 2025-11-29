"""Scan Entity.

Represents a scan/analysis operation performed on a page.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from ..value_objects import ScanId


class ScanType(Enum):
    """Enumeration of scan types."""

    FULL = "full"                    # Complete analysis
    ADS_ONLY = "ads_only"            # Only ads detection
    SHOPIFY_DETECT = "shopify"       # Shopify detection only
    SITEMAP = "sitemap"              # Sitemap analysis
    PROFILE_UPDATE = "profile"       # Profile information update
    QUICK = "quick"                  # Quick/lightweight scan


class ScanStatus(Enum):
    """Enumeration of scan statuses."""

    PENDING = "pending"              # Waiting to start
    RUNNING = "running"              # Currently executing
    COMPLETED = "completed"          # Successfully completed
    FAILED = "failed"                # Failed with error
    CANCELLED = "cancelled"          # Cancelled by user/system
    TIMEOUT = "timeout"              # Timed out


@dataclass
class ScanResult:
    """Value object representing scan results.

    Attributes:
        ads_found: Number of ads found.
        new_ads: Number of new ads (not seen before).
        products_found: Number of products found.
        is_shopify: Whether Shopify was detected.
        errors: List of error messages.
        warnings: List of warning messages.
        metadata: Additional result metadata.
    """

    ads_found: int = 0
    new_ads: int = 0
    products_found: int = 0
    is_shopify: Optional[bool] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


@dataclass
class Scan:
    """Entity representing a scan operation.

    A Scan represents a single analysis operation performed on a page,
    tracking its status, duration, and results.

    Attributes:
        id: Unique identifier (ScanId).
        page_id: Reference to the scanned Page.
        scan_type: Type of scan performed.
        status: Current scan status.
        result: Scan results (when completed).
        priority: Scan priority (higher = more urgent).
        retry_count: Number of retry attempts.
        max_retries: Maximum allowed retries.
        error_message: Error message (if failed).
        started_at: When the scan started.
        completed_at: When the scan completed.
        created_at: Record creation timestamp.
        updated_at: Record update timestamp.
    """

    id: ScanId
    page_id: str
    scan_type: ScanType
    status: ScanStatus = ScanStatus.PENDING
    result: Optional[ScanResult] = None
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        page_id: str,
        scan_type: ScanType,
        priority: int = 0,
    ) -> "Scan":
        """Factory method to create a new Scan.

        Args:
            page_id: The page to scan.
            scan_type: Type of scan to perform.
            priority: Scan priority.

        Returns:
            A new Scan instance.
        """
        now = datetime.utcnow()
        return cls(
            id=ScanId.generate(),
            page_id=page_id,
            scan_type=scan_type,
            status=ScanStatus.PENDING,
            priority=priority,
            created_at=now,
            updated_at=now,
        )

    def start(self) -> "Scan":
        """Mark the scan as started.

        Returns:
            Updated Scan instance.
        """
        return Scan(
            id=self.id,
            page_id=self.page_id,
            scan_type=self.scan_type,
            status=ScanStatus.RUNNING,
            result=self.result,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=None,
            started_at=datetime.utcnow(),
            completed_at=None,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def complete(self, result: ScanResult) -> "Scan":
        """Mark the scan as completed with results.

        Args:
            result: The scan results.

        Returns:
            Updated Scan instance.
        """
        return Scan(
            id=self.id,
            page_id=self.page_id,
            scan_type=self.scan_type,
            status=ScanStatus.COMPLETED,
            result=result,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=None,
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def fail(self, error_message: str) -> "Scan":
        """Mark the scan as failed.

        Args:
            error_message: The error message.

        Returns:
            Updated Scan instance.
        """
        return Scan(
            id=self.id,
            page_id=self.page_id,
            scan_type=self.scan_type,
            status=ScanStatus.FAILED,
            result=self.result,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=error_message,
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def retry(self) -> "Scan":
        """Create a retry attempt.

        Returns:
            Updated Scan instance with incremented retry count.
        """
        return Scan(
            id=self.id,
            page_id=self.page_id,
            scan_type=self.scan_type,
            status=ScanStatus.PENDING,
            result=None,
            priority=self.priority,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
            error_message=None,
            started_at=None,
            completed_at=None,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def cancel(self) -> "Scan":
        """Cancel the scan.

        Returns:
            Updated Scan instance.
        """
        return Scan(
            id=self.id,
            page_id=self.page_id,
            scan_type=self.scan_type,
            status=ScanStatus.CANCELLED,
            result=self.result,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message=None,
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def timeout(self) -> "Scan":
        """Mark the scan as timed out.

        Returns:
            Updated Scan instance.
        """
        return Scan(
            id=self.id,
            page_id=self.page_id,
            scan_type=self.scan_type,
            status=ScanStatus.TIMEOUT,
            result=self.result,
            priority=self.priority,
            retry_count=self.retry_count,
            max_retries=self.max_retries,
            error_message="Scan timed out",
            started_at=self.started_at,
            completed_at=datetime.utcnow(),
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
        )

    def can_retry(self) -> bool:
        """Check if the scan can be retried."""
        return (
            self.status in {ScanStatus.FAILED, ScanStatus.TIMEOUT}
            and self.retry_count < self.max_retries
        )

    def is_pending(self) -> bool:
        """Check if the scan is pending."""
        return self.status == ScanStatus.PENDING

    def is_running(self) -> bool:
        """Check if the scan is running."""
        return self.status == ScanStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if the scan completed successfully."""
        return self.status == ScanStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if the scan failed."""
        return self.status in {ScanStatus.FAILED, ScanStatus.TIMEOUT}

    def is_terminal(self) -> bool:
        """Check if the scan is in a terminal state."""
        return self.status in {
            ScanStatus.COMPLETED,
            ScanStatus.CANCELLED,
            ScanStatus.FAILED,
            ScanStatus.TIMEOUT,
        } and not self.can_retry()

    def get_duration_seconds(self) -> Optional[float]:
        """Get the scan duration in seconds.

        Returns:
            Duration in seconds, or None if not applicable.
        """
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Scan):
            return self.id == other.id
        return False

    def __hash__(self) -> int:
        return hash(self.id)

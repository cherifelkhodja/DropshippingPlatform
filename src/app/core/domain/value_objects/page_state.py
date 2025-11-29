"""Page State Value Object.

Represents the current state of a tracked page in the system.
"""

from dataclasses import dataclass
from enum import Enum

from ..errors import InvalidPageStateError


class PageStatus(Enum):
    """Enumeration of possible page states."""

    # Initial discovery states
    DISCOVERED = "discovered"  # Page found but not yet analyzed
    PENDING_ANALYSIS = "pending"  # Queued for analysis

    # Analysis states
    ANALYZING = "analyzing"  # Currently being analyzed
    ANALYZED = "analyzed"  # Analysis complete

    # Verification states
    VERIFIED_SHOPIFY = "verified"  # Confirmed as Shopify store
    NOT_SHOPIFY = "not_shopify"  # Confirmed as not Shopify

    # Active monitoring states
    ACTIVE = "active"  # Actively monitored
    INACTIVE = "inactive"  # No longer actively monitored

    # Error states
    ERROR = "error"  # Error during processing
    UNREACHABLE = "unreachable"  # Site cannot be reached

    # Removal states
    ARCHIVED = "archived"  # Archived for historical purposes
    DELETED = "deleted"  # Marked for deletion

    @classmethod
    def from_string(cls, value: str) -> "PageStatus":
        """Create PageStatus from string value.

        Args:
            value: The status string.

        Returns:
            The corresponding PageStatus enum.

        Raises:
            InvalidPageStateError: If the value is not a valid status.
        """
        normalized = value.lower().strip()
        for status in cls:
            if status.value == normalized:
                return status
        raise InvalidPageStateError(value)


# Valid state transitions
VALID_TRANSITIONS: dict[PageStatus, frozenset[PageStatus]] = {
    PageStatus.DISCOVERED: frozenset(
        {
            PageStatus.PENDING_ANALYSIS,
            PageStatus.ERROR,
            PageStatus.DELETED,
        }
    ),
    PageStatus.PENDING_ANALYSIS: frozenset(
        {
            PageStatus.ANALYZING,
            PageStatus.ERROR,
            PageStatus.DELETED,
        }
    ),
    PageStatus.ANALYZING: frozenset(
        {
            PageStatus.ANALYZED,
            PageStatus.ERROR,
            PageStatus.UNREACHABLE,
        }
    ),
    PageStatus.ANALYZED: frozenset(
        {
            PageStatus.VERIFIED_SHOPIFY,
            PageStatus.NOT_SHOPIFY,
            PageStatus.ERROR,
        }
    ),
    PageStatus.VERIFIED_SHOPIFY: frozenset(
        {
            PageStatus.ACTIVE,
            PageStatus.INACTIVE,
            PageStatus.ERROR,
            PageStatus.UNREACHABLE,
        }
    ),
    PageStatus.NOT_SHOPIFY: frozenset(
        {
            PageStatus.ARCHIVED,
            PageStatus.DELETED,
        }
    ),
    PageStatus.ACTIVE: frozenset(
        {
            PageStatus.INACTIVE,
            PageStatus.ERROR,
            PageStatus.UNREACHABLE,
            PageStatus.ARCHIVED,
        }
    ),
    PageStatus.INACTIVE: frozenset(
        {
            PageStatus.ACTIVE,
            PageStatus.ARCHIVED,
            PageStatus.DELETED,
        }
    ),
    PageStatus.ERROR: frozenset(
        {
            PageStatus.PENDING_ANALYSIS,
            PageStatus.ARCHIVED,
            PageStatus.DELETED,
        }
    ),
    PageStatus.UNREACHABLE: frozenset(
        {
            PageStatus.PENDING_ANALYSIS,
            PageStatus.ARCHIVED,
            PageStatus.DELETED,
        }
    ),
    PageStatus.ARCHIVED: frozenset(
        {
            PageStatus.DELETED,
            PageStatus.ACTIVE,  # Can be reactivated
        }
    ),
    PageStatus.DELETED: frozenset(),  # Terminal state
}


@dataclass(frozen=True)
class PageState:
    """Immutable page state value object with transition validation.

    Attributes:
        status: The current PageStatus.
    """

    status: PageStatus

    def __post_init__(self) -> None:
        """Validate page state after initialization."""
        if not isinstance(self.status, PageStatus):
            raise InvalidPageStateError(str(self.status))

    @classmethod
    def initial(cls) -> "PageState":
        """Create initial page state (DISCOVERED)."""
        return cls(status=PageStatus.DISCOVERED)

    @classmethod
    def from_string(cls, value: str) -> "PageState":
        """Create PageState from string value."""
        return cls(status=PageStatus.from_string(value))

    def can_transition_to(self, target: PageStatus) -> bool:
        """Check if transition to target state is valid.

        Args:
            target: The target PageStatus.

        Returns:
            True if the transition is allowed, False otherwise.
        """
        allowed = VALID_TRANSITIONS.get(self.status, frozenset())
        return target in allowed

    def transition_to(self, target: PageStatus) -> "PageState":
        """Create a new PageState with the target status.

        Args:
            target: The target PageStatus.

        Returns:
            A new PageState with the target status.

        Raises:
            InvalidPageStateError: If the transition is not allowed.
        """
        if not self.can_transition_to(target):
            raise InvalidPageStateError(
                f"Cannot transition from {self.status.value} to {target.value}"
            )
        return PageState(status=target)

    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self.status == PageStatus.DELETED

    def is_active(self) -> bool:
        """Check if the page is in an active state."""
        return self.status in {PageStatus.ACTIVE, PageStatus.VERIFIED_SHOPIFY}

    def is_error(self) -> bool:
        """Check if the page is in an error state."""
        return self.status in {PageStatus.ERROR, PageStatus.UNREACHABLE}

    def requires_analysis(self) -> bool:
        """Check if the page needs analysis."""
        return self.status in {
            PageStatus.DISCOVERED,
            PageStatus.PENDING_ANALYSIS,
        }

    def __str__(self) -> str:
        return self.status.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PageState):
            return self.status == other.status
        return False

    def __hash__(self) -> int:
        return hash(self.status)

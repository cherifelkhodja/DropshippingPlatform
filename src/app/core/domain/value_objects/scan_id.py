"""Scan ID Value Object.

Represents a validated unique identifier for scans.
"""

from dataclasses import dataclass
import re
import uuid

from ..errors import InvalidScanIdError


@dataclass(frozen=True)
class ScanId:
    """Immutable scan ID value object with UUID validation.

    Attributes:
        value: The UUID string representation.
    """

    value: str

    # UUID v4 pattern
    _UUID_PATTERN: re.Pattern[str] = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )

    def __post_init__(self) -> None:
        """Validate scan ID format after initialization."""
        if not self.value:
            raise InvalidScanIdError("")

        normalized = self.value.lower().strip()

        if not self._UUID_PATTERN.match(normalized):
            raise InvalidScanIdError(self.value)

        # Store normalized (lowercase) version
        object.__setattr__(self, "value", normalized)

    @classmethod
    def generate(cls) -> "ScanId":
        """Generate a new unique ScanId.

        Returns:
            A new ScanId with a generated UUID v4.
        """
        return cls(value=str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> "ScanId":
        """Create a ScanId from a string value.

        Args:
            value: The UUID string.

        Returns:
            A new ScanId instance.

        Raises:
            InvalidScanIdError: If the value is not a valid UUID.
        """
        return cls(value=value)

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ScanId):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

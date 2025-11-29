"""URL Value Object.

Represents a validated URL with domain extraction capabilities.
"""

from dataclasses import dataclass
import re
from typing import Optional

from ..errors import InvalidUrlError


@dataclass(frozen=True)
class Url:
    """Immutable URL value object with validation.

    Attributes:
        value: The full URL string.
    """

    value: str

    # URL pattern supporting http/https with domain validation
    _URL_PATTERN: re.Pattern[str] = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",  # path
        re.IGNORECASE,
    )

    def __post_init__(self) -> None:
        """Validate URL format after initialization."""
        if not self.value:
            raise InvalidUrlError(self.value, "URL cannot be empty")

        if not self._URL_PATTERN.match(self.value):
            raise InvalidUrlError(self.value, "Invalid URL format")

    @property
    def domain(self) -> str:
        """Extract the domain from the URL.

        Returns:
            The domain portion of the URL (e.g., 'example.com').
        """
        # Remove protocol
        without_protocol = re.sub(r"^https?://", "", self.value)
        # Get domain (before first / or end)
        domain = without_protocol.split("/")[0]
        # Remove port if present
        domain = domain.split(":")[0]
        return domain

    @property
    def is_https(self) -> bool:
        """Check if the URL uses HTTPS."""
        return self.value.startswith("https://")

    @property
    def path(self) -> Optional[str]:
        """Extract the path from the URL.

        Returns:
            The path portion of the URL, or None if no path.
        """
        without_protocol = re.sub(r"^https?://", "", self.value)
        parts = without_protocol.split("/", 1)
        if len(parts) > 1 and parts[1]:
            return "/" + parts[1]
        return None

    def __str__(self) -> str:
        return self.value

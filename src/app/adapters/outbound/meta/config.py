"""Meta Ads API Configuration.

Configuration settings for Meta Ads Library API client.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MetaAdsConfig:
    """Configuration for Meta Ads API client.

    Attributes:
        access_token: Meta API access token.
        base_url: Base URL for Meta Graph API.
        api_version: API version string (e.g., "v18.0").
        timeout_seconds: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_base_delay: Base delay between retries in seconds.
    """

    access_token: str
    base_url: str = "https://graph.facebook.com"
    api_version: str = "v18.0"
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_base_delay: float = 1.0

    @property
    def ads_archive_url(self) -> str:
        """Get the full URL for ads_archive endpoint."""
        return f"{self.base_url}/{self.api_version}/ads_archive"

    @classmethod
    def from_env(
        cls,
        access_token: str,
        base_url: str | None = None,
        api_version: str | None = None,
    ) -> "MetaAdsConfig":
        """Create configuration from environment values.

        Args:
            access_token: Meta API access token (required).
            base_url: Optional custom base URL.
            api_version: Optional API version override.

        Returns:
            MetaAdsConfig instance.
        """
        return cls(
            access_token=access_token,
            base_url=base_url or "https://graph.facebook.com",
            api_version=api_version or "v18.0",
        )

"""Runtime Settings.

Pydantic v2 settings for application configuration.
Auto-loads from environment variables and .env files.
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: str = Field(
        default="postgresql+asyncpg://dropshipping:dropshipping@localhost:5432/dropshipping",
        alias="DATABASE_URL",
    )
    pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    echo: bool = Field(default=False, alias="DB_ECHO")


class MetaAdsSettings(BaseSettings):
    """Meta Ads API settings."""

    model_config = SettingsConfigDict(
        env_prefix="META_ADS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    access_token: SecretStr = Field(default=SecretStr(""))
    base_url: str = Field(default="https://graph.facebook.com")
    api_version: str = Field(default="v18.0")
    timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)


class ScraperSettings(BaseSettings):
    """HTTP scraper settings."""

    model_config = SettingsConfigDict(
        env_prefix="SCRAPER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    default_timeout: int = Field(default=15)
    max_retries: int = Field(default=3)
    retry_base_delay: float = Field(default=1.0)
    user_agent: str = Field(
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    )


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = Field(default="Dropshipping Platform")
    version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    meta_ads: MetaAdsSettings = Field(default_factory=MetaAdsSettings)
    scraper: ScraperSettings = Field(default_factory=ScraperSettings)


@lru_cache
def get_settings() -> AppSettings:
    """Get cached application settings.

    Returns:
        AppSettings instance loaded from environment.
    """
    return AppSettings()

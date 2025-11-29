"""Tests for admin API authentication.

Verifies the admin API key authentication works correctly.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.app.api.dependencies import get_admin_auth


def _create_settings_mock(admin_api_key: str | None) -> MagicMock:
    """Create a mock settings object with security settings."""
    settings = MagicMock()
    security = MagicMock()
    security.admin_api_key = admin_api_key
    settings.security = security
    return settings


class TestGetAdminAuth:
    """Tests for get_admin_auth dependency."""

    def test_no_auth_required_when_key_not_configured(self) -> None:
        """When admin_api_key is None, no authentication is required."""
        settings = _create_settings_mock(admin_api_key=None)

        # Should not raise
        get_admin_auth(settings=settings, x_admin_api_key=None)

    def test_auth_required_when_key_configured(self) -> None:
        """When admin_api_key is set, header must match."""
        settings = _create_settings_mock(admin_api_key="secret-key-123")

        # Missing header should raise
        with pytest.raises(HTTPException) as exc_info:
            get_admin_auth(settings=settings, x_admin_api_key=None)

        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail

    def test_wrong_key_raises_401(self) -> None:
        """Wrong API key raises 401 Unauthorized."""
        settings = _create_settings_mock(admin_api_key="secret-key-123")

        with pytest.raises(HTTPException) as exc_info:
            get_admin_auth(settings=settings, x_admin_api_key="wrong-key")

        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail

    def test_correct_key_passes(self) -> None:
        """Correct API key passes authentication."""
        settings = _create_settings_mock(admin_api_key="secret-key-123")

        # Should not raise
        get_admin_auth(settings=settings, x_admin_api_key="secret-key-123")

    def test_empty_string_key_treated_as_no_key(self) -> None:
        """Empty string for admin_api_key is treated as no key configured."""
        settings = _create_settings_mock(admin_api_key="")

        # Empty string is falsy, so should pass without header
        get_admin_auth(settings=settings, x_admin_api_key=None)

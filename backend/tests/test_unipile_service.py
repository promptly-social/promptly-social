"""
Unit tests for Unipile integration in ProfileService.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import UUID

from app.core.config import settings
from app.services.profile import ProfileService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def profile_service(mock_db):
    """Create ProfileService instance with mocked database."""
    return ProfileService(mock_db)


class TestUnipileFeatureFlag:
    """Test Unipile feature flag functionality in ProfileService."""

    def test_create_linkedin_authorization_url_native(self, profile_service):
        """Test native LinkedIn authorization URL creation."""
        with patch.object(settings, "use_unipile_for_linkedin", False):
            with patch.object(settings, "linkedin_client_id", "test_client_id"):
                with patch.object(settings, "frontend_url", "http://localhost:3000"):
                    url = profile_service.create_linkedin_authorization_url(
                        "test_state"
                    )
                    assert "linkedin.com/oauth/v2/authorization" in url
                    assert "client_id=test_client_id" in url
                    assert "state=test_state" in url

    @patch("httpx.Client")
    def test_create_linkedin_authorization_url_unipile(
        self, mock_httpx_client, profile_service
    ):
        """Test Unipile LinkedIn authorization URL creation."""
        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"url": "https://unipile.hosted.auth/test123"}

        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client_instance

        with patch.object(settings, "use_unipile_for_linkedin", True):
            with patch.object(settings, "unipile_dsn", "test_dsn"):
                with patch.object(settings, "unipile_access_token", "test_token"):
                    with patch.object(
                        settings, "frontend_url", "http://localhost:3000"
                    ):
                        with patch.object(
                            settings, "backend_url", "http://localhost:8000"
                        ):
                            url = profile_service.create_linkedin_authorization_url(
                                "test_state"
                            )
                            assert url == "https://unipile.hosted.auth/test123"

    def test_create_linkedin_authorization_url_native_missing_config(
        self, profile_service
    ):
        """Test native LinkedIn URL creation fails with missing config."""
        with patch.object(settings, "use_unipile_for_linkedin", False):
            with patch.object(settings, "linkedin_client_id", None):
                with pytest.raises(
                    ValueError, match="LINKEDIN_CLIENT_ID is not configured"
                ):
                    profile_service.create_linkedin_authorization_url("test_state")

    def test_create_linkedin_authorization_url_unipile_missing_config(
        self, profile_service
    ):
        """Test Unipile URL creation fails with missing config."""
        with patch.object(settings, "use_unipile_for_linkedin", True):
            with patch.object(settings, "unipile_dsn", None):
                with pytest.raises(
                    ValueError,
                    match="UNIPILE_DSN and UNIPILE_ACCESS_TOKEN are not configured",
                ):
                    profile_service.create_linkedin_authorization_url("test_state")


class TestUnipileSharing:
    """Test Unipile sharing functionality."""

    @pytest.mark.asyncio
    async def test_share_on_linkedin_detects_auth_method(
        self, profile_service, mock_db
    ):
        """Test that share_on_linkedin correctly detects auth method from connection data."""
        # Mock connection with native auth method
        mock_connection = MagicMock()
        mock_connection.connection_data = {
            "auth_method": "native",
            "access_token": "test_token",
        }

        # Setup async mock for get_social_connection
        profile_service.get_social_connection = AsyncMock(return_value=mock_connection)
        profile_service._share_via_native_linkedin = AsyncMock(
            return_value={"share_id": "123", "method": "native"}
        )

        result = await profile_service.share_on_linkedin(
            UUID("12345678-1234-5678-1234-567812345678"), "Test post"
        )

        assert result["method"] == "native"
        profile_service._share_via_native_linkedin.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_on_linkedin_uses_unipile_method(
        self, profile_service, mock_db
    ):
        """Test that share_on_linkedin uses Unipile method when connection has unipile auth method."""
        # Mock connection with Unipile auth method
        mock_connection = MagicMock()
        mock_connection.connection_data = {
            "auth_method": "unipile",
            "account_id": "account123",
            "unipile_account_id": "account123",
        }

        profile_service.get_social_connection = AsyncMock(return_value=mock_connection)
        profile_service._share_via_unipile = AsyncMock(
            return_value={"share_id": "456", "method": "unipile"}
        )

        result = await profile_service.share_on_linkedin(
            UUID("12345678-1234-5678-1234-567812345678"), "Test post"
        )

        assert result["method"] == "unipile"
        profile_service._share_via_unipile.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_on_linkedin_defaults_to_native(self, profile_service, mock_db):
        """Test that share_on_linkedin defaults to native method when auth_method is not specified."""
        # Mock connection without auth_method specified
        mock_connection = MagicMock()
        mock_connection.connection_data = {
            "access_token": "test_token"
        }  # No auth_method specified

        profile_service.get_social_connection = AsyncMock(return_value=mock_connection)
        profile_service._share_via_native_linkedin = AsyncMock(
            return_value={"share_id": "789", "method": "native"}
        )

        result = await profile_service.share_on_linkedin(
            UUID("12345678-1234-5678-1234-567812345678"), "Test post"
        )

        assert result["method"] == "native"
        profile_service._share_via_native_linkedin.assert_called_once()


class TestUnipileConfiguration:
    """Test Unipile configuration validation."""

    def test_configuration_check_native_valid(self):
        """Test configuration check for native LinkedIn OAuth."""
        with patch.object(settings, "use_unipile_for_linkedin", False):
            with patch.object(settings, "linkedin_client_id", "client_id"):
                with patch.object(settings, "linkedin_client_secret", "client_secret"):
                    # This would be used in the auth-info endpoint
                    configured = bool(
                        settings.linkedin_client_id and settings.linkedin_client_secret
                    )
                    assert configured is True

    def test_configuration_check_native_invalid(self):
        """Test configuration check for native LinkedIn OAuth with missing credentials."""
        with patch.object(settings, "use_unipile_for_linkedin", False):
            with patch.object(settings, "linkedin_client_id", None):
                with patch.object(settings, "linkedin_client_secret", None):
                    configured = bool(
                        settings.linkedin_client_id and settings.linkedin_client_secret
                    )
                    assert configured is False

    def test_configuration_check_unipile_valid(self):
        """Test configuration check for Unipile."""
        with patch.object(settings, "use_unipile_for_linkedin", True):
            with patch.object(settings, "unipile_dsn", "test_dsn"):
                with patch.object(settings, "unipile_access_token", "test_token"):
                    configured = bool(
                        settings.unipile_dsn and settings.unipile_access_token
                    )
                    assert configured is True

    def test_configuration_check_unipile_invalid(self):
        """Test configuration check for Unipile with missing credentials."""
        with patch.object(settings, "use_unipile_for_linkedin", True):
            with patch.object(settings, "unipile_dsn", None):
                with patch.object(settings, "unipile_access_token", None):
                    configured = bool(
                        settings.unipile_dsn and settings.unipile_access_token
                    )
                    assert configured is False

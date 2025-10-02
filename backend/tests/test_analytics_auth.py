"""
Tests for LinkedIn Analytics authentication functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.core.config import settings


@pytest.fixture
def mock_analytics_settings():
    """Mock analytics settings."""
    with patch.object(settings, 'linkedin_analytics_client_id', 'test_analytics_client_id'), \
         patch.object(settings, 'linkedin_analytics_client_secret', 'test_analytics_secret'):
        yield


class TestLinkedInAnalyticsAuth:
    """Test LinkedIn Analytics authentication logic."""

    @pytest.mark.asyncio
    async def test_analytics_auth_url_generation(self, mock_analytics_settings):
        """Test analytics auth URL generation."""
        from app.services.auth import AuthService
        from sqlalchemy.ext.asyncio import AsyncSession

        # Mock database session
        mock_db = MagicMock(spec=AsyncSession)
        auth_service = AuthService(mock_db)

        # Test URL generation
        result = await auth_service.initiate_linkedin_analytics_auth(
            "http://localhost:8080/auth/linkedin-analytics-callback",
            "profile"
        )

        # Verify the result
        assert result["error"] is None
        assert "url" in result
        assert "r_member_postAnalytics" in result["url"]
        assert "r_member_profileAnalytics" in result["url"]
        assert "test_analytics_client_id" in result["url"]

    @pytest.mark.asyncio
    async def test_analytics_auth_missing_config(self):
        """Test analytics auth with missing configuration."""
        from app.services.auth import AuthService
        from sqlalchemy.ext.asyncio import AsyncSession

        # Mock database session
        mock_db = MagicMock(spec=AsyncSession)
        auth_service = AuthService(mock_db)

        # Ensure analytics client ID is None
        with patch.object(settings, 'linkedin_analytics_client_id', None):
            # Test with missing config
            result = await auth_service.initiate_linkedin_analytics_auth(
                "http://localhost:8080/auth/linkedin-analytics-callback",
                "profile"
            )

            # Should return error when config is missing
            assert result["error"] == "LinkedIn Analytics client ID not configured"
            assert result["url"] is None

    @pytest.mark.asyncio
    async def test_analytics_auth_state_encoding(self, mock_analytics_settings):
        """Test that user_id is properly encoded in state parameter."""
        from app.services.auth import AuthService
        from sqlalchemy.ext.asyncio import AsyncSession

        # Mock database session
        mock_db = MagicMock(spec=AsyncSession)
        auth_service = AuthService(mock_db)

        # Test URL generation with user_id
        result = await auth_service.initiate_linkedin_analytics_auth(
            "http://localhost:8080/auth/linkedin-analytics-callback",
            "profile",
            "test-user-id-123"
        )

        # Verify the result
        assert result["error"] is None
        assert "url" in result
        assert "state" in result

        # Verify state contains user_id
        state = result["state"]
        state_parts = state.split('_')
        assert len(state_parts) >= 2
        assert state_parts[1] == "test-user-id-123"  # user_id should be second part


class TestLinkedInAnalyticsService:
    """Test LinkedIn Analytics service methods."""

    @pytest.mark.asyncio
    @patch('app.services.linkedin_service.LinkedInService.exchange_code_for_analytics_token')
    async def test_analytics_token_exchange(self, mock_exchange_token):
        """Test analytics token exchange without calling get_user_info."""
        from app.services.linkedin_service import LinkedInService

        # Mock token exchange response
        mock_exchange_token.return_value = {
            "access_token": "analytics_access_token",
            "refresh_token": "analytics_refresh_token",
            "expires_in": 3600,
            "scope": "r_member_postAnalytics r_member_profileAnalytics"
        }

        # Test the method
        result = await LinkedInService.exchange_code_for_analytics_token(
            "test_code",
            "http://localhost:8080/auth/linkedin-analytics-callback"
        )

        # Verify the result
        assert result["access_token"] == "analytics_access_token"
        assert result["scope"] == "r_member_postAnalytics r_member_profileAnalytics"

        # Verify the mock was called correctly
        mock_exchange_token.assert_called_once_with(
            "test_code",
            "http://localhost:8080/auth/linkedin-analytics-callback"
        )

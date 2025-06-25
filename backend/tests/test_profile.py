"""
Tests for profile services and endpoints.
Comprehensive test coverage for all profile-related functionality.
"""

import os
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_async_db
from app.main import app
from app.models.profile import SocialConnection, UserPreferences, WritingStyleAnalysis
from app.routers.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.profile import SocialConnectionUpdate, UserPreferencesUpdate
from app.services.profile import ProfileService

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_profile.db"


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create test database session."""
    # Remove existing test database
    if os.path.exists("./test_profile.db"):
        os.remove("./test_profile.db")

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    # Clean up
    await engine.dispose()
    if os.path.exists("./test_profile.db"):
        os.remove("./test_profile.db")


@pytest.fixture
def test_user():
    """Create a test user."""
    return UserResponse(
        id=uuid4(),
        email="test@example.com",
        is_active=True,
        is_verified=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def profile_service(test_db):
    """Create ProfileService instance."""
    return ProfileService(test_db)


class TestProfileService:
    """Test cases for ProfileService."""

    @pytest.mark.asyncio
    async def test_user_preferences_operations(self, profile_service, test_user):
        """Test user preferences CRUD operations."""
        # Create preferences
        preferences_data = UserPreferencesUpdate(
            topics_of_interest=["AI", "Technology"],
            websites=["example.com", "test.com"],
            bio="this is the user's bio",
        )
        preferences = await profile_service.upsert_user_preferences(
            test_user.id, preferences_data
        )

        assert preferences.topics_of_interest == ["AI", "Technology"]
        assert preferences.websites == ["example.com", "test.com"]
        assert preferences.bio == "this is the user's bio"

        # Update preferences
        update_data = UserPreferencesUpdate(
            topics_of_interest=["AI", "Technology", "Business"]
        )
        updated = await profile_service.upsert_user_preferences(
            test_user.id, update_data
        )

        assert len(updated.topics_of_interest) == 3
        assert "Business" in updated.topics_of_interest

    @pytest.mark.asyncio
    async def test_social_connections_operations(self, profile_service, test_user):
        """Test social connections CRUD operations."""
        # Create connection
        connection_data = SocialConnectionUpdate(
            platform_username="testuser",
            is_active=True,
            connection_data={"access_token": "test_token"},
        )
        connection = await profile_service.upsert_social_connection(
            test_user.id, "linkedin", connection_data
        )

        assert connection.platform == "linkedin"
        assert connection.platform_username == "testuser"
        assert connection.is_active is True

        # Get connection
        retrieved = await profile_service.get_social_connection(
            test_user.id, "linkedin"
        )
        assert retrieved.id == connection.id

        # Get all connections
        all_connections = await profile_service.get_social_connections(test_user.id)
        assert len(all_connections) == 1

    @pytest.mark.asyncio
    async def test_disconnect_social_connection(self, profile_service, test_user):
        """Test disconnecting a social connection."""
        # Create a connection first
        connection_data = SocialConnectionUpdate(
            platform_username="testuser",
            is_active=True,
            connection_data={"access_token": "test_token", "auth_method": "native"},
        )
        connection = await profile_service.upsert_social_connection(
            test_user.id, "linkedin", connection_data
        )
        assert connection.is_active is True
        assert connection.connection_data is not None

        # Disconnect the connection
        disconnect_data = SocialConnectionUpdate(is_active=False)
        disconnected = await profile_service.upsert_social_connection(
            test_user.id, "linkedin", disconnect_data
        )

        assert disconnected.is_active is False
        assert disconnected.connection_data is None
        assert disconnected.platform_username is None

    @pytest.mark.asyncio
    async def test_disconnect_unipile_connection(self, profile_service, test_user):
        """Test disconnecting a Unipile connection."""
        # Create a Unipile connection first
        connection_data = SocialConnectionUpdate(
            platform_username="testuser",
            is_active=True,
            connection_data={
                "access_token": "test_token",
                "auth_method": "unipile",
                "account_id": "test_account_id",
            },
        )
        connection = await profile_service.upsert_social_connection(
            test_user.id, "linkedin", connection_data
        )
        assert connection.is_active is True
        assert connection.connection_data is not None

        # Mock the Unipile API call
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = (
                mock_client.return_value.__aenter__.return_value.delete.return_value
            )
            mock_response.raise_for_status.return_value = None

            # Disconnect the connection
            disconnect_data = SocialConnectionUpdate(is_active=False)
            disconnected = await profile_service.upsert_social_connection(
                test_user.id, "linkedin", disconnect_data
            )

            assert disconnected.is_active is False
            assert disconnected.connection_data is None
            assert disconnected.platform_username is None

            # Verify the Unipile API was called
            mock_client.return_value.__aenter__.return_value.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_writing_style_analysis_operations(self, profile_service, test_user):
        """Test writing style analysis CRUD operations."""
        # Create analysis - updated to match service signature
        analysis_data_str = "this is the writing style analysis data"
        analysis = await profile_service.upsert_writing_style_analysis(
            test_user.id, "linkedin", analysis_data_str
        )

        assert analysis.source == "linkedin"
        assert analysis.analysis_data == "this is the writing style analysis data"

        # Get analysis
        retrieved = await profile_service.get_writing_style_analysis(
            test_user.id, "linkedin"
        )
        assert retrieved.id == analysis.id


class TestProfileEndpoints:
    """Test cases for profile API endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user."""
        user = UserResponse(
            id=uuid4(),
            email="test@example.com",
            is_active=True,
            is_verified=True,
            created_at=datetime.now(timezone.utc),
        )

        async def mock_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = mock_get_current_user
        yield user
        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_db(self, test_db):
        """Mock database dependency."""

        async def mock_get_db():
            yield test_db

        app.dependency_overrides[get_async_db] = mock_get_db
        yield test_db
        app.dependency_overrides.clear()

    def test_get_user_preferences_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test GET /profile/preferences endpoint."""
        with patch(
            "app.services.profile.ProfileService.get_user_preferences"
        ) as mock_service:
            mock_service.return_value = None

            response = test_client.get(
                "/api/v1/profile/preferences",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "topics_of_interest" in data

    def test_update_user_preferences_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test PUT /profile/preferences endpoint."""
        with patch(
            "app.services.profile.ProfileService.upsert_user_preferences"
        ) as mock_service:
            mock_preferences = UserPreferences(
                id=uuid4(),
                user_id=mock_current_user.id,
                topics_of_interest=["AI", "Tech"],
                websites=["example.com"],
                bio="this is the user's bio",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_service.return_value = mock_preferences

            preferences_data = {
                "topics_of_interest": ["AI", "Tech"],
                "websites": ["example.com"],
                "bio": "this is the user's bio",
            }

            response = test_client.put(
                "/api/v1/profile/preferences",
                json=preferences_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["topics_of_interest"] == ["AI", "Tech"]
            assert data["bio"] == "this is the user's bio"

    def test_get_social_connections_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test GET /profile/social-connections endpoint."""
        with patch(
            "app.services.profile.ProfileService.get_social_connections"
        ) as mock_service:
            mock_service.return_value = []

            response = test_client.get(
                "/api/v1/profile/social-connections",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)

    def test_run_writing_style_analysis_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-writing-style endpoint."""
        with patch(
            "app.services.profile.ProfileService.analyze_linkedin"
        ) as mock_analyze_linkedin:
            mock_connection = SocialConnection(
                id=uuid4(),
                user_id=mock_current_user.id,
                platform="linkedin",
                platform_username="testuser",
                is_active=True,
                analysis_status="in_progress",
                analysis_started_at=datetime.now(timezone.utc),
            )
            mock_analyze_linkedin.return_value = mock_connection

            response = test_client.post(
                "/api/v1/profile/writing-analysis/linkedin",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_connected"] is True
            mock_analyze_linkedin.assert_called_once_with(
                mock_current_user.id, ["writing_style"]
            )

    def test_run_substack_analysis_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack endpoint."""
        with (
            patch(
                "app.services.profile.ProfileService.analyze_substack"
            ) as mock_service,
            patch("google.oauth2.id_token.fetch_id_token") as mock_fetch_token,
        ):
            mock_service.return_value = SocialConnection(
                id=uuid4(),
                user_id=mock_current_user.id,
                platform="substack",
                platform_username="testuser",
                is_active=True,
                analysis_status="in_progress",
                analysis_started_at=datetime.now(timezone.utc),
            )
            mock_fetch_token.return_value = "mock_token"
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.gcp_analysis_function_url = "test-url"

                response = test_client.post(
                    "/api/v1/profile/analyze-substack",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["is_analyzing"] is True
                mock_service.assert_called_once_with(
                    mock_current_user.id, ["bio", "interests"]
                )

    def test_run_substack_analysis_no_connection(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack when no Substack connection exists."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            mock_get_connection.return_value = None

            response = test_client.post(
                "/api/v1/profile/analyze-substack",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "Substack connection not found" in data["detail"]

    def test_run_substack_analysis_gcp_failure(
        self, test_client, mock_current_user, mock_db
    ):
        """Test running Substack analysis with a GCP trigger failure."""
        with (
            patch(
                "app.services.profile.ProfileService.get_social_connection_for_analysis"
            ) as mock_get_connection,
            patch("google.oauth2.id_token.fetch_id_token") as mock_fetch_token,
            patch("app.core.config.settings") as mock_settings,
        ):
            mock_settings.gcp_analysis_function_url = "test-url"

            mock_connection = SocialConnection(
                id=uuid4(),
                user_id=mock_current_user.id,
                platform="substack",
                platform_username="testuser",
                is_active=True,
                analysis_status="not_started",
            )
            mock_get_connection.return_value = mock_connection
            mock_fetch_token.side_effect = Exception("GCP function failed")

            response = test_client.post(
                "/api/v1/profile/analyze-substack",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "GCP function failed" in response.json()["detail"]

    def test_run_substack_analysis_database_error(
        self, test_client, mock_current_user, mock_db
    ):
        """Test running Substack analysis with a database error."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            with patch.object(mock_db, "commit") as mock_commit:
                with patch.object(mock_db, "rollback") as mock_rollback:
                    # Mock valid connection
                    mock_connection = SocialConnection(
                        id=str(uuid4()),
                        user_id=mock_current_user.id,
                        platform="substack",
                        platform_username="testnewsletter",
                        is_active=True,
                        analysis_status="not_started",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    mock_get_connection.return_value = mock_connection

                    # Mock database commit failure
                    mock_commit.side_effect = Exception("Database error")
                    mock_rollback.return_value = None

                    response = test_client.post(
                        "/api/v1/profile/analyze-substack",
                        headers={"Authorization": "Bearer test_token"},
                    )

                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Database error" in response.json()["detail"]
                    mock_rollback.assert_called_once()

    # TODO: a user should be allowed to re-run the analysis
    # def test_run_substack_analysis_completed_analysis(
    #     self, test_client, mock_current_user, mock_db
    # ):
    #     """Test running Substack analysis when analysis is already complete."""
    #     with patch(
    #         "app.services.profile.ProfileService.get_social_connection_for_analysis"
    #     ) as mock_get_connection:
    #         mock_connection = SocialConnection(
    #             id=uuid4(),
    #             user_id=mock_current_user.id,
    #             platform="substack",
    #             platform_username="testuser",
    #             is_active=True,
    #             analysis_completed_at=datetime.now(timezone.utc),
    #         )
    #         mock_get_connection.return_value = mock_connection

    #         response = test_client.post(
    #             "/api/v1/profile/analyze-substack",
    #             headers={"Authorization": "Bearer test_token"},
    #         )
    #         assert response.status_code == status.HTTP_400_BAD_REQUEST
    #         assert "already been completed" in response.json()["detail"]

    def test_run_substack_analysis_no_username(
        self, test_client, mock_current_user, mock_db
    ):
        """Test running Substack analysis when there is no username."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            mock_connection = SocialConnection(
                id=uuid4(),
                user_id=mock_current_user.id,
                platform="substack",
                platform_username=None,
                is_active=True,
                analysis_status="not_started",
            )
            mock_get_connection.return_value = mock_connection

            response = test_client.post(
                "/api/v1/profile/analyze-substack",
                headers={"Authorization": "Bearer test_token"},
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert (
                "substack connection has no platform_username configured"
                in response.json()["detail"]
            )

    def test_unauthorized_access(self, test_client):
        """Test unauthorized access to protected endpoints."""
        response = test_client.get("/api/v1/profile/preferences")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__])

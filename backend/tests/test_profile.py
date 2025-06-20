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
        id=str(uuid4()),
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
    async def test_writing_style_analysis_operations(self, profile_service, test_user):
        """Test writing style analysis CRUD operations."""
        # Create analysis - updated to match service signature
        analysis_data_str = "this is the writing style analysis data"
        analysis = await profile_service.upsert_writing_style_analysis(
            test_user.id, "linkedin", analysis_data_str
        )

        assert analysis.platform == "linkedin"
        assert analysis.analysis_data == "this is the writing style analysis data"
        assert analysis.content_count == 0  # Default value

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
            id=str(uuid4()),
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
                id=str(uuid4()),
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

    def test_get_writing_style_analysis_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test GET /profile/writing-analysis/{platform} endpoint."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection"
        ) as mock_conn:
            with patch(
                "app.services.profile.ProfileService.get_writing_style_analysis"
            ) as mock_analysis:
                mock_conn.return_value = SocialConnection(
                    id=str(uuid4()),
                    user_id=mock_current_user.id,
                    platform="linkedin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                mock_analysis.return_value = None

                response = test_client.get(
                    "/api/v1/profile/writing-analysis/linkedin",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "is_connected" in data
                assert data["is_connected"] is True

    def test_run_writing_style_analysis_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/writing-analysis/{platform} endpoint."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection"
        ) as mock_conn:
            with patch(
                "app.services.profile.ProfileService.upsert_writing_style_analysis"
            ) as mock_analysis:
                mock_conn.return_value = SocialConnection(
                    id=str(uuid4()),
                    user_id=mock_current_user.id,
                    platform="linkedin",
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )

                mock_analysis_obj = WritingStyleAnalysis(
                    id=str(uuid4()),
                    user_id=mock_current_user.id,
                    platform="linkedin",
                    analysis_data="this is the writing style analysis data",
                    content_count=25,
                    last_analyzed_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                mock_analysis.return_value = mock_analysis_obj

                response = test_client.post(
                    "/api/v1/profile/writing-analysis/linkedin",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["is_connected"] is True
                assert "analysis_data" in data

    def test_run_substack_analysis_endpoint(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack endpoint."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            with patch(
                "app.services.profile.ProfileService._trigger_gcp_cloud_run"
            ) as mock_trigger:
                with patch.object(mock_db, "commit") as mock_commit:
                    with patch.object(mock_db, "refresh") as mock_refresh:
                        # Mock the connection that get_social_connection_for_analysis returns
                        mock_connection = SocialConnection(
                            id=str(uuid4()),
                            user_id=mock_current_user.id,
                            platform="substack",
                            platform_username="testnewsletter",
                            is_active=True,
                            connection_data={
                                "analysis_result": {
                                    "topics": ["Technology", "AI"],
                                    "subscriber_insights": {
                                        "estimated_subscribers": 1000
                                    },
                                    "recent_posts": [
                                        {
                                            "title": "Test Post",
                                            "url": "https://test.com",
                                        }
                                    ],
                                }
                            },
                            analysis_started_at=datetime.now(timezone.utc),
                            analysis_completed_at=datetime.now(timezone.utc),
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        mock_get_connection.return_value = mock_connection
                        mock_trigger.return_value = (
                            None  # Async function that doesn't return anything
                        )
                        mock_commit.return_value = None
                        mock_refresh.return_value = None

                        response = test_client.post(
                            "/api/v1/profile/analyze-substack",
                            headers={"Authorization": "Bearer test_token"},
                        )

                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["is_connected"] is True
                        assert len(data["substack_data"]) > 0
                        assert data["substack_data"][0]["topics"] == [
                            "Technology",
                            "AI",
                        ]
                        assert (
                            data["is_analyzing"] is True
                        )  # Analysis is started but not completed
                        assert data["analysis_started_at"] is not None
                        assert data["analysis_completed_at"] is None

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

    def test_run_substack_analysis_no_username(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack when connection has no platform_username."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            # Mock connection without platform_username
            mock_connection = SocialConnection(
                id=str(uuid4()),
                user_id=mock_current_user.id,
                platform="substack",
                platform_username=None,  # No username set
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_get_connection.return_value = mock_connection

            response = test_client.post(
                "/api/v1/profile/analyze-substack",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not configured" in data["detail"]

    def test_run_substack_analysis_gcp_failure(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack when GCP Cloud Run fails."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            with patch(
                "app.services.profile.ProfileService._trigger_gcp_cloud_run"
            ) as mock_trigger:
                with patch.object(mock_db, "commit") as mock_commit:
                    with patch.object(mock_db, "refresh") as mock_refresh:
                        # Mock valid connection
                        mock_connection = SocialConnection(
                            id=str(uuid4()),
                            user_id=mock_current_user.id,
                            platform="substack",
                            platform_username="testnewsletter",
                            is_active=True,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        mock_get_connection.return_value = mock_connection
                        mock_commit.return_value = None
                        mock_refresh.return_value = None

                        # Mock GCP failure
                        mock_trigger.side_effect = Exception("GCP Cloud Run failed")

                        response = test_client.post(
                            "/api/v1/profile/analyze-substack",
                            headers={"Authorization": "Bearer test_token"},
                        )

                        assert (
                            response.status_code
                            == status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                        data = response.json()
                        assert "Failed to run Substack analysis" in data["detail"]

    def test_run_substack_analysis_database_error(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack when database commit fails."""
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
                    data = response.json()
                    assert "Failed to run Substack analysis" in data["detail"]
                    mock_rollback.assert_called_once()

    def test_run_substack_analysis_completed_analysis(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack with a completed analysis."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            with patch(
                "app.services.profile.ProfileService._trigger_gcp_cloud_run"
            ) as mock_trigger:
                with patch.object(mock_db, "commit") as mock_commit:
                    with patch.object(mock_db, "refresh") as mock_refresh:
                        # Mock connection with completed analysis
                        completed_time = datetime.now(timezone.utc)
                        mock_connection = SocialConnection(
                            id=str(uuid4()),
                            user_id=mock_current_user.id,
                            platform="substack",
                            platform_username="testnewsletter",
                            is_active=True,
                            connection_data={
                                "analysis_result": {
                                    "topics": ["Business", "Entrepreneurship"],
                                    "subscriber_insights": {
                                        "estimated_subscribers": 5000
                                    },
                                    "recent_posts": [
                                        {
                                            "title": "Building a Startup",
                                            "url": "https://test.substack.com/p/startup",
                                        }
                                    ],
                                }
                            },
                            analysis_started_at=completed_time,
                            analysis_completed_at=completed_time,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        mock_get_connection.return_value = mock_connection
                        mock_trigger.return_value = None
                        mock_commit.return_value = None
                        mock_refresh.return_value = None

                        response = test_client.post(
                            "/api/v1/profile/analyze-substack",
                            headers={"Authorization": "Bearer test_token"},
                        )

                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["is_connected"] is True
                        assert len(data["substack_data"]) > 0
                        assert data["substack_data"][0]["topics"] == [
                            "Business",
                            "Entrepreneurship",
                        ]
                        assert data["substack_data"][0]["subscriber_count"] == 5000
                        assert data["is_analyzing"] is True  # Analysis was restarted
                        assert data["analysis_started_at"] is not None
                        assert (
                            data["analysis_completed_at"] is None
                        )  # Reset when analysis starts

    def test_run_substack_analysis_no_analysis_data(
        self, test_client, mock_current_user, mock_db
    ):
        """Test POST /profile/analyze-substack when connection has no analysis data."""
        with patch(
            "app.services.profile.ProfileService.get_social_connection_for_analysis"
        ) as mock_get_connection:
            with patch(
                "app.services.profile.ProfileService._trigger_gcp_cloud_run"
            ) as mock_trigger:
                with patch.object(mock_db, "commit") as mock_commit:
                    with patch.object(mock_db, "refresh") as mock_refresh:
                        # Mock connection without analysis data
                        mock_connection = SocialConnection(
                            id=str(uuid4()),
                            user_id=mock_current_user.id,
                            platform="substack",
                            platform_username="testnewsletter",
                            is_active=True,
                            connection_data={},  # No analysis_result
                            analysis_started_at=datetime.now(timezone.utc),
                            analysis_completed_at=None,
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc),
                        )
                        mock_get_connection.return_value = mock_connection
                        mock_trigger.return_value = None
                        mock_commit.return_value = None
                        mock_refresh.return_value = None

                        response = test_client.post(
                            "/api/v1/profile/analyze-substack",
                            headers={"Authorization": "Bearer test_token"},
                        )

                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["is_connected"] is True
                        assert len(data["substack_data"]) == 0  # No data available
                        assert data["is_analyzing"] is True  # Analysis in progress
                        assert data["analysis_started_at"] is not None
                        assert data["analysis_completed_at"] is None

    def test_unauthorized_access(self, test_client):
        """Test unauthorized access to endpoints."""
        response = test_client.get("/api/v1/profile/preferences")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__])

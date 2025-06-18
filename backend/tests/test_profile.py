"""
Tests for profile services and endpoints.
Comprehensive test coverage for all profile-related functionality.
"""

import pytest
import pytest_asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_async_db
from app.routers.auth import get_current_user
from app.models.profile import (
    UserPreferences,
    SocialConnection,
    WritingStyleAnalysis,
)
from app.services.profile import ProfileService
from app.schemas.profile import (
    UserPreferencesUpdate,
    SocialConnectionUpdate,
    WritingStyleAnalysisUpdate,
)
from app.schemas.auth import UserResponse

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_profile.db"


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
        )
        preferences = await profile_service.upsert_user_preferences(
            test_user.id, preferences_data
        )

        assert preferences.topics_of_interest == ["AI", "Technology"]
        assert preferences.websites == ["example.com", "test.com"]

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
        # Create analysis
        analysis_data = WritingStyleAnalysisUpdate(
            analysis_data={
                "tone": "professional",
                "complexity": "intermediate",
                "topics": ["technology", "business"],
            },
            content_count=10,
        )
        analysis = await profile_service.upsert_writing_style_analysis(
            test_user.id, "linkedin", analysis_data
        )

        assert analysis.platform == "linkedin"
        assert analysis.analysis_data["tone"] == "professional"
        assert analysis.content_count == 10

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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_service.return_value = mock_preferences

            preferences_data = {
                "topics_of_interest": ["AI", "Tech"],
                "websites": ["example.com"],
            }

            response = test_client.put(
                "/api/v1/profile/preferences",
                json=preferences_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["topics_of_interest"] == ["AI", "Tech"]

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
                    analysis_data={
                        "writing_style": {
                            "tone": "Professional",
                            "complexity": "intermediate",
                            "avg_length": 150,
                            "key_themes": ["business", "technology"],
                        },
                        "topics": ["AI", "business", "technology"],
                        "posting_patterns": {
                            "frequency": "weekly",
                            "best_times": ["9AM", "2PM"],
                        },
                        "engagement_insights": {
                            "high_performing_topics": ["AI", "business"],
                            "content_types": ["article", "post"],
                        },
                    },
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
        """Test POST /profile/substack-analysis endpoint."""
        with patch(
            "app.services.profile.ProfileService.upsert_social_connection"
        ) as mock_service:
            mock_connection = SocialConnection(
                id=str(uuid4()),
                user_id=mock_current_user.id,
                platform="substack",
                is_active=True,
                connection_data={
                    "substackData": [
                        {
                            "name": "Test Newsletter",
                            "url": "https://test.substack.com",
                            "topics": ["Technology"],
                        }
                    ],
                    "analyzed_at": "2024-01-01T00:00:00Z",
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_service.return_value = mock_connection

            response = test_client.post(
                "/api/v1/profile/substack-analysis",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_connected"] is True
            assert len(data["substack_data"]) > 0

    def test_unauthorized_access(self, test_client):
        """Test unauthorized access to endpoints."""
        response = test_client.get("/api/v1/profile/preferences")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


if __name__ == "__main__":
    pytest.main([__file__])

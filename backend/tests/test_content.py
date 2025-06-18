"""
Tests for content services and endpoints.
Comprehensive test coverage for all content-related functionality.
"""

import os
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.core.database import Base, get_async_db
from app.routers.auth import get_current_user
from app.models.content import (
    ContentIdea,
    UserPreferences,
    SocialConnection,
    WritingStyleAnalysis,
)
from app.services.content import ContentService
from app.schemas.content import (
    ContentIdeaCreate,
    ContentIdeaUpdate,
    UserPreferencesUpdate,
    SocialConnectionUpdate,
    WritingStyleAnalysisUpdate,
)
from app.schemas.auth import UserResponse


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_content.db"


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create test database session."""
    # Remove existing test database
    if os.path.exists("./test_content.db"):
        os.remove("./test_content.db")

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
    if os.path.exists("./test_content.db"):
        os.remove("./test_content.db")


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
def content_service(test_db):
    """Create ContentService instance."""
    return ContentService(test_db)


class TestContentService:
    """Test cases for ContentService."""

    @pytest.mark.asyncio
    async def test_create_content_idea(self, content_service, test_user):
        """Test creating a content idea."""
        content_data = ContentIdeaCreate(
            title="Test Content Idea",
            content_type="blog_post",
            original_input="Test input",
            generated_outline={"sections": ["intro", "body", "conclusion"]},
        )

        result = await content_service.create_content_idea(test_user.id, content_data)

        assert result.title == "Test Content Idea"
        assert result.content_type == "blog_post"
        assert result.user_id == test_user.id
        assert result.status == "draft"
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_content_ideas_with_filters(self, content_service, test_user):
        """Test getting content ideas with filters."""
        # Create test content ideas
        for i in range(5):
            content_data = ContentIdeaCreate(
                title=f"Test Content {i}",
                content_type="blog_post" if i % 2 == 0 else "linkedin_post",
                status="published" if i < 3 else "draft",
            )
            await content_service.create_content_idea(test_user.id, content_data)

        # Test filtering by status
        result = await content_service.get_content_ideas(
            user_id=test_user.id, status=["published"]
        )
        assert result["total"] == 3
        assert len(result["items"]) == 3

        # Test filtering by content type
        result = await content_service.get_content_ideas(
            user_id=test_user.id, content_type="blog_post"
        )
        assert result["total"] == 3  # 3 blog posts (even indices)

        # Test pagination
        result = await content_service.get_content_ideas(
            user_id=test_user.id, page=1, size=2
        )
        assert len(result["items"]) == 2
        assert result["has_next"] is True

    @pytest.mark.asyncio
    async def test_update_content_idea(self, content_service, test_user):
        """Test updating a content idea."""
        # Create content idea
        content_data = ContentIdeaCreate(
            title="Original Title", content_type="blog_post"
        )
        content_idea = await content_service.create_content_idea(
            test_user.id, content_data
        )

        # Update content idea
        update_data = ContentIdeaUpdate(title="Updated Title", status="published")
        updated = await content_service.update_content_idea(
            test_user.id, content_idea.id, update_data
        )

        assert updated.title == "Updated Title"
        assert updated.status == "published"
        assert updated.updated_at > updated.created_at

    @pytest.mark.asyncio
    async def test_delete_content_idea(self, content_service, test_user):
        """Test deleting a content idea."""
        # Create content idea
        content_data = ContentIdeaCreate(
            title="To Be Deleted", content_type="blog_post"
        )
        content_idea = await content_service.create_content_idea(
            test_user.id, content_data
        )

        # Delete content idea
        deleted = await content_service.delete_content_idea(
            test_user.id, content_idea.id
        )
        assert deleted is True

        # Verify it's deleted
        result = await content_service.get_content_idea(test_user.id, content_idea.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_user_preferences_operations(self, content_service, test_user):
        """Test user preferences CRUD operations."""
        # Create preferences
        preferences_data = UserPreferencesUpdate(
            topics_of_interest=["AI", "Technology"],
            websites=["example.com", "test.com"],
        )
        preferences = await content_service.upsert_user_preferences(
            test_user.id, preferences_data
        )

        assert preferences.topics_of_interest == ["AI", "Technology"]
        assert preferences.websites == ["example.com", "test.com"]

        # Update preferences
        update_data = UserPreferencesUpdate(
            topics_of_interest=["AI", "Technology", "Business"]
        )
        updated = await content_service.upsert_user_preferences(
            test_user.id, update_data
        )

        assert len(updated.topics_of_interest) == 3
        assert "Business" in updated.topics_of_interest

    @pytest.mark.asyncio
    async def test_social_connections_operations(self, content_service, test_user):
        """Test social connections CRUD operations."""
        # Create connection
        connection_data = SocialConnectionUpdate(
            platform_username="testuser",
            is_active=True,
            connection_data={"access_token": "test_token"},
        )
        connection = await content_service.upsert_social_connection(
            test_user.id, "linkedin", connection_data
        )

        assert connection.platform == "linkedin"
        assert connection.platform_username == "testuser"
        assert connection.is_active is True

        # Get connection
        retrieved = await content_service.get_social_connection(
            test_user.id, "linkedin"
        )
        assert retrieved.id == connection.id

        # Get all connections
        all_connections = await content_service.get_social_connections(test_user.id)
        assert len(all_connections) == 1

    @pytest.mark.asyncio
    async def test_writing_style_analysis_operations(self, content_service, test_user):
        """Test writing style analysis operations."""
        # Create analysis
        analysis_data = WritingStyleAnalysisUpdate(
            analysis_data={
                "tone": "professional",
                "topics": ["AI", "Tech"],
                "avg_length": 500,
            },
            content_count=10,
        )
        analysis = await content_service.upsert_writing_style_analysis(
            test_user.id, "linkedin", analysis_data
        )

        assert analysis.platform == "linkedin"
        assert analysis.content_count == 10
        assert analysis.analysis_data["tone"] == "professional"

        # Get analysis
        retrieved = await content_service.get_writing_style_analysis(
            test_user.id, "linkedin"
        )
        assert retrieved.id == analysis.id


class TestContentEndpoints:
    """Test cases for content endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock the current user dependency."""
        test_user = UserResponse(
            id=str(uuid4()),
            email="test@example.com",
            is_active=True,
            is_verified=True,
            created_at=datetime.now(timezone.utc),
        )

        async def mock_get_current_user():
            return test_user

        app.dependency_overrides[get_current_user] = mock_get_current_user
        yield test_user

        # Clean up
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

    @pytest.fixture
    def mock_db(self, test_db):
        """Mock the database dependency."""

        async def mock_get_db():
            return test_db

        app.dependency_overrides[get_async_db] = mock_get_db
        yield test_db

        # Clean up
        if get_async_db in app.dependency_overrides:
            del app.dependency_overrides[get_async_db]

    def test_get_content_ideas_endpoint(self, client, mock_current_user, mock_db):
        """Test GET /content/ideas endpoint."""
        with patch(
            "app.services.content.ContentService.get_content_ideas"
        ) as mock_service:
            mock_service.return_value = {
                "items": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "has_next": False,
            }

            response = client.get(
                "/api/v1/content/ideas",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "items" in data
            assert "total" in data

    def test_create_content_idea_endpoint(self, client, mock_current_user, mock_db):
        """Test POST /content/ideas endpoint."""
        with patch(
            "app.services.content.ContentService.create_content_idea"
        ) as mock_service:
            mock_content = ContentIdea(
                id=str(uuid4()),
                user_id=mock_current_user.id,
                title="Test Content",
                content_type="blog_post",
                status="draft",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_service.return_value = mock_content

            content_data = {
                "title": "Test Content",
                "content_type": "blog_post",
                "original_input": "Test input",
            }

            response = client.post(
                "/api/v1/content/ideas",
                json=content_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["title"] == "Test Content"

    def test_get_user_preferences_endpoint(self, client, mock_current_user, mock_db):
        """Test GET /content/preferences endpoint."""
        with patch(
            "app.services.content.ContentService.get_user_preferences"
        ) as mock_service:
            mock_service.return_value = None

            response = client.get(
                "/api/v1/content/preferences",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "topics_of_interest" in data
            assert "websites" in data

    def test_update_user_preferences_endpoint(self, client, mock_current_user, mock_db):
        """Test PUT /content/preferences endpoint."""
        with patch(
            "app.services.content.ContentService.upsert_user_preferences"
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

            response = client.put(
                "/api/v1/content/preferences",
                json=preferences_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["topics_of_interest"] == ["AI", "Tech"]

    def test_get_social_connections_endpoint(self, client, mock_current_user, mock_db):
        """Test GET /content/social-connections endpoint."""
        with patch(
            "app.services.content.ContentService.get_social_connections"
        ) as mock_service:
            mock_service.return_value = []

            response = client.get(
                "/api/v1/content/social-connections",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)

    def test_get_writing_style_analysis_endpoint(
        self, client, mock_current_user, mock_db
    ):
        """Test GET /content/writing-analysis/{platform} endpoint."""
        with patch(
            "app.services.content.ContentService.get_social_connection"
        ) as mock_conn:
            with patch(
                "app.services.content.ContentService.get_writing_style_analysis"
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

                response = client.get(
                    "/api/v1/content/writing-analysis/linkedin",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "is_connected" in data
                assert data["is_connected"] is True

    def test_run_writing_style_analysis_endpoint(
        self, client, mock_current_user, mock_db
    ):
        """Test POST /content/writing-analysis/{platform} endpoint."""
        with patch(
            "app.services.content.ContentService.get_social_connection"
        ) as mock_conn:
            with patch(
                "app.services.content.ContentService.upsert_writing_style_analysis"
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
                            "tone": "professional",
                            "complexity": "intermediate",
                            "avg_length": 150,
                            "key_themes": ["leadership", "technology"],
                        },
                        "topics": ["business", "tech"],
                        "posting_patterns": {
                            "frequency": "weekly",
                            "best_times": ["9:00 AM", "5:00 PM"],
                        },
                        "engagement_insights": {
                            "high_performing_topics": ["AI"],
                            "content_types": ["insights", "tips"],
                        },
                    },
                    content_count=10,
                    last_analyzed_at=datetime.now(timezone.utc),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                mock_analysis.return_value = mock_analysis_obj

                response = client.post(
                    "/api/v1/content/writing-analysis/linkedin",
                    headers={"Authorization": "Bearer test_token"},
                )

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "analysis_data" in data
                assert "is_connected" in data

    def test_run_substack_analysis_endpoint(self, client, mock_current_user, mock_db):
        """Test POST /content/substack-analysis endpoint."""
        with patch(
            "app.services.content.ContentService.upsert_social_connection"
        ) as mock_service:
            mock_connection = SocialConnection(
                id=str(uuid4()),
                user_id=mock_current_user.id,
                platform="substack",
                is_active=True,
                connection_data={
                    "substackData": [{"name": "Test Blog", "url": "test.substack.com"}],
                    "analyzed_at": datetime.now(timezone.utc).isoformat(),
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            mock_service.return_value = mock_connection

            response = client.post(
                "/api/v1/content/substack-analysis",
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "substack_data" in data
            assert "is_connected" in data

    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        endpoints = [
            "/api/v1/content/ideas",
            "/api/v1/content/preferences",
            "/api/v1/content/social-connections",
            "/api/v1/content/writing-analysis/linkedin",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestContentValidation:
    """Test data validation and edge cases."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """Mock the current user dependency."""
        test_user = UserResponse(
            id=str(uuid4()),
            email="test@example.com",
            is_active=True,
            is_verified=True,
            created_at=datetime.now(timezone.utc),
        )

        async def mock_get_current_user():
            return test_user

        app.dependency_overrides[get_current_user] = mock_get_current_user
        yield test_user

        # Clean up
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

    @pytest.fixture
    def mock_db(self, test_db):
        """Mock the database dependency."""

        async def mock_get_db():
            return test_db

        app.dependency_overrides[get_async_db] = mock_get_db
        yield test_db

        # Clean up
        if get_async_db in app.dependency_overrides:
            del app.dependency_overrides[get_async_db]

    def test_invalid_content_type(self, client, mock_current_user, mock_db):
        """Test creating content with missing required fields."""
        content_data = {
            "content_type": "blog_post",
            # Missing required 'title' field
        }

        response = client.post(
            "/api/v1/content/ideas",
            json=content_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_platform(self, client, mock_current_user, mock_db):
        """Test analysis with invalid platform."""
        response = client.get(
            "/api/v1/content/writing-analysis/invalid_platform",
            headers={"Authorization": "Bearer test_token"},
        )

        # Should still work but return no connection
        assert response.status_code == status.HTTP_200_OK

    def test_pagination_limits(self, client, mock_current_user, mock_db):
        """Test pagination parameter validation."""
        # Test invalid page number
        response = client.get(
            "/api/v1/content/ideas?page=0",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test invalid size
        response = client.get(
            "/api/v1/content/ideas?size=1000",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_order_direction_validation(self, client, mock_current_user, mock_db):
        """Test order direction parameter validation."""
        response = client.get(
            "/api/v1/content/ideas?order_direction=invalid",
            headers={"Authorization": "Bearer test_token"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


if __name__ == "__main__":
    pytest.main([__file__])

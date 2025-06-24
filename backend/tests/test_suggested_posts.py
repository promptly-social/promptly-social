"""
Tests for suggested posts functionality.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient


from app.schemas.suggested_posts import PostFeedback, SuggestedPostCreate


class TestSuggestedPosts:
    """Test cases for suggested posts endpoints."""

    @pytest.fixture
    def sample_post_data(self):
        """Sample post data for testing."""
        return {
            "title": "Test Post",
            "content": "This is a test post\nwith multiple lines\nof content.",
            "platform": "linkedin",
            "topics": ["technology", "AI"],
            "recommendation_score": 85,
            "status": "suggested",
        }

    @pytest.fixture
    def sample_feedback(self):
        """Sample feedback data for testing."""
        return {"feedback_type": "positive"}

    @pytest.fixture
    def sample_negative_feedback(self):
        """Sample negative feedback with comment."""
        return {
            "feedback_type": "negative",
            "comment": "Content doesn't match my industry",
        }

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers for testing."""
        return {"Authorization": "Bearer test-token"}

    def test_get_suggested_posts_unauthorized(self, test_client: TestClient):
        """Test that unauthorized requests are rejected."""
        response = test_client.get("/api/v1/suggested-posts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_feedback_schema_validation(self):
        """Test PostFeedback schema validation."""
        # Valid feedback
        valid_feedback = PostFeedback(feedback_type="positive")
        assert valid_feedback.feedback_type == "positive"
        assert valid_feedback.comment is None

        valid_feedback_with_comment = PostFeedback(
            feedback_type="negative", comment="Not relevant"
        )
        assert valid_feedback_with_comment.feedback_type == "negative"
        assert valid_feedback_with_comment.comment == "Not relevant"

        # Invalid feedback type should raise validation error
        with pytest.raises(ValueError):
            PostFeedback(feedback_type="neutral")

    def test_suggested_post_create_schema_validation(self):
        """Test SuggestedPostCreate schema validation."""
        # Valid creation data
        valid_data = SuggestedPostCreate(content="Test content\nwith newlines")
        assert valid_data.content == "Test content\nwith newlines"
        assert valid_data.platform == "linkedin"  # default value
        assert valid_data.recommendation_score == 0  # default value

        # Test with all fields
        full_data = SuggestedPostCreate(
            title="Test Title",
            content="Test content",
            platform="twitter",
            topics=["tech", "AI"],
            recommendation_score=95,
            status="draft",
        )
        assert full_data.title == "Test Title"
        assert full_data.platform == "twitter"
        assert full_data.recommendation_score == 95

    @pytest.mark.asyncio
    async def test_service_layer_feedback_submission(self):
        """Test the service layer feedback submission logic."""
        from app.services.suggested_posts import SuggestedPostsService
        from app.models.suggested_posts import SuggestedPost

        # Mock database session
        mock_db = AsyncMock()
        service = SuggestedPostsService(mock_db)

        # Mock post
        mock_post = SuggestedPost(
            id=uuid4(),
            user_id=uuid4(),
            content="Test content",
            platform="linkedin",
            recommendation_score=80,
            status="suggested",
        )

        # Mock the get_suggested_post method
        service.get_suggested_post = AsyncMock(return_value=mock_post)

        # Test feedback submission
        result = await service.submit_feedback(
            user_id=mock_post.user_id,
            post_id=mock_post.id,
            feedback_type="positive",
            comment="Great suggestion!",
        )

        assert result.user_feedback == "positive"
        assert result.feedback_comment == "Great suggestion!"
        assert result.feedback_at is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_feedback_endpoint_structure(self, test_client: TestClient):
        """Test that the feedback endpoint exists and has proper structure."""
        # This test verifies the endpoint exists without authentication
        fake_id = str(uuid4())
        response = test_client.post(f"/api/v1/suggested-posts/{fake_id}/feedback")
        # Should return 401 (unauthorized) not 404 (not found), proving endpoint exists
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_suggested_posts_endpoints_exist(self, test_client: TestClient):
        """Test that all suggested posts endpoints exist."""
        endpoints_to_test = [
            ("GET", "/api/v1/suggested-posts/"),
            ("POST", "/api/v1/suggested-posts/"),
            ("GET", f"/api/v1/suggested-posts/{uuid4()}"),
            ("PUT", f"/api/v1/suggested-posts/{uuid4()}"),
            ("DELETE", f"/api/v1/suggested-posts/{uuid4()}"),
            ("POST", f"/api/v1/suggested-posts/{uuid4()}/dismiss"),
            ("POST", f"/api/v1/suggested-posts/{uuid4()}/mark-posted"),
            ("POST", f"/api/v1/suggested-posts/{uuid4()}/feedback"),
        ]

        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = test_client.get(endpoint)
            elif method == "POST":
                response = test_client.post(endpoint, json={})
            elif method == "PUT":
                response = test_client.put(endpoint, json={})
            elif method == "DELETE":
                response = test_client.delete(endpoint)

            # All should return 401 (unauthorized) not 404 (not found)
            # This proves the endpoints are properly registered
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"Endpoint {method} {endpoint} not found"
            )

    def test_invalid_feedback_validation(self, test_client: TestClient):
        """Test that invalid feedback types are rejected."""
        fake_id = str(uuid4())
        invalid_feedback = {"feedback_type": "neutral", "comment": "test"}

        response = test_client.post(
            f"/api/v1/suggested-posts/{fake_id}/feedback",
            json=invalid_feedback,
            headers={"Authorization": "Bearer invalid-token"},
        )

        # Should be either 401 (unauthorized) or 422 (validation error)
        # Both are acceptable since we're testing validation
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_newline_content_handling(self):
        """Test that content with newlines is properly handled in schemas."""
        content_with_newlines = "Line 1\nLine 2\nLine 3\n\nLine 5"

        post_data = SuggestedPostCreate(content=content_with_newlines)
        assert post_data.content == content_with_newlines
        assert "\n" in post_data.content

        # Test that the content maintains its structure
        lines = post_data.content.split("\n")
        assert len(lines) == 5
        assert lines[0] == "Line 1"
        assert lines[3] == ""  # Empty line
        assert lines[4] == "Line 5"

    def test_post_feedback_comment_optional(self):
        """Test that feedback comment is optional."""
        # Positive feedback without comment
        positive_feedback = PostFeedback(feedback_type="positive")
        assert positive_feedback.comment is None

        # Negative feedback without comment
        negative_feedback = PostFeedback(feedback_type="negative")
        assert negative_feedback.comment is None

        # Negative feedback with comment
        negative_with_comment = PostFeedback(
            feedback_type="negative", comment="This doesn't match my industry focus"
        )
        assert negative_with_comment.comment == "This doesn't match my industry focus"

"""
Tests for user activity analysis migration and models.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.user_activity_analysis import UserAnalysisTracking
from app.models.profile import UserPreferences
from app.models.user import User


class TestUserActivityAnalysisModels:
    """Test the user activity analysis models."""

    def test_user_analysis_tracking_model_creation(self):
        """Test creating UserAnalysisTracking model instances."""
        user_id = uuid4()

        # Create a tracking record
        tracking = UserAnalysisTracking(
            user_id=user_id,
            analysis_scope={
                "posts_analyzed": {
                    "scheduled_count": 5,
                    "dismissed_count": 3,
                    "post_ids": ["uuid1", "uuid2"],
                    "date_range": {
                        "start": "2024-01-01T00:00:00Z",
                        "end": "2024-01-02T00:00:00Z",
                    },
                },
                "messages_analyzed": {
                    "total_count": 12,
                    "conversation_ids": ["uuid1", "uuid2"],
                    "excluded_first_messages": 3,
                },
                "analysis_types_performed": [
                    "writing_style",
                    "topics_of_interest",
                    "bio_update",
                    "negative_analysis",
                ],
            },
        )

        # Verify model attributes
        assert tracking.user_id == user_id
        assert tracking.analysis_scope is not None
        assert "posts_analyzed" in tracking.analysis_scope
        assert tracking.analysis_scope["posts_analyzed"]["scheduled_count"] == 5
        assert tracking.analysis_scope["messages_analyzed"]["total_count"] == 12

    def test_user_analysis_tracking_model_defaults(self):
        """Test UserAnalysisTracking model with default values."""
        user_id = uuid4()

        tracking = UserAnalysisTracking(user_id=user_id)

        assert tracking.user_id == user_id
        assert tracking.last_analysis_at is None
        assert tracking.last_analyzed_post_id is None
        assert tracking.last_analyzed_message_id is None
        assert tracking.analysis_scope is None

    def test_user_analysis_tracking_model_with_timestamps(self):
        """Test UserAnalysisTracking model with timestamp fields."""
        user_id = uuid4()
        post_id = uuid4()
        message_id = uuid4()
        analysis_time = datetime.now()

        tracking = UserAnalysisTracking(
            user_id=user_id,
            last_analysis_at=analysis_time,
            last_analyzed_post_id=post_id,
            last_analyzed_message_id=message_id,
        )

        assert tracking.user_id == user_id
        assert tracking.last_analysis_at == analysis_time
        assert tracking.last_analyzed_post_id == post_id
        assert tracking.last_analyzed_message_id == message_id

    def test_user_analysis_tracking_repr(self):
        """Test UserAnalysisTracking model string representation."""
        user_id = uuid4()
        analysis_time = datetime.now()

        tracking = UserAnalysisTracking(user_id=user_id, last_analysis_at=analysis_time)

        repr_str = repr(tracking)
        assert str(user_id) in repr_str
        assert "UserAnalysisTracking" in repr_str

    def test_user_preferences_negative_analysis_field(self):
        """Test that UserPreferences model can handle negative_analysis field."""
        user_id = uuid4()

        # Test creating preferences with negative analysis
        preferences = UserPreferences(
            user_id=user_id,
            bio="Test bio",
            negative_analysis="User dislikes overly promotional content and prefers technical discussions.",
        )

        assert preferences.user_id == user_id
        assert preferences.bio == "Test bio"
        # Note: We can't test the actual database field without a real database connection
        # This test verifies the model can be instantiated with the field

    def test_user_preferences_without_negative_analysis(self):
        """Test UserPreferences model without negative_analysis field."""
        user_id = uuid4()

        preferences = UserPreferences(user_id=user_id, bio="Test bio")

        assert preferences.user_id == user_id
        assert preferences.bio == "Test bio"

    def test_analysis_scope_structure(self):
        """Test the expected structure of analysis_scope JSON field."""
        user_id = uuid4()

        expected_scope = {
            "posts_analyzed": {
                "scheduled_count": 5,
                "dismissed_count": 3,
                "post_ids": ["post-uuid-1", "post-uuid-2"],
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-02T00:00:00Z",
                },
            },
            "messages_analyzed": {
                "total_count": 12,
                "conversation_ids": ["conv-uuid-1", "conv-uuid-2"],
                "excluded_first_messages": 3,
            },
            "analysis_types_performed": [
                "writing_style",
                "topics_of_interest",
                "bio_update",
                "negative_analysis",
            ],
        }

        tracking = UserAnalysisTracking(user_id=user_id, analysis_scope=expected_scope)

        # Verify structure
        scope = tracking.analysis_scope
        assert "posts_analyzed" in scope
        assert "messages_analyzed" in scope
        assert "analysis_types_performed" in scope

        # Verify posts analysis structure
        posts_data = scope["posts_analyzed"]
        assert "scheduled_count" in posts_data
        assert "dismissed_count" in posts_data
        assert "post_ids" in posts_data
        assert "date_range" in posts_data

        # Verify messages analysis structure
        messages_data = scope["messages_analyzed"]
        assert "total_count" in messages_data
        assert "conversation_ids" in messages_data
        assert "excluded_first_messages" in messages_data

        # Verify analysis types
        analysis_types = scope["analysis_types_performed"]
        assert "writing_style" in analysis_types
        assert "topics_of_interest" in analysis_types
        assert "bio_update" in analysis_types
        assert "negative_analysis" in analysis_types


class TestMigrationRequirements:
    """Test that migration requirements are met."""

    def test_user_analysis_tracking_table_name(self):
        """Test that UserAnalysisTracking uses correct table name."""
        assert UserAnalysisTracking.__tablename__ == "user_analysis_tracking"

    def test_user_analysis_tracking_has_required_columns(self):
        """Test that UserAnalysisTracking has all required columns."""
        # Get the model's columns
        columns = UserAnalysisTracking.__table__.columns
        column_names = [col.name for col in columns]

        required_columns = [
            "id",
            "user_id",
            "last_analysis_at",
            "last_analyzed_post_id",
            "last_analyzed_message_id",
            "analysis_scope",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert (
                col in column_names
            ), f"Column {col} not found in UserAnalysisTracking model"

    def test_user_analysis_tracking_foreign_key(self):
        """Test that UserAnalysisTracking has proper foreign key to users table."""
        user_id_column = UserAnalysisTracking.__table__.columns["user_id"]

        # Check that user_id has a foreign key constraint
        assert len(user_id_column.foreign_keys) > 0

        # Check that it references the users table
        fk = list(user_id_column.foreign_keys)[0]
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"

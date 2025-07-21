"""
Unit tests for UserAnalysisTracking model.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.models.user_activity_analysis import UserAnalysisTracking


class TestUserAnalysisTracking:
    """Test cases for UserAnalysisTracking model."""

    def test_create_user_analysis_tracking(self):
        """Test creating a new UserAnalysisTracking record."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        assert tracking.user_id == user_id
        assert tracking.last_analysis_at is None
        assert tracking.last_analyzed_post_id is None
        assert tracking.last_analyzed_message_id is None
        assert tracking.analysis_scope is None

    def test_has_been_analyzed_property(self):
        """Test the has_been_analyzed hybrid property."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Initially should be False
        assert tracking.has_been_analyzed is False

        # After setting last_analysis_at, should be True
        tracking.last_analysis_at = datetime.now(timezone.utc)
        assert tracking.has_been_analyzed is True

    def test_needs_analysis_property(self):
        """Test the needs_analysis hybrid property."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Initially should need analysis
        assert tracking.needs_analysis is True

        # After analysis, should not need analysis (basic check)
        tracking.last_analysis_at = datetime.now(timezone.utc)
        assert tracking.needs_analysis is False

    def test_get_posts_analyzed_count(self):
        """Test getting posts analyzed count from analysis scope."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Initially should return 0
        assert tracking.get_posts_analyzed_count() == 0

        # Set analysis scope with posts data
        tracking.analysis_scope = {
            "posts_analyzed": {
                "scheduled_count": 5,
                "dismissed_count": 3,
                "post_ids": ["uuid1", "uuid2"],
            }
        }

        assert tracking.get_posts_analyzed_count() == 8  # 5 + 3

    def test_get_posts_analyzed_count_missing_data(self):
        """Test getting posts analyzed count with missing data."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Test with partial data
        tracking.analysis_scope = {
            "posts_analyzed": {
                "scheduled_count": 5,
                # missing dismissed_count
            }
        }
        assert tracking.get_posts_analyzed_count() == 5

        # Test with no posts_analyzed key
        tracking.analysis_scope = {"messages_analyzed": {"total_count": 10}}
        assert tracking.get_posts_analyzed_count() == 0

    def test_get_messages_analyzed_count(self):
        """Test getting messages analyzed count from analysis scope."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Initially should return 0
        assert tracking.get_messages_analyzed_count() == 0

        # Set analysis scope with messages data
        tracking.analysis_scope = {
            "messages_analyzed": {
                "total_count": 12,
                "conversation_ids": ["uuid1", "uuid2"],
            }
        }

        assert tracking.get_messages_analyzed_count() == 12

    def test_get_messages_analyzed_count_missing_data(self):
        """Test getting messages analyzed count with missing data."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Test with no messages_analyzed key
        tracking.analysis_scope = {"posts_analyzed": {"scheduled_count": 5}}
        assert tracking.get_messages_analyzed_count() == 0

    def test_get_analysis_types_performed(self):
        """Test getting analysis types performed from analysis scope."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Initially should return empty list
        assert tracking.get_analysis_types_performed() == []

        # Set analysis scope with analysis types
        tracking.analysis_scope = {
            "analysis_types_performed": [
                "writing_style",
                "topics_of_interest",
                "bio_update",
            ]
        }

        types = tracking.get_analysis_types_performed()
        assert len(types) == 3
        assert "writing_style" in types
        assert "topics_of_interest" in types
        assert "bio_update" in types

    def test_get_analysis_types_performed_missing_data(self):
        """Test getting analysis types performed with missing data."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Test with no analysis_types_performed key
        tracking.analysis_scope = {"posts_analyzed": {"scheduled_count": 5}}
        assert tracking.get_analysis_types_performed() == []

    def test_update_analysis_completion(self):
        """Test updating analysis completion with all data."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Prepare test data
        analysis_time = datetime.now(timezone.utc)
        posts_data = {
            "scheduled_count": 5,
            "dismissed_count": 3,
            "post_ids": ["uuid1", "uuid2"],
            "date_range": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-01-02T00:00:00Z",
            },
        }
        messages_data = {
            "total_count": 12,
            "conversation_ids": ["uuid3", "uuid4"],
            "excluded_first_messages": 3,
        }
        analysis_types = ["writing_style", "topics_of_interest", "bio_update"]
        last_post_id = uuid4()
        last_message_id = uuid4()

        # Update analysis completion
        tracking.update_analysis_completion(
            analysis_timestamp=analysis_time,
            posts_analyzed=posts_data,
            messages_analyzed=messages_data,
            analysis_types=analysis_types,
            last_post_id=last_post_id,
            last_message_id=last_message_id,
        )

        # Verify all fields were updated
        assert tracking.last_analysis_at == analysis_time
        assert tracking.last_analyzed_post_id == last_post_id
        assert tracking.last_analyzed_message_id == last_message_id

        # Verify analysis scope structure
        scope = tracking.analysis_scope
        assert scope["posts_analyzed"] == posts_data
        assert scope["messages_analyzed"] == messages_data
        assert scope["analysis_types_performed"] == analysis_types

        # Verify helper methods work with updated data
        assert tracking.get_posts_analyzed_count() == 8
        assert tracking.get_messages_analyzed_count() == 12
        assert tracking.get_analysis_types_performed() == analysis_types
        assert tracking.has_been_analyzed is True

    def test_update_analysis_completion_minimal(self):
        """Test updating analysis completion with minimal data."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        analysis_time = datetime.now(timezone.utc)
        posts_data = {"scheduled_count": 0, "dismissed_count": 0}
        messages_data = {"total_count": 0}
        analysis_types = ["writing_style"]

        tracking.update_analysis_completion(
            analysis_timestamp=analysis_time,
            posts_analyzed=posts_data,
            messages_analyzed=messages_data,
            analysis_types=analysis_types,
        )

        assert tracking.last_analysis_at == analysis_time
        assert tracking.last_analyzed_post_id is None
        assert tracking.last_analyzed_message_id is None
        assert tracking.has_been_analyzed is True

    def test_repr_method(self):
        """Test the __repr__ method."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        repr_str = repr(tracking)
        assert "UserAnalysisTracking" in repr_str
        assert str(tracking.user_id) in repr_str
        assert "has_been_analyzed=False" in repr_str

        # Test with analysis completed
        tracking.last_analysis_at = datetime.now(timezone.utc)
        repr_str = repr(tracking)
        assert "has_been_analyzed=True" in repr_str

    def test_analysis_scope_json_structure(self):
        """Test that analysis_scope handles complex JSON structure."""
        user_id = uuid4()
        tracking = UserAnalysisTracking(user_id=user_id)

        # Test complex nested JSON structure
        complex_scope = {
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
                "conversation_ids": ["uuid3", "uuid4"],
                "excluded_first_messages": 3,
            },
            "analysis_types_performed": [
                "writing_style",
                "topics_of_interest",
                "bio_update",
                "negative_analysis",
            ],
        }

        tracking.analysis_scope = complex_scope

        # Verify structure is preserved
        assert tracking.analysis_scope == complex_scope

        # Verify nested access works
        assert tracking.analysis_scope["posts_analyzed"]["scheduled_count"] == 5
        assert len(tracking.analysis_scope["analysis_types_performed"]) == 4

    def test_table_name(self):
        """Test that the model uses the correct table name."""
        assert UserAnalysisTracking.__tablename__ == "user_analysis_tracking"

    def test_model_columns(self):
        """Test that the model has all required columns."""
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

    def test_foreign_key_constraint(self):
        """Test that user_id has proper foreign key constraint."""
        user_id_column = UserAnalysisTracking.__table__.columns["user_id"]

        # Check that user_id has a foreign key constraint
        assert len(user_id_column.foreign_keys) > 0

        # Check that it references the users table
        fk = list(user_id_column.foreign_keys)[0]
        assert fk.column.table.name == "users"
        assert fk.column.name == "id"

    def test_unique_constraint_on_user_id(self):
        """Test that user_id has unique constraint."""
        user_id_column = UserAnalysisTracking.__table__.columns["user_id"]
        assert user_id_column.unique is True

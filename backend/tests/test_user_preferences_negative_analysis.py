"""
Unit tests for UserPreferences model negative_analysis field extension.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.profile import UserPreferences


class TestUserPreferencesNegativeAnalysis:
    """Test cases for UserPreferences negative_analysis field."""

    def test_create_user_preferences_with_negative_analysis(self):
        """Test creating UserPreferences with negative_analysis field."""
        user_id = uuid4()
        negative_analysis_text = (
            "User dislikes overly promotional content and prefers technical discussions. "
            "Avoids posts with excessive emojis and clickbait titles."
        )

        preferences = UserPreferences(
            user_id=user_id, bio="Test bio", negative_analysis=negative_analysis_text
        )

        assert preferences.user_id == user_id
        assert preferences.bio == "Test bio"
        assert preferences.negative_analysis == negative_analysis_text

    def test_create_user_preferences_without_negative_analysis(self):
        """Test creating UserPreferences without negative_analysis field."""
        user_id = uuid4()

        preferences = UserPreferences(user_id=user_id, bio="Test bio")

        assert preferences.user_id == user_id
        assert preferences.bio == "Test bio"
        assert preferences.negative_analysis is None

    def test_negative_analysis_field_is_optional(self):
        """Test that negative_analysis field is optional and nullable."""
        user_id = uuid4()

        # Create with None value
        preferences = UserPreferences(user_id=user_id, negative_analysis=None)

        assert preferences.negative_analysis is None

    def test_negative_analysis_field_accepts_long_text(self):
        """Test that negative_analysis field can handle long text content."""
        user_id = uuid4()

        # Create a long negative analysis text
        long_text = (
            "User consistently dismisses posts that contain: "
            "1. Excessive use of buzzwords like 'revolutionary', 'game-changing', 'disruptive' "
            "2. Posts that are overly self-promotional without providing value "
            "3. Content with too many hashtags (more than 5) "
            "4. Posts that use clickbait titles with phrases like 'You won't believe...' "
            "5. Generic motivational quotes without context "
            "6. Posts that are too long (over 1000 characters) "
            "7. Content that lacks technical depth when discussing technical topics "
            "8. Posts with excessive emojis (more than 3 per post) "
            "9. Content that doesn't align with professional networking goals "
            "10. Posts that are purely personal without professional relevance"
        ) * 3  # Make it even longer

        preferences = UserPreferences(user_id=user_id, negative_analysis=long_text)

        assert preferences.negative_analysis == long_text
        assert len(preferences.negative_analysis) > 1000

    def test_negative_analysis_field_accepts_empty_string(self):
        """Test that negative_analysis field can be set to empty string."""
        user_id = uuid4()

        preferences = UserPreferences(user_id=user_id, negative_analysis="")

        assert preferences.negative_analysis == ""

    def test_update_negative_analysis_field(self):
        """Test updating the negative_analysis field."""
        user_id = uuid4()

        preferences = UserPreferences(
            user_id=user_id, negative_analysis="Initial negative analysis"
        )

        assert preferences.negative_analysis == "Initial negative analysis"

        # Update the field
        new_analysis = (
            "Updated negative analysis: User prefers concise, technical content "
            "and dislikes promotional language."
        )
        preferences.negative_analysis = new_analysis

        assert preferences.negative_analysis == new_analysis

    def test_negative_analysis_with_special_characters(self):
        """Test that negative_analysis field handles special characters."""
        user_id = uuid4()

        special_text = (
            "User dislikes: "
            "• Posts with excessive punctuation!!! "
            "• Content with quotes like \"revolutionary\" or 'game-changing' "
            "• Posts containing symbols: @#$%^&*()_+ "
            "• Unicode characters: 🚀 💡 ⭐ "
            "• Line breaks and\nnewlines "
            "• Tabs\tand\tspaces "
        )

        preferences = UserPreferences(user_id=user_id, negative_analysis=special_text)

        assert preferences.negative_analysis == special_text

    def test_negative_analysis_field_type_validation(self):
        """Test that negative_analysis field has correct type mapping."""
        # Check the column type
        negative_analysis_column = UserPreferences.__table__.columns[
            "negative_analysis"
        ]

        # Should be Text type for long content
        assert str(negative_analysis_column.type) == "TEXT"

        # Should be nullable
        assert negative_analysis_column.nullable is True

    def test_user_preferences_model_with_all_fields(self):
        """Test UserPreferences model with all fields including negative_analysis."""
        user_id = uuid4()

        preferences = UserPreferences(
            user_id=user_id,
            topics_of_interest=["AI", "Machine Learning", "Python"],
            websites=["https://example.com"],
            substacks=["newsletter@example.com"],
            bio="Software engineer specializing in AI",
            timezone="UTC",
            image_generation_style="professional",
            negative_analysis="Dislikes overly promotional content and prefers technical depth",
        )

        assert preferences.user_id == user_id
        assert preferences.topics_of_interest == ["AI", "Machine Learning", "Python"]
        assert preferences.websites == ["https://example.com"]
        assert preferences.substacks == ["newsletter@example.com"]
        assert preferences.bio == "Software engineer specializing in AI"
        assert preferences.timezone == "UTC"
        assert preferences.image_generation_style == "professional"
        assert (
            preferences.negative_analysis
            == "Dislikes overly promotional content and prefers technical depth"
        )

    def test_negative_analysis_field_in_table_columns(self):
        """Test that negative_analysis field is properly defined in table columns."""
        columns = UserPreferences.__table__.columns
        column_names = [col.name for col in columns]

        assert "negative_analysis" in column_names

        # Verify it's the correct column
        negative_analysis_col = columns["negative_analysis"]
        assert negative_analysis_col.nullable is True

    def test_negative_analysis_default_value(self):
        """Test that negative_analysis has proper default value."""
        user_id = uuid4()

        # Create without specifying negative_analysis
        preferences = UserPreferences(user_id=user_id)

        # Should default to None (not empty string)
        assert preferences.negative_analysis is None

    def test_negative_analysis_migration_compatibility(self):
        """Test that the field is compatible with migration requirements."""
        # This test ensures the field was added in a migration-compatible way
        user_id = uuid4()

        # Should be able to create preferences without the field (for existing records)
        preferences_old = UserPreferences(user_id=user_id, bio="Existing user bio")
        assert preferences_old.negative_analysis is None

        # Should be able to add the field later (for new analysis)
        preferences_old.negative_analysis = "Added after migration"
        assert preferences_old.negative_analysis == "Added after migration"

    def test_negative_analysis_json_serializable_content(self):
        """Test that negative_analysis can store JSON-like content if needed."""
        user_id = uuid4()

        # Test storing structured text that could be JSON
        json_like_content = """
        {
            "dismissed_patterns": [
                "excessive_emojis",
                "clickbait_titles",
                "overly_promotional"
            ],
            "feedback_reasons": [
                "too_generic",
                "not_relevant",
                "poor_quality"
            ],
            "content_preferences": {
                "tone": "professional",
                "length": "concise",
                "technical_depth": "high"
            }
        }
        """

        preferences = UserPreferences(
            user_id=user_id, negative_analysis=json_like_content
        )

        assert preferences.negative_analysis == json_like_content

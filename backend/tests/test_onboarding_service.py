"""
Tests for onboarding service functionality.
"""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock

from app.schemas.onboarding import OnboardingUpdate
from app.services.onboarding_service import OnboardingService


class TestOnboardingService:
    """Test cases for OnboardingService."""

    def test_create_user_onboarding(self, db_session: Session):
        """Test creating new onboarding progress."""
        user_id = "test-user-123"

        onboarding = OnboardingService.create_user_onboarding(db_session, user_id)

        assert onboarding.user_id == user_id
        assert onboarding.current_step == 1
        assert not onboarding.is_completed
        assert not onboarding.is_skipped
        assert not onboarding.step_profile_completed

    def test_get_or_create_user_onboarding_existing(self, db_session: Session):
        """Test getting existing onboarding progress."""
        user_id = "test-user-123"

        # Create initial onboarding
        original = OnboardingService.create_user_onboarding(db_session, user_id)
        original.current_step = 3
        db_session.commit()

        # Get existing onboarding
        retrieved = OnboardingService.get_or_create_user_onboarding(db_session, user_id)

        assert retrieved.id == original.id
        assert retrieved.current_step == 3

    def test_get_or_create_user_onboarding_new(self, db_session: Session):
        """Test creating new onboarding when none exists."""
        user_id = "test-user-456"

        onboarding = OnboardingService.get_or_create_user_onboarding(
            db_session, user_id
        )

        assert onboarding.user_id == user_id
        assert onboarding.current_step == 1

    def test_update_onboarding_step_complete(self, db_session: Session):
        """Test updating a specific step to completed."""
        user_id = "test-user-123"

        onboarding = OnboardingService.update_onboarding_step(
            db_session, user_id, 1, True
        )

        assert onboarding.step_profile_completed
        assert onboarding.current_step == 2
        assert not onboarding.is_completed

    def test_update_onboarding_step_uncomplete(self, db_session: Session):
        """Test updating a specific step to uncompleted."""
        user_id = "test-user-123"

        # First complete the step
        OnboardingService.update_onboarding_step(db_session, user_id, 1, True)

        # Then uncomplete it
        onboarding = OnboardingService.update_onboarding_step(
            db_session, user_id, 1, False
        )

        assert not onboarding.step_profile_completed
        assert not onboarding.is_completed

    def test_complete_all_steps(self, db_session: Session):
        """Test completing all onboarding steps."""
        user_id = "test-user-123"

        # Complete all steps
        for step in range(1, 7):
            OnboardingService.update_onboarding_step(db_session, user_id, step, True)

        onboarding = OnboardingService.get_user_onboarding(db_session, user_id)

        assert onboarding.is_completed
        assert onboarding.completed_at is not None
        assert onboarding.step_profile_completed
        assert onboarding.step_content_preferences_completed
        assert onboarding.step_settings_completed
        assert onboarding.step_my_posts_completed
        assert onboarding.step_content_ideas_completed
        assert onboarding.step_posting_schedule_completed

    def test_skip_onboarding(self, db_session: Session):
        """Test skipping the entire onboarding process."""
        user_id = "test-user-123"
        notes = "User chose to skip onboarding"

        onboarding = OnboardingService.skip_onboarding(db_session, user_id, notes)

        assert onboarding.is_skipped
        assert onboarding.skipped_at is not None
        assert onboarding.notes == notes

    def test_update_onboarding_multiple_fields(self, db_session: Session):
        """Test updating multiple onboarding fields at once."""
        user_id = "test-user-123"

        update_data = OnboardingUpdate(
            current_step=3,
            notes="Updated notes",
            step_profile_completed=True,
            step_content_preferences_completed=True,
        )

        onboarding = OnboardingService.update_onboarding(
            db_session, user_id, update_data
        )

        assert onboarding.current_step == 3
        assert onboarding.notes == "Updated notes"
        assert onboarding.step_profile_completed
        assert onboarding.step_content_preferences_completed

    def test_reset_onboarding(self, db_session: Session):
        """Test resetting onboarding progress."""
        user_id = "test-user-123"

        # First complete some steps
        OnboardingService.update_onboarding_step(db_session, user_id, 1, True)
        OnboardingService.update_onboarding_step(db_session, user_id, 2, True)

        # Then reset
        onboarding = OnboardingService.reset_onboarding(db_session, user_id)

        assert onboarding.current_step == 1
        assert not onboarding.is_completed
        assert not onboarding.is_skipped
        assert not onboarding.step_profile_completed
        assert not onboarding.step_content_preferences_completed
        assert onboarding.completed_at is None
        assert onboarding.skipped_at is None

    def test_delete_onboarding(self, db_session: Session):
        """Test deleting onboarding progress."""
        user_id = "test-user-123"

        # Create onboarding
        OnboardingService.create_user_onboarding(db_session, user_id)

        # Delete it
        success = OnboardingService.delete_onboarding(db_session, user_id)

        assert success

        # Verify it's deleted
        onboarding = OnboardingService.get_user_onboarding(db_session, user_id)
        assert onboarding is None

    def test_delete_nonexistent_onboarding(self, db_session: Session):
        """Test deleting non-existent onboarding progress."""
        user_id = "nonexistent-user"

        success = OnboardingService.delete_onboarding(db_session, user_id)

        assert not success


@pytest.fixture
def db_session():
    """Mock database session for testing."""
    session = Mock(spec=Session)
    session.query.return_value.filter.return_value.first.return_value = None
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.delete = Mock()
    return session

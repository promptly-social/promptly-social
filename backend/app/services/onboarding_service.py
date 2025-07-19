"""
Service layer for onboarding functionality.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.onboarding import UserOnboarding
from app.models.user import User
from app.schemas.onboarding import OnboardingUpdate


class OnboardingService:
    """Service class for managing user onboarding progress."""

    @staticmethod
    def get_user_onboarding(db: Session, user_id: str) -> Optional[UserOnboarding]:
        """Get user onboarding progress by user ID."""
        return (
            db.query(UserOnboarding).filter(UserOnboarding.user_id == user_id).first()
        )

    @staticmethod
    def create_user_onboarding(db: Session, user_id: str) -> UserOnboarding:
        """Create new onboarding progress for user."""
        # First, verify the user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist")

        try:
            onboarding = UserOnboarding(user_id=user_id)
            db.add(onboarding)
            db.commit()
            db.refresh(onboarding)
            return onboarding
        except IntegrityError as e:
            db.rollback()
            raise ValueError(f"Failed to create onboarding record: {str(e)}")

    @staticmethod
    def get_or_create_user_onboarding(db: Session, user_id: str) -> UserOnboarding:
        """Get existing onboarding progress or create new one."""
        onboarding = OnboardingService.get_user_onboarding(db, user_id)
        if not onboarding:
            # Verify user exists before creating onboarding record
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(
                    f"Cannot create onboarding for non-existent user: {user_id}"
                )
            onboarding = OnboardingService.create_user_onboarding(db, user_id)
        return onboarding

    @staticmethod
    def update_onboarding_step(
        db: Session, user_id: str, step: int, completed: bool = True
    ) -> UserOnboarding:
        """Update a specific onboarding step."""
        onboarding = OnboardingService.get_or_create_user_onboarding(db, user_id)

        if completed:
            onboarding.mark_step_completed(step)
        else:
            # Allow unchecking steps if needed
            step_mapping = {
                1: "step_profile_completed",
                2: "step_content_preferences_completed",
                3: "step_settings_completed",
                4: "step_my_posts_completed",
                5: "step_content_ideas_completed",
                6: "step_posting_schedule_completed",
            }

            if step in step_mapping:
                setattr(onboarding, step_mapping[step], False)
                # Reset completion status if any step is unchecked
                onboarding.is_completed = False
                onboarding.completed_at = None

        db.commit()
        db.refresh(onboarding)
        return onboarding

    @staticmethod
    def skip_onboarding(
        db: Session, user_id: str, notes: Optional[str] = None
    ) -> UserOnboarding:
        """Skip the entire onboarding process."""
        onboarding = OnboardingService.get_or_create_user_onboarding(db, user_id)
        onboarding.skip_onboarding()
        if notes:
            onboarding.notes = notes

        db.commit()
        db.refresh(onboarding)
        return onboarding

    @staticmethod
    def complete_onboarding(db: Session, user_id: str) -> UserOnboarding:
        """Mark onboarding as completed."""
        onboarding = OnboardingService.get_or_create_user_onboarding(db, user_id)
        
        # Mark all steps as completed
        onboarding.step_profile_completed = True
        onboarding.step_content_preferences_completed = True
        onboarding.step_settings_completed = True
        onboarding.step_my_posts_completed = True
        onboarding.step_content_ideas_completed = True
        onboarding.step_posting_schedule_completed = True
        
        # Mark as completed
        onboarding.is_completed = True
        onboarding.is_skipped = False
        onboarding.completed_at = datetime.utcnow()
        onboarding.skipped_at = None

        db.commit()
        db.refresh(onboarding)
        return onboarding

    @staticmethod
    def update_onboarding(
        db: Session, user_id: str, update_data: OnboardingUpdate
    ) -> UserOnboarding:
        """Update onboarding progress with multiple fields."""
        onboarding = OnboardingService.get_or_create_user_onboarding(db, user_id)

        # Update fields if provided
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(onboarding, field):
                setattr(onboarding, field, value)

        # Check if all steps are completed after update
        if (
            all(
                [
                    onboarding.step_profile_completed,
                    onboarding.step_content_preferences_completed,
                    onboarding.step_settings_completed,
                    onboarding.step_my_posts_completed,
                    onboarding.step_content_ideas_completed,
                    onboarding.step_posting_schedule_completed,
                ]
            )
            and not onboarding.is_completed
        ):
            onboarding.is_completed = True
            onboarding.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(onboarding)
        return onboarding

    @staticmethod
    def reset_onboarding(db: Session, user_id: str) -> UserOnboarding:
        """Reset onboarding progress to start over."""
        onboarding = OnboardingService.get_or_create_user_onboarding(db, user_id)

        # Reset all completion flags
        onboarding.step_profile_completed = False
        onboarding.step_content_preferences_completed = False
        onboarding.step_settings_completed = False
        onboarding.step_my_posts_completed = False
        onboarding.step_content_ideas_completed = False
        onboarding.step_posting_schedule_completed = False

        # Reset status
        onboarding.is_completed = False
        onboarding.is_skipped = False
        onboarding.current_step = 1
        onboarding.completed_at = None
        onboarding.skipped_at = None

        db.commit()
        db.refresh(onboarding)
        return onboarding

    @staticmethod
    def delete_onboarding(db: Session, user_id: str) -> bool:
        """Delete onboarding progress for user."""
        onboarding = OnboardingService.get_user_onboarding(db, user_id)
        if onboarding:
            db.delete(onboarding)
            db.commit()
            return True
        return False

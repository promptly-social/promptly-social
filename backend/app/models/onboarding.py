"""
Onboarding models for tracking user onboarding progress.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.helpers import UUIDType


class UserOnboarding(Base):
    """
    User onboarding model for tracking onboarding progress.

    Features:
    - Track completion status of each onboarding step
    - Allow users to skip onboarding entirely
    - Audit logging with timestamps
    - Flexible step tracking system
    """

    __tablename__ = "user_onboarding"

    # Primary key with UUID support
    id: Mapped[str] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        UUIDType(),
        nullable=False,
        unique=True,
        index=True,
    )

    # Onboarding status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Individual step completion tracking
    step_profile_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    step_content_preferences_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    step_settings_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    step_my_posts_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    step_content_ideas_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    step_posting_schedule_completed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Current step tracking (for UI navigation)
    current_step: Mapped[int] = mapped_column(
        default=1, nullable=False
    )  # 1-6 for the 6 steps

    # Optional notes or feedback from user
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit logging
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    skipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def mark_step_completed(self, step: int) -> None:
        """Mark a specific step as completed."""
        step_mapping = {
            1: "step_profile_completed",
            2: "step_content_preferences_completed",
            3: "step_settings_completed",
            4: "step_my_posts_completed",
            5: "step_content_ideas_completed",
            6: "step_posting_schedule_completed",
        }

        if step in step_mapping:
            setattr(self, step_mapping[step], True)
            self.current_step = min(step + 1, 6)

            # Check if all steps are completed
            if all(
                [
                    self.step_profile_completed,
                    self.step_content_preferences_completed,
                    self.step_settings_completed,
                    self.step_my_posts_completed,
                    self.step_content_ideas_completed,
                    self.step_posting_schedule_completed,
                ]
            ):
                self.is_completed = True
                self.completed_at = datetime.utcnow()

    def skip_onboarding(self) -> None:
        """Skip the entire onboarding process."""
        self.is_skipped = True
        self.skipped_at = datetime.utcnow()

    def get_progress_percentage(self) -> float:
        """Calculate onboarding progress as percentage."""
        if self.is_skipped or self.is_completed:
            return 100.0

        completed_steps = sum(
            [
                self.step_profile_completed,
                self.step_content_preferences_completed,
                self.step_settings_completed,
                self.step_my_posts_completed,
                self.step_content_ideas_completed,
                self.step_posting_schedule_completed,
            ]
        )

        return (completed_steps / 6) * 100

    def __repr__(self) -> str:
        return f"<UserOnboarding(id={self.id}, user_id={self.user_id}, progress={self.get_progress_percentage():.1f}%)>"

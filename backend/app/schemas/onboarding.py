"""
Pydantic schemas for onboarding endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OnboardingStepUpdate(BaseModel):
    """Schema for updating a specific onboarding step."""

    step: int = Field(..., ge=1, le=6, description="Step number (1-6)")
    completed: bool = Field(default=True, description="Whether the step is completed")


class OnboardingSkip(BaseModel):
    """Schema for skipping onboarding."""

    notes: Optional[str] = Field(
        None, description="Optional notes about why onboarding was skipped"
    )


class OnboardingResponse(BaseModel):
    """Schema for onboarding progress response."""

    id: UUID
    user_id: UUID
    is_completed: bool
    is_skipped: bool
    step_profile_completed: bool
    step_content_preferences_completed: bool
    step_settings_completed: bool
    step_my_posts_completed: bool
    step_content_ideas_completed: bool
    step_posting_schedule_completed: bool
    current_step: int
    progress_percentage: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    skipped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OnboardingCreate(BaseModel):
    """Schema for creating onboarding progress."""

    user_id: str
    current_step: int = Field(default=1, ge=1, le=6)
    notes: Optional[str] = None


class OnboardingUpdate(BaseModel):
    """Schema for updating onboarding progress."""

    current_step: Optional[int] = Field(None, ge=1, le=6)
    notes: Optional[str] = None
    step_profile_completed: Optional[bool] = None
    step_content_preferences_completed: Optional[bool] = None
    step_settings_completed: Optional[bool] = None
    step_my_posts_completed: Optional[bool] = None
    step_content_ideas_completed: Optional[bool] = None
    step_posting_schedule_completed: Optional[bool] = None

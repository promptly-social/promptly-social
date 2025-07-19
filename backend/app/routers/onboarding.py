"""
API routes for onboarding functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.dependencies import get_current_user_with_rls_sync as get_current_user
from app.schemas.auth import UserResponse
from app.schemas.onboarding import (
    OnboardingResponse,
    OnboardingSkip,
    OnboardingStepUpdate,
    OnboardingUpdate,
)
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/", response_model=OnboardingResponse)
def get_onboarding_progress(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Get current user's onboarding progress."""
    try:
        onboarding = OnboardingService.get_or_create_user_onboarding(
            db, current_user.id
        )

        # Calculate progress percentage
        progress_percentage = onboarding.get_progress_percentage()

        return OnboardingResponse(
            id=onboarding.id,
            user_id=onboarding.user_id,
            is_completed=onboarding.is_completed,
            is_skipped=onboarding.is_skipped,
            step_profile_completed=onboarding.step_profile_completed,
            step_content_preferences_completed=onboarding.step_content_preferences_completed,
            step_settings_completed=onboarding.step_settings_completed,
            step_my_posts_completed=onboarding.step_my_posts_completed,
            step_content_ideas_completed=onboarding.step_content_ideas_completed,
            step_posting_schedule_completed=onboarding.step_posting_schedule_completed,
            current_step=onboarding.current_step,
            progress_percentage=progress_percentage,
            notes=onboarding.notes,
            created_at=onboarding.created_at,
            updated_at=onboarding.updated_at,
            completed_at=onboarding.completed_at,
            skipped_at=onboarding.skipped_at,
        )
    except ValueError as e:
        # Handle user validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get onboarding progress: {str(e)}",
        )


@router.put("/step", response_model=OnboardingResponse)
def update_onboarding_step(
    step_update: OnboardingStepUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Update a specific onboarding step."""
    try:
        onboarding = OnboardingService.update_onboarding_step(
            db, current_user.id, step_update.step, step_update.completed
        )

        progress_percentage = onboarding.get_progress_percentage()

        return OnboardingResponse(
            id=onboarding.id,
            user_id=onboarding.user_id,
            is_completed=onboarding.is_completed,
            is_skipped=onboarding.is_skipped,
            step_profile_completed=onboarding.step_profile_completed,
            step_content_preferences_completed=onboarding.step_content_preferences_completed,
            step_settings_completed=onboarding.step_settings_completed,
            step_my_posts_completed=onboarding.step_my_posts_completed,
            step_content_ideas_completed=onboarding.step_content_ideas_completed,
            step_posting_schedule_completed=onboarding.step_posting_schedule_completed,
            current_step=onboarding.current_step,
            progress_percentage=progress_percentage,
            notes=onboarding.notes,
            created_at=onboarding.created_at,
            updated_at=onboarding.updated_at,
            completed_at=onboarding.completed_at,
            skipped_at=onboarding.skipped_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update onboarding step: {str(e)}",
        )


@router.post("/skip", response_model=OnboardingResponse)
def skip_onboarding(
    skip_data: OnboardingSkip,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Skip the entire onboarding process."""
    try:
        onboarding = OnboardingService.skip_onboarding(
            db, current_user.id, skip_data.notes
        )

        progress_percentage = onboarding.get_progress_percentage()

        return OnboardingResponse(
            id=onboarding.id,
            user_id=onboarding.user_id,
            is_completed=onboarding.is_completed,
            is_skipped=onboarding.is_skipped,
            step_profile_completed=onboarding.step_profile_completed,
            step_content_preferences_completed=onboarding.step_content_preferences_completed,
            step_settings_completed=onboarding.step_settings_completed,
            step_my_posts_completed=onboarding.step_my_posts_completed,
            step_content_ideas_completed=onboarding.step_content_ideas_completed,
            step_posting_schedule_completed=onboarding.step_posting_schedule_completed,
            current_step=onboarding.current_step,
            progress_percentage=progress_percentage,
            notes=onboarding.notes,
            created_at=onboarding.created_at,
            updated_at=onboarding.updated_at,
            completed_at=onboarding.completed_at,
            skipped_at=onboarding.skipped_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip onboarding: {str(e)}",
        )


@router.put("/", response_model=OnboardingResponse)
def update_onboarding_progress(
    update_data: OnboardingUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Update onboarding progress with multiple fields."""
    try:
        onboarding = OnboardingService.update_onboarding(
            db, current_user.id, update_data
        )

        progress_percentage = onboarding.get_progress_percentage()

        return OnboardingResponse(
            id=onboarding.id,
            user_id=onboarding.user_id,
            is_completed=onboarding.is_completed,
            is_skipped=onboarding.is_skipped,
            step_profile_completed=onboarding.step_profile_completed,
            step_content_preferences_completed=onboarding.step_content_preferences_completed,
            step_settings_completed=onboarding.step_settings_completed,
            step_my_posts_completed=onboarding.step_my_posts_completed,
            step_content_ideas_completed=onboarding.step_content_ideas_completed,
            step_posting_schedule_completed=onboarding.step_posting_schedule_completed,
            current_step=onboarding.current_step,
            progress_percentage=progress_percentage,
            notes=onboarding.notes,
            created_at=onboarding.created_at,
            updated_at=onboarding.updated_at,
            completed_at=onboarding.completed_at,
            skipped_at=onboarding.skipped_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update onboarding: {str(e)}",
        )


@router.post("/complete", response_model=OnboardingResponse)
def complete_onboarding(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Mark onboarding as completed."""
    try:
        onboarding = OnboardingService.complete_onboarding(db, current_user.id)

        progress_percentage = onboarding.get_progress_percentage()

        return OnboardingResponse(
            id=onboarding.id,
            user_id=onboarding.user_id,
            is_completed=onboarding.is_completed,
            is_skipped=onboarding.is_skipped,
            step_profile_completed=onboarding.step_profile_completed,
            step_content_preferences_completed=onboarding.step_content_preferences_completed,
            step_settings_completed=onboarding.step_settings_completed,
            step_my_posts_completed=onboarding.step_my_posts_completed,
            step_content_ideas_completed=onboarding.step_content_ideas_completed,
            step_posting_schedule_completed=onboarding.step_posting_schedule_completed,
            current_step=onboarding.current_step,
            progress_percentage=progress_percentage,
            notes=onboarding.notes,
            created_at=onboarding.created_at,
            updated_at=onboarding.updated_at,
            completed_at=onboarding.completed_at,
            skipped_at=onboarding.skipped_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}",
        )


@router.post("/reset", response_model=OnboardingResponse)
def reset_onboarding(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Reset onboarding progress to start over."""
    try:
        onboarding = OnboardingService.reset_onboarding(db, current_user.id)

        progress_percentage = onboarding.get_progress_percentage()

        return OnboardingResponse(
            id=onboarding.id,
            user_id=onboarding.user_id,
            is_completed=onboarding.is_completed,
            is_skipped=onboarding.is_skipped,
            step_profile_completed=onboarding.step_profile_completed,
            step_content_preferences_completed=onboarding.step_content_preferences_completed,
            step_settings_completed=onboarding.step_settings_completed,
            step_my_posts_completed=onboarding.step_my_posts_completed,
            step_content_ideas_completed=onboarding.step_content_ideas_completed,
            step_posting_schedule_completed=onboarding.step_posting_schedule_completed,
            current_step=onboarding.current_step,
            progress_percentage=progress_percentage,
            notes=onboarding.notes,
            created_at=onboarding.created_at,
            updated_at=onboarding.updated_at,
            completed_at=onboarding.completed_at,
            skipped_at=onboarding.skipped_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset onboarding: {str(e)}",
        )


@router.delete("/")
def delete_onboarding(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_sync_db),
):
    """Delete onboarding progress for current user."""
    try:
        success = OnboardingService.delete_onboarding(db, current_user.id)
        if success:
            return {"message": "Onboarding progress deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onboarding progress not found",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete onboarding: {str(e)}",
        )

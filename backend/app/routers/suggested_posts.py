"""
Suggested Posts router with endpoints for suggested posts management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.routers.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.suggested_posts import (
    SuggestedPostCreate,
    SuggestedPostListResponse,
    SuggestedPostResponse,
    SuggestedPostUpdate,
    PostFeedback,
)
from app.services.suggested_posts import SuggestedPostsService

# Create router
router = APIRouter(prefix="/suggested-posts", tags=["suggested-posts"])


@router.get("/", response_model=SuggestedPostListResponse)
async def get_suggested_posts(
    platform: Optional[str] = Query(None),
    status: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get suggested posts with filtering and pagination."""
    try:
        service = SuggestedPostsService(db)
        result = await service.get_suggested_posts_list(
            user_id=current_user.id,
            platform=platform,
            status=status,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
        )
        return SuggestedPostListResponse(**result)
    except Exception as e:
        logger.error(f"Error getting suggested posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch suggested posts",
        )


@router.get("/{post_id}", response_model=SuggestedPostResponse)
async def get_suggested_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific suggested post."""
    try:
        service = SuggestedPostsService(db)
        post = await service.get_suggested_post(current_user.id, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggested post not found"
            )

        return SuggestedPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggested post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch suggested post",
        )


@router.post(
    "/", response_model=SuggestedPostResponse, status_code=status.HTTP_201_CREATED
)
async def create_suggested_post(
    post_data: SuggestedPostCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new suggested post."""
    try:
        service = SuggestedPostsService(db)
        post = await service.create_suggested_post(current_user.id, post_data)
        return SuggestedPostResponse.model_validate(post)
    except Exception as e:
        logger.error(f"Error creating suggested post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create suggested post",
        )


@router.put("/{post_id}", response_model=SuggestedPostResponse)
async def update_suggested_post(
    post_id: UUID,
    update_data: SuggestedPostUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a suggested post."""
    try:
        service = SuggestedPostsService(db)
        post = await service.update_suggested_post(
            current_user.id, post_id, update_data
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggested post not found"
            )

        return SuggestedPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating suggested post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update suggested post",
        )


@router.delete("/{post_id}")
async def delete_suggested_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a suggested post."""
    try:
        service = SuggestedPostsService(db)
        deleted = await service.delete_suggested_post(current_user.id, post_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggested post not found"
            )

        return {"message": "Suggested post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting suggested post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete suggested post",
        )


@router.post("/{post_id}/dismiss", response_model=SuggestedPostResponse)
async def dismiss_suggested_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Mark a suggested post as dismissed."""
    try:
        service = SuggestedPostsService(db)
        post = await service.dismiss_suggested_post(current_user.id, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggested post not found"
            )

        return SuggestedPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing suggested post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dismiss suggested post",
        )


@router.post("/{post_id}/mark-posted", response_model=SuggestedPostResponse)
async def mark_post_as_posted(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Mark a suggested post as posted."""
    try:
        service = SuggestedPostsService(db)
        post = await service.mark_as_posted(current_user.id, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggested post not found"
            )

        return SuggestedPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking suggested post as posted {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark post as posted",
        )


@router.post("/{post_id}/feedback", response_model=SuggestedPostResponse)
async def submit_post_feedback(
    post_id: UUID,
    feedback: PostFeedback,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Submit feedback for a suggested post."""
    try:
        service = SuggestedPostsService(db)
        post = await service.submit_feedback(
            current_user.id, post_id, feedback.feedback_type, feedback.comment
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Suggested post not found"
            )

        return SuggestedPostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback",
        )

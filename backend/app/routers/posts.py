"""
Posts router with endpoints for posts management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.routers.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.posts import (
    PostCreate,
    PostListResponse,
    PostResponse,
    PostUpdate,
    PostFeedback,
)
from app.services.posts import PostsService

# Create router
router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=PostListResponse)
async def get_posts(
    platform: Optional[str] = Query(None),
    post_status: Optional[List[str]] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get posts with filtering and pagination."""
    try:
        service = PostsService(db)
        result = await service.get_posts_list(
            user_id=current_user.id,
            platform=platform,
            status=post_status,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
        )
        return PostListResponse(**result)
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch posts",
        )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific post."""
    try:
        service = PostsService(db)
        post = await service.get_post(current_user.id, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return PostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch post",
        )


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new post."""
    try:
        service = PostsService(db)
        post = await service.create_post(current_user.id, post_data)
        return PostResponse.model_validate(post)
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create post",
        )


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    update_data: PostUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a post."""
    try:
        service = PostsService(db)
        post = await service.update_post(current_user.id, post_id, update_data)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return PostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update post",
        )


@router.delete("/{post_id}")
async def delete_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a post."""
    try:
        service = PostsService(db)
        deleted = await service.delete_post(current_user.id, post_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return {"message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete post",
        )


@router.post("/{post_id}/dismiss", response_model=PostResponse)
async def dismiss_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Mark a post as dismissed."""
    try:
        service = PostsService(db)
        post = await service.dismiss_post(current_user.id, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return PostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to dismiss post",
        )


@router.post("/{post_id}/mark-posted", response_model=PostResponse)
async def mark_post_as_posted(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Mark a post as posted."""
    try:
        service = PostsService(db)
        post = await service.mark_as_posted(current_user.id, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return PostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking post as posted {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark post as posted",
        )


@router.post("/{post_id}/feedback", response_model=PostResponse)
async def submit_post_feedback(
    post_id: UUID,
    feedback: PostFeedback,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Submit feedback for a post."""
    try:
        service = PostsService(db)
        post = await service.submit_feedback(
            current_user.id, post_id, feedback.feedback_type, feedback.comment
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return PostResponse.model_validate(post)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback",
        )

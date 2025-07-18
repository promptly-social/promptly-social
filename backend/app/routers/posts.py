"""
Posts router with endpoints for posts management.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    BackgroundTasks,
    UploadFile,
    File,
)
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
    PostBatchUpdate,
    PostCountsResponse,
    PostMediaResponse,
    ImagePromptRequest,
    ImagePromptResponse,
    PostScheduleRequest,
    PostScheduleResponse,
)
from app.services.posts import PostsService
from app.services.post_schedule import PostScheduleService
from app.core.config import settings
from app.utils.gcp import trigger_gcp_cloud_run
from app.services.image_gen_service import ImageGenService

# Create router
router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=PostListResponse)
async def get_posts(
    platform: Optional[str] = Query(None),
    post_status: Optional[List[str]] = Query(None, alias="status"),
    after_date: Optional[datetime] = Query(None),
    before_date: Optional[datetime] = Query(None),
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
            after_date=after_date,
            before_date=before_date,
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


@router.get("/counts", response_model=PostCountsResponse)
async def get_post_counts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get counts of posts by status categories for the current user."""
    try:
        service = PostsService(db)
        counts = await service.get_post_counts(current_user.id)
        return PostCountsResponse(**counts)
    except Exception as e:
        logger.error(f"Error getting post counts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch post counts",
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


@router.post("/{post_id}/media", response_model=List[PostMediaResponse])
async def upload_post_media_files(
    post_id: UUID,
    files: List[UploadFile] = File(...),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Upload one or more media files for a post."""
    try:
        service = PostsService(db)
        media_files = await service.upload_media_for_post(
            current_user.id, post_id, files
        )
        return [PostMediaResponse.model_validate(mf) for mf in media_files]
    except Exception as e:
        logger.error(f"Error uploading media for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload media",
        )


@router.get("/{post_id}/media", response_model=List[PostMediaResponse])
async def get_post_media(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Retrieve signed media URLs for a post so that media can be displayed securely."""
    try:
        service = PostsService(db)
        media_items = await service.get_signed_media_for_post(current_user.id, post_id)
        return [PostMediaResponse.model_validate(m) for m in media_items]
    except Exception as e:
        logger.error(f"Error fetching media for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch media for post",
        )


@router.delete("/{post_id}/media/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_media(
    post_id: UUID,
    media_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a media file from a post."""
    try:
        service = PostsService(db)
        await service.delete_media_for_post(current_user.id, post_id, media_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting media {media_id} for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete media",
        )


@router.post("/batch-update", response_model=PostListResponse)
async def batch_update_posts(
    posts: PostBatchUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Batch update posts."""
    try:
        service = PostsService(db)
        posts = await service.batch_update_posts(current_user.id, posts)
        return PostListResponse.model_validate(posts)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch updating posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch update posts",
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


@router.post("/{post_id}/publish", status_code=status.HTTP_200_OK)
async def publish_post(
    post_id: UUID,
    platform: str = Query("linkedin", enum=["linkedin"]),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Publish a post to the specified platform."""
    try:
        service = PostsService(db)
        result = await service.publish_post(current_user.id, post_id, platform)

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return {"message": "Post published successfully", "details": result}
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing post {post_id} to {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish post: {e}",
        )


@router.post("/{post_id}/schedule", response_model=PostScheduleResponse)
async def schedule_post(
    post_id: UUID,
    schedule_data: PostScheduleRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Schedule a post for publishing."""
    try:
        schedule_service = PostScheduleService(db)
        success = await schedule_service.schedule_post(
            current_user.id, post_id, schedule_data.scheduled_at, schedule_data.timezone
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or failed to schedule",
            )

        return PostScheduleResponse(
            success=True,
            scheduled_at=schedule_data.scheduled_at,
            scheduler_job_name="unified-scheduler",  # Indicate unified scheduler is used
            message="Post scheduled successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule post",
        )


@router.delete("/{post_id}/schedule", response_model=PostScheduleResponse)
async def unschedule_post(
    post_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Remove a post from schedule."""
    try:
        schedule_service = PostScheduleService(db)
        success = await schedule_service.unschedule_post(current_user.id, post_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        return PostScheduleResponse(
            success=True,
            scheduled_at=None,
            scheduler_job_name="",
            message="Post unscheduled successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unscheduling post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unschedule post",
        )


@router.put("/{post_id}/schedule", response_model=PostScheduleResponse)
async def reschedule_post(
    post_id: UUID,
    schedule_data: PostScheduleRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Reschedule a post to a new time."""
    try:
        schedule_service = PostScheduleService(db)
        success = await schedule_service.reschedule_post(
            current_user.id, post_id, schedule_data.scheduled_at, schedule_data.timezone
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found or failed to reschedule",
            )

        return PostScheduleResponse(
            success=True,
            scheduled_at=schedule_data.scheduled_at,
            scheduler_job_name="unified-scheduler",  # Indicate unified scheduler is used
            message="Post rescheduled successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reschedule post",
        )


@router.post("/generate-suggestions", status_code=status.HTTP_202_ACCEPTED)
async def generate_suggestions(
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
):
    """Trigger generation of new post suggestions in the background."""
    if not settings.gcp_generate_suggestions_function_url:
        logger.error("gcp_generate_suggestions_function_url is not configured.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Suggestion generation service is not configured.",
        )

    async def trigger_generation_task():
        """Wrapper task for error handling."""
        try:
            logger.info(f"Triggering suggestion generation for user {current_user.id}")
            await trigger_gcp_cloud_run(
                target_url=settings.gcp_generate_suggestions_function_url,
                payload={"user_id": str(current_user.id)},
                timeout=300.0,  # 5 minutes
            )
            logger.info(f"Suggestion generation triggered for user {current_user.id}")
        except Exception as e:
            logger.error(
                f"Error triggering suggestion generation for user {current_user.id}: {e}"
            )

    background_tasks.add_task(trigger_generation_task)

    return {"message": "Post generation started. Please check back in a few minutes."}


@router.post("/image-prompt", response_model=ImagePromptResponse)
async def generate_image_prompt(
    postContent: ImagePromptRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Generate an image prompt for a post."""
    try:
        service = ImageGenService()
        result = await service.generate_image_prompt(postContent.postContent)
        return ImagePromptResponse(imagePrompt=result.output)
    except Exception as e:
        logger.error(
            f"Error generating image prompt for post {postContent.postContent}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate image prompt",
        )

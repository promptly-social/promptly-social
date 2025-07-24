"""
User Topics router with endpoints for topic management.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.dependencies import get_current_user_with_rls as get_current_user
from app.schemas.auth import UserResponse
from app.schemas.user_topics import (
    UserTopicCreate,
    UserTopicResponse,
    UserTopicUpdate,
    UserTopicsListResponse,
    BulkTopicCreateRequest,
    TopicColorsResponse,
    TopicColorMap,
)
from app.services.user_topics import UserTopicsService

# Create router
router = APIRouter(prefix="/user-topics", tags=["user-topics"])


@router.get("/", response_model=UserTopicsListResponse)
async def get_user_topics(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get all topics for the current user."""
    try:
        service = UserTopicsService(db)
        topics = await service.get_user_topics(current_user.id)

        return UserTopicsListResponse(
            topics=[UserTopicResponse.model_validate(topic) for topic in topics],
            total=len(topics),
        )
    except Exception as e:
        logger.error(f"Error getting user topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user topics",
        )


@router.get("/colors", response_model=TopicColorsResponse)
async def get_topic_colors(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get topic-color mapping for the current user."""
    try:
        service = UserTopicsService(db)
        topic_colors_map = await service.get_topic_colors_map(current_user.id)

        topic_colors = [
            TopicColorMap(topic=topic, color=color)
            for topic, color in topic_colors_map.items()
        ]

        return TopicColorsResponse(topic_colors=topic_colors)
    except Exception as e:
        logger.error(f"Error getting topic colors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch topic colors",
        )


@router.get("/{topic_id}", response_model=UserTopicResponse)
async def get_user_topic(
    topic_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific topic for the current user."""
    try:
        service = UserTopicsService(db)
        topic = await service.get_user_topic(current_user.id, topic_id)

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found"
            )

        return UserTopicResponse.model_validate(topic)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user topic {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user topic",
        )


@router.post("/", response_model=UserTopicResponse, status_code=status.HTTP_201_CREATED)
async def create_user_topic(
    topic_data: UserTopicCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new topic for the current user."""
    try:
        service = UserTopicsService(db)
        topic = await service.create_user_topic(current_user.id, topic_data)

        return UserTopicResponse.model_validate(topic)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user topic",
        )


@router.post(
    "/bulk", response_model=List[UserTopicResponse], status_code=status.HTTP_201_CREATED
)
async def bulk_create_topics(
    request: BulkTopicCreateRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Bulk create topics for the current user."""
    try:
        service = UserTopicsService(db)
        new_topics = await service.bulk_create_topics(current_user.id, request.topics)

        return [UserTopicResponse.model_validate(topic) for topic in new_topics]
    except Exception as e:
        logger.error(f"Error bulk creating topics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create topics",
        )


@router.post("/sync-from-posts", response_model=List[UserTopicResponse])
async def sync_topics_from_posts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Sync topics from user's posts to create missing UserTopic entries."""
    try:
        service = UserTopicsService(db)
        new_topics = await service.sync_topics_from_posts(current_user.id)

        return [UserTopicResponse.model_validate(topic) for topic in new_topics]
    except Exception as e:
        logger.error(f"Error syncing topics from posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync topics from posts",
        )


@router.put("/{topic_id}", response_model=UserTopicResponse)
async def update_user_topic(
    topic_id: UUID,
    update_data: UserTopicUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a topic for the current user."""
    try:
        service = UserTopicsService(db)
        topic = await service.update_user_topic(current_user.id, topic_id, update_data)

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found"
            )

        return UserTopicResponse.model_validate(topic)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user topic {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user topic",
        )


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_topic(
    topic_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a topic for the current user."""
    try:
        service = UserTopicsService(db)
        success = await service.delete_user_topic(current_user.id, topic_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found"
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user topic {topic_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user topic",
        )

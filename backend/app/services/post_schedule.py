"""
Service for managing post scheduling using unified scheduler approach.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.posts import Post


class PostScheduleService:
    """Business logic for post scheduling using unified scheduler approach."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def schedule_post(
        self,
        user_id: UUID,
        post_id: UUID,
        scheduled_at: datetime,
        timezone: str = "UTC",
    ) -> bool:
        """Schedule a post by updating database only - unified scheduler handles publishing."""
        try:
            # Get the post
            query = select(Post).where(Post.id == post_id, Post.user_id == user_id)
            result = await self.db.execute(query)
            post = result.scalar_one_or_none()

            if not post:
                logger.error(f"Post {post_id} not found for user {user_id}")
                return False

            # Update post with scheduling information
            post.scheduled_at = scheduled_at
            post.status = "scheduled"
            # Clear any previous scheduler job name (legacy field)
            post.scheduler_job_name = None
            # Clear any previous sharing errors
            post.sharing_error = None

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(
                f"Scheduled post {post_id} for {scheduled_at} (unified scheduler)"
            )
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error scheduling post {post_id}: {e}")
            return False

    async def unschedule_post(self, user_id: UUID, post_id: UUID) -> bool:
        """Unschedule a post by updating database only."""
        try:
            # Get the post
            query = select(Post).where(Post.id == post_id, Post.user_id == user_id)
            result = await self.db.execute(query)
            post = result.scalar_one_or_none()

            if not post:
                logger.error(f"Post {post_id} not found for user {user_id}")
                return False

            # Update post to remove scheduling
            post.scheduled_at = None
            post.scheduler_job_name = None
            post.status = "draft"  # Reset to draft status
            post.sharing_error = None

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(f"Unscheduled post {post_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error unscheduling post {post_id}: {e}")
            return False

    async def reschedule_post(
        self,
        user_id: UUID,
        post_id: UUID,
        new_scheduled_at: datetime,
        timezone: str = "UTC",
    ) -> bool:
        """Reschedule a post to a new time by updating database only."""
        try:
            # Get the post
            query = select(Post).where(Post.id == post_id, Post.user_id == user_id)
            result = await self.db.execute(query)
            post = result.scalar_one_or_none()

            if not post:
                logger.error(f"Post {post_id} not found for user {user_id}")
                return False

            # Update post with new scheduling information
            post.scheduled_at = new_scheduled_at
            post.status = "scheduled"
            # Clear legacy scheduler job name
            post.scheduler_job_name = None
            # Clear any previous sharing errors
            post.sharing_error = None

            await self.db.commit()
            await self.db.refresh(post)

            logger.info(
                f"Rescheduled post {post_id} to {new_scheduled_at} (unified scheduler)"
            )
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error rescheduling post {post_id}: {e}")
            return False

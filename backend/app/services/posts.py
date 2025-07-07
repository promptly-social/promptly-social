"""
Posts service for business logic.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.posts import Post
from app.schemas.posts import PostCreate, PostUpdate, PostBatchUpdate


class PostsService:
    """Service for posts operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_post_by_ids(self, post_ids: List[UUID]) -> List[Post]:
        """Get a post by id."""
        query = select(Post).where(Post.id.in_(post_ids))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_posts_list(
        self,
        user_id: UUID,
        platform: Optional[str] = None,
        status: Optional[List[str]] = None,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None,
        page: int = 1,
        size: int = 20,
        order_by: str = "scheduled_at",
        order_direction: str = "desc",
    ) -> Dict:
        """Get posts with filtering and pagination."""
        try:
            # Build filters
            filters = [Post.user_id == user_id]

            if platform:
                filters.append(Post.platform == platform)

            if status:
                filters.append(Post.status.in_(status))

            if after_date:
                if after_date.tzinfo is None:
                    after_date = after_date.replace(
                        tzinfo=datetime.now().astimezone().tzinfo
                    )
                filters.append(Post.scheduled_at >= after_date)

            if before_date:
                if before_date.tzinfo is None:
                    before_date = before_date.replace(
                        tzinfo=datetime.now().astimezone().tzinfo
                    )
                filters.append(Post.scheduled_at <= before_date)

            # Build query for total count
            count_query = select(func.count()).select_from(Post).where(and_(*filters))
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Build main query with pagination
            offset = (page - 1) * size

            # Order by
            order_column = getattr(Post, order_by, Post.created_at)
            if order_direction.lower() == "desc":
                order_column = desc(order_column)

            query = (
                select(Post)
                .where(and_(*filters))
                .order_by(order_column)
                .offset(offset)
                .limit(size)
            )

            result = await self.db.execute(query)
            posts = result.scalars().all()

            return {
                "items": posts,
                "total": total,
                "page": page,
                "size": size,
                "has_next": total > page * size,
            }

        except Exception as e:
            logger.error(f"Error getting posts list: {e}")
            raise

    async def get_post(self, user_id: UUID, post_id: UUID) -> Optional[Post]:
        """Get a specific post."""
        try:
            query = select(Post).where(
                and_(
                    Post.id == post_id,
                    Post.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            raise

    async def create_post(self, user_id: UUID, post_data: PostCreate) -> Post:
        """Create a new post."""
        try:
            post = Post(
                user_id=user_id,
                idea_bank_id=post_data.idea_bank_id,
                title=post_data.title,
                content=post_data.content,
                platform=post_data.platform,
                topics=post_data.topics,
                recommendation_score=post_data.recommendation_score,
                status=post_data.status,
            )

            self.db.add(post)
            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating post: {e}")
            raise

    async def update_post(
        self, user_id: UUID, post_id: UUID, update_data: PostUpdate
    ) -> Optional[Post]:
        """Update a post."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(post, field, value)

            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating post {post_id}: {e}")
            raise

    async def batch_update_posts(
        self, user_id: UUID, posts: PostBatchUpdate
    ) -> List[Post]:
        """Batch update posts."""
        try:
            items = posts.posts
            for post in items:
                await self.update_post(user_id, post.id, post)

            updated_posts = await self._get_post_by_ids([post.id for post in items])

            return {
                "items": updated_posts,
                "total": len(updated_posts),
                "page": 1,
                "size": len(updated_posts),
                "has_next": False,
            }
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error batch updating posts: {e}")
            raise

    async def delete_post(self, user_id: UUID, post_id: UUID) -> bool:
        """Delete a post."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return False

            await self.db.delete(post)
            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting post {post_id}: {e}")
            raise

    async def dismiss_post(self, user_id: UUID, post_id: UUID) -> Optional[Post]:
        """Mark a post as dismissed."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            post.status = "dismissed"
            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error dismissing post {post_id}: {e}")
            raise

    async def mark_as_posted(self, user_id: UUID, post_id: UUID) -> Optional[Post]:
        """Mark a post as posted."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            post.status = "posted"
            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking post as posted {post_id}: {e}")
            raise

    async def submit_feedback(
        self,
        user_id: UUID,
        post_id: UUID,
        feedback_type: str,
        comment: Optional[str] = None,
    ) -> Optional[Post]:
        """Submit user feedback for a post."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            post.user_feedback = feedback_type
            post.feedback_comment = comment
            post.feedback_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error submitting feedback for post {post_id}: {e}")
            raise

    async def schedule_post(
        self, user_id: UUID, post_id: UUID, scheduled_at: str
    ) -> Optional[Post]:
        """Schedule a post for publishing."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            # Parse the scheduled_at string to datetime
            if isinstance(scheduled_at, str):
                scheduled_at = datetime.fromisoformat(
                    scheduled_at.replace("Z", "+00:00")
                )

            post.status = "scheduled"
            post.scheduled_at = scheduled_at

            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error scheduling post {post_id}: {e}")
            raise

    async def unschedule_post(self, user_id: UUID, post_id: UUID) -> Optional[Post]:
        """Remove a post from schedule."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            post.status = "saved"
            post.scheduled_at = None

            await self.db.commit()
            await self.db.refresh(post)
            return post

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error unscheduling post {post_id}: {e}")
            raise

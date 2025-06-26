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
from app.schemas.posts import PostCreate, PostUpdate


class PostsService:
    """Service for posts operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_posts_list(
        self,
        user_id: UUID,
        platform: Optional[str] = None,
        status: Optional[List[str]] = None,
        page: int = 1,
        size: int = 20,
        order_by: str = "created_at",
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

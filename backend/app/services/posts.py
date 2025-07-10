"""
Posts service for business logic.
"""

import math
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import UploadFile

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.posts import Post
from app.schemas.posts import PostCreate, PostUpdate, PostBatchUpdate, PostResponse
from app.services.profile import ProfileService
from app.services.linkedin_service import LinkedInService
from app.core.config import settings
from supabase import create_client, Client

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


class PostsService:
    """Service for posts operations."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def upload_media_for_post(
        self, user_id: UUID, post_id: UUID, file: UploadFile
    ) -> Post:
        """Uploads media for a post to Supabase storage and updates the post."""
        post = await self.get_post(user_id, post_id)
        if not post:
            raise Exception("Post not found")

        file_path = f"{user_id}/{post_id}/{file.filename}"

        # Upload to Supabase Storage
        try:
            supabase.storage.from_("post-media").upload(
                path=file_path,
                file=await file.read(),
                file_options={"content-type": file.content_type},
            )
        except Exception as e:
            logger.error(f"Error uploading to Supabase Storage: {e}")
            raise

        media_url = supabase.storage.from_("post-media").get_public_url(file_path)

        # Register upload with LinkedIn
        profile_service = ProfileService(self._db)
        connection = await profile_service.get_social_connection(user_id, "linkedin")
        if not connection:
            raise Exception("LinkedIn connection not found")

        linkedin_service = LinkedInService(connection)

        # Determine media type from content type
        media_type = "image" if "image" in file.content_type else "video"

        registration_response = await linkedin_service._register_upload(media_type)
        upload_url = registration_response["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn = registration_response["value"]["asset"]

        # The _upload_media function expects a local file path.
        # This needs to be adapted to work with the uploaded file content.
        # For now, let's assume we can write it to a temp file.
        # This part of the logic will need refinement.
        import tempfile

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file.filename
        ) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        await linkedin_service._upload_media(upload_url, temp_file_path)

        # Update post with media details
        update_data = PostUpdate(
            media_type=media_type,
            media_url=media_url,
            linkedin_asset_urn=asset_urn,
        )
        updated_post = await self.update_post(user_id, post_id, update_data)

        import os

        os.unlink(temp_file_path)

        return updated_post

    async def _get_post_by_ids(self, post_ids: List[UUID]) -> List[Post]:
        """Get a post by id."""
        query = select(Post).where(Post.id.in_(post_ids))
        result = await self._db.execute(query)
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
        order_by: str = "created_at",
        order_direction: str = "desc",
    ) -> Dict[str, Any]:
        """Get a paginated list of posts for a user."""
        try:
            offset = (page - 1) * size

            filters = [Post.user_id == user_id]
            if platform:
                filters.append(Post.platform == platform)
            if status:
                filters.append(Post.status.in_(status))
            if after_date:
                filters.append(Post.created_at >= after_date)
            if before_date:
                filters.append(Post.created_at <= before_date)

            # Build query for total count
            count_query = select(func.count()).select_from(Post).where(and_(*filters))
            count_result = await self._db.execute(count_query)
            total = count_result.scalar() or 0
            total_pages = math.ceil(total / size) if size > 0 else 0

            # Build query for paginated posts
            query = (
                select(Post)
                .where(and_(*filters))
                .order_by(
                    desc(getattr(Post, order_by))
                    if order_direction == "desc"
                    else getattr(Post, order_by)
                )
                .offset(offset)
                .limit(size)
            )

            result = await self._db.execute(query)
            posts = result.scalars().all()

            return {
                "items": [PostResponse.model_validate(p) for p in posts],
                "total": total,
                "page": page,
                "size": size,
                "total_pages": total_pages,
            }
        except Exception as e:
            logger.error(f"Error getting posts list for user {user_id}: {e}")
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
            result = await self._db.execute(query)
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

            self._db.add(post)
            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
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

            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
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
            await self._db.rollback()
            logger.error(f"Error batch updating posts: {e}")
            raise

    async def delete_post(self, user_id: UUID, post_id: UUID) -> bool:
        """Delete a post."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return False

            await self._db.delete(post)
            await self._db.commit()
            return True

        except Exception as e:
            await self._db.rollback()
            logger.error(f"Error deleting post {post_id}: {e}")
            raise

    async def dismiss_post(self, user_id: UUID, post_id: UUID) -> Optional[Post]:
        """Mark a post as dismissed."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            post.status = "dismissed"
            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
            logger.error(f"Error dismissing post {post_id}: {e}")
            raise

    async def mark_as_posted(self, user_id: UUID, post_id: UUID) -> Optional[Post]:
        """Mark a post as posted."""
        try:
            post = await self.get_post(user_id, post_id)
            if not post:
                return None

            post.status = "posted"
            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
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
            if comment:
                post.feedback_comment = comment
            post.feedback_at = datetime.utcnow()

            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
            logger.error(f"Error submitting feedback for post {post_id}: {e}")
            raise

    async def publish_post(
        self, user_id: UUID, post_id: UUID, platform: str
    ) -> Optional[dict]:
        """Publish a post to a social media platform."""
        post = await self.get_post(user_id, post_id)
        if not post:
            return None

        if platform == "linkedin":
            profile_service = ProfileService(self._db)
            connection = await profile_service.get_social_connection(
                user_id, "linkedin"
            )
            if not connection:
                raise Exception("LinkedIn connection not found for user.")

            linkedin_service = LinkedInService(connection)

            share_result = await linkedin_service.share_post(
                text=post.content,
                media_type=post.media_type,
                media_url=post.media_url,
                linkedin_asset_urn=post.linkedin_asset_urn,
            )

            # Mark post as "posted"
            await self.update_post(
                user_id,
                post_id,
                PostUpdate(status="posted", posted_at=datetime.utcnow()),
            )
            return share_result

        # Placeholder for other platforms
        raise NotImplementedError(f"Publishing to {platform} is not supported.")

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

            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
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

            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
            logger.error(f"Error unscheduling post {post_id}: {e}")
            raise

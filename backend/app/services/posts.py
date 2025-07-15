"""
Posts service for business logic.
"""

import math
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import UploadFile

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from google.cloud import storage
import asyncio

from app.core.config import settings
from app.models.posts import Post, PostMedia
from app.schemas.posts import PostCreate, PostUpdate, PostBatchUpdate
from app.services.profile import ProfileService
from app.services.linkedin_service import LinkedInService


class PostsService:
    """Service for posts operations."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(settings.post_media_bucket_name)

    async def upload_media_for_post(
        self, user_id: UUID, post_id: UUID, files: List[UploadFile]
    ) -> List[PostMedia]:
        """Uploads media for a post to GCS and creates PostMedia records."""
        post = await self.get_post(user_id, post_id)
        if not post:
            raise Exception("Post not found")

        created_media = []
        for file in files:
            storage_path = f"{user_id}/{post_id}/{file.filename}"
            blob = self.bucket.blob(storage_path)

            try:
                # TODO: Use async upload method when available in google-cloud-storage
                blob.upload_from_string(
                    await file.read(), content_type=file.content_type
                )
            except Exception as e:
                logger.error(f"Error uploading to GCS: {e}")
                raise

            media_type = "image" if "image" in file.content_type else "video"

            post_media = PostMedia(
                post_id=post_id,
                user_id=user_id,
                media_type=media_type,
                file_name=file.filename,
                storage_path=storage_path,
                gcs_url=blob.public_url,
            )
            self._db.add(post_media)
            await self._db.commit()
            await self._db.refresh(post_media)
            created_media.append(post_media)

        return created_media

    async def delete_media_for_post(self, user_id: UUID, post_id: UUID, media_id: UUID):
        """Deletes a media file from GCS and the database."""
        post = await self.get_post(user_id, post_id)
        if not post:
            raise Exception("Post not found or access denied")

        media_query = select(PostMedia).where(
            PostMedia.id == media_id, PostMedia.post_id == post_id
        )
        result = await self._db.execute(media_query)
        media = result.scalar_one_or_none()

        if not media:
            raise Exception("Media not found")

        # Delete from GCS
        if media.storage_path:
            try:
                blob = self.bucket.blob(media.storage_path)
                if blob.exists():
                    # TODO: Use async delete method
                    blob.delete()
            except Exception as e:
                logger.error(f"Error deleting {media.storage_path} from GCS: {e}")

        await self._db.delete(media)
        await self._db.commit()

    async def _get_post_by_ids(self, post_ids: List[UUID]) -> List[Post]:
        """Get a post by id."""
        query = (
            select(Post).where(Post.id.in_(post_ids)).options(selectinload(Post.media))
        )
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
        order_by: str = "scheduled_at",
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
                filters.append(Post.scheduled_at >= after_date)
            if before_date:
                filters.append(Post.scheduled_at <= before_date)

            count_query = select(func.count()).select_from(Post).where(and_(*filters))
            count_result = await self._db.execute(count_query)
            total = count_result.scalar() or 0
            total_pages = math.ceil(total / size) if size > 0 else 0

            query = (
                select(Post)
                .where(and_(*filters))
                .options(selectinload(Post.media))
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
                "items": posts,
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
            query = (
                select(Post)
                .where(
                    and_(
                        Post.id == post_id,
                        Post.user_id == user_id,
                    )
                )
                .options(selectinload(Post.media))
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

            media_payloads = []
            if post.media:
                for media_item in post.media:
                    if (
                        media_item.media_type in ["image", "video"]
                        and media_item.storage_path
                    ):
                        blob = self.bucket.blob(media_item.storage_path)
                        # TODO: Use async download
                        media_content = blob.download_as_bytes()

                        asset_urn = await linkedin_service.upload_media(
                            media_content, media_item.media_type
                        )
                        media_item.linkedin_asset_urn = asset_urn
                        self._db.add(media_item)
                        media_payloads.append({"media": asset_urn})

                await self._db.commit()

            share_result = await linkedin_service.share_post(
                text=post.content,
                media_items=media_payloads,
            )

            await self.update_post(
                user_id,
                post_id,
                PostUpdate(status="posted", posted_at=datetime.utcnow()),
            )

            # Delete media from GCS after posting
            if post.media:
                for media_item in post.media:
                    if media_item.storage_path:
                        try:
                            blob = self.bucket.blob(media_item.storage_path)
                            if blob.exists():
                                blob.delete()
                            media_item.storage_path = None
                            media_item.gcs_url = None
                            self._db.add(media_item)
                        except Exception as e:
                            logger.error(
                                f"Error deleting media {media_item.storage_path} from GCS: {e}"
                            )
                await self._db.commit()

            return share_result

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

            post.status = "draft"
            post.scheduled_at = None

            await self._db.commit()
            await self._db.refresh(post)
            return post

        except Exception as e:
            await self._db.rollback()
            logger.error(f"Error unscheduling post {post_id}: {e}")
            raise

    async def get_signed_media_for_post(
        self, user_id: UUID, post_id: UUID
    ) -> List[PostMedia]:
        """Retrieve media for a post with signed GCS URLs."""
        post = await self.get_post(user_id, post_id)
        if not post:
            raise Exception("Post not found")

        media_items: List[PostMedia] = []
        for media in post.media:
            if media.storage_path:
                try:
                    blob = self.bucket.blob(media.storage_path)
                    # Generate a signed URL valid for 1 hour
                    signed_url = blob.generate_signed_url(
                        version="v4", expiration=timedelta(hours=1), method="GET"
                    )
                    # Do not persist to DB; modify in-memory only
                    media.gcs_url = signed_url  # type: ignore
                except Exception as e:
                    logger.error(
                        f"Error generating signed URL for {media.storage_path}: {e}"
                    )
            media_items.append(media)

        return media_items

    async def get_post_counts(self, user_id: UUID) -> Dict[str, int]:
        """Return counts of drafts, scheduled, and posted posts for a user.

        Drafts are considered any posts in status: suggested, saved, or draft.
        """
        try:
            # Drafts (multiple statuses)
            draft_statuses = ["suggested", "draft"]

            draft_count_query = (
                select(func.count())
                .select_from(Post)
                .where(Post.user_id == user_id, Post.status.in_(draft_statuses))
            )
            scheduled_count_query = (
                select(func.count())
                .select_from(Post)
                .where(Post.user_id == user_id, Post.status == "scheduled")
            )
            posted_count_query = (
                select(func.count())
                .select_from(Post)
                .where(Post.user_id == user_id, Post.status == "posted")
            )

            draft_result, scheduled_result, posted_result = await asyncio.gather(
                self._db.execute(draft_count_query),
                self._db.execute(scheduled_count_query),
                self._db.execute(posted_count_query),
            )

            drafts = draft_result.scalar() or 0
            scheduled = scheduled_result.scalar() or 0
            posted = posted_result.scalar() or 0

            return {"drafts": drafts, "scheduled": scheduled, "posted": posted}
        except Exception as e:
            logger.error(f"Error fetching post counts for user {user_id}: {e}")
            raise

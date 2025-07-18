"""
Posts service for business logic.
"""

import math
from datetime import datetime, timedelta, timezone
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

        # Initialize GCS client only outside of test environment. This prevents
        # Google Application Default Credentials look-ups during unit tests.
        self.storage_client = None
        self.bucket = None
        if settings.environment != "test":
            try:
                self.storage_client = storage.Client()
                if settings.post_media_bucket_name:
                    self.bucket = self.storage_client.bucket(
                        settings.post_media_bucket_name
                    )
            except Exception as e:
                # Log but do not raise in non-test environments to keep app running.
                logger.warning(
                    f"Failed to initialize GCS client (env={settings.environment}): {e}"
                )

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
                article_url=post_data.article_url,
            )

            self._db.add(post)
            await self._db.commit()

            # Eagerly load media relationship to prevent lazy-loading outside of async context
            result = await self._db.execute(
                select(Post).options(selectinload(Post.media)).where(Post.id == post.id)
            )
            post = result.scalar_one()
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
            for post_item in items:
                # Convert batch item to PostUpdate while excluding the id to avoid primary key updates
                update_data = PostUpdate.model_validate(
                    post_item.model_dump(exclude={"id"}, exclude_unset=True)
                )
                await self.update_post(user_id, post_item.id, update_data)

            updated_posts = await self._get_post_by_ids(
                [post_item.id for post_item in items]
            )

            return {
                "items": updated_posts,
                "total": len(updated_posts),
                "page": 1,
                "size": len(updated_posts),
                "total_pages": 1,
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

            # Delete any associated media files (GCS & DB)
            if post.media:
                for media_item in list(post.media):
                    # Remove from GCS if we have a storage path & bucket is configured
                    if media_item.storage_path and self.bucket:
                        try:
                            blob = self.bucket.blob(media_item.storage_path)
                            if blob.exists():
                                # TODO: use async delete when available
                                blob.delete()
                        except Exception as e:
                            logger.error(
                                f"Error deleting media {media_item.storage_path} from GCS during dismiss: {e}"
                            )

                    # Delete the media record from the DB
                    await self._db.delete(media_item)

                # Flush deletes so relationships are updated
                await self._db.flush()

            # Finally mark post as dismissed
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
            try:
                profile_service = ProfileService(self._db)
                connection = await profile_service.get_social_connection(
                    user_id, "linkedin"
                )
                if not connection:
                    error_msg = "LinkedIn connection not found for user."
                    await self.update_post(
                        user_id,
                        post_id,
                        PostUpdate(sharing_error=error_msg),
                    )
                    raise Exception(error_msg)

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

                logger.info(
                    f"Publishing post {post_id}: content_length={len(post.content)}, article_url={post.article_url}, media_count={len(media_payloads)}"
                )

                share_result = await linkedin_service.share_post(
                    text=post.content,
                    article_url=post.article_url,
                    media_items=media_payloads,
                )

                print("LINKEDIN SHARE RESULT", share_result)

                # Capture LinkedIn shortened URL if possible
                try:
                    share_id = (
                        share_result.get("id")
                        if isinstance(share_result, dict)
                        else None
                    )
                    if share_id:
                        linkedin_short_url = (
                            f"https://www.linkedin.com/feed/update/{share_id}"
                        )
                        await self.update_post(
                            user_id,
                            post_id,
                            PostUpdate(linkedin_article_url=linkedin_short_url),
                        )
                except Exception as e:
                    logger.warning(
                        f"Unable to parse LinkedIn share response for shortened URL: {e}"
                    )

                # Clear any previous sharing errors and mark as posted
                await self.update_post(
                    user_id,
                    post_id,
                    PostUpdate(
                        status="posted",
                        posted_at=datetime.now(timezone.utc),
                        sharing_error=None,  # Clear any previous errors
                    ),
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

            except Exception as e:
                # Store the error message and keep the current status
                error_msg = str(e)
                logger.error(
                    f"Error publishing post {post_id} to {platform}: {error_msg}"
                )

                # Update the post with the error but don't change status
                await self.update_post(
                    user_id,
                    post_id,
                    PostUpdate(sharing_error=error_msg),
                )

                # Re-raise the exception so the router can handle it appropriately
                raise

        raise NotImplementedError(f"Publishing to {platform} is not supported.")

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
                    # Only append media with valid signed URL
                    media_items.append(media)
                except Exception as e:
                    logger.error(
                        f"Error generating signed URL for {media.storage_path}: {e}"
                    )
                    # Skip this media item if URL generation fails
            elif media.gcs_url:
                # If media already has a valid GCS URL, include it
                media_items.append(media)
            # Skip media items without storage_path or gcs_url

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

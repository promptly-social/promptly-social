"""
Posts service for business logic.
"""

import math
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import UploadFile

from loguru import logger
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from google.cloud import storage
from google.oauth2 import service_account
from google.auth import default
from google.auth import impersonated_credentials
from google.cloud import iam_credentials_v1
import asyncio

from app.core.config import settings
from app.models.posts import Post, PostMedia
from app.schemas.posts import PostCreate, PostUpdate, PostBatchUpdate
from app.services.profile import ProfileService
from app.services.linkedin_service import LinkedInService


class PostsService:
    """Service for posts operations."""

    # Class-level cache for shared credentials and clients
    _shared_storage_client = None
    _shared_signing_credentials = None
    _shared_iam_client = None
    _shared_service_account_email = None
    _shared_bucket = None
    _credentials_initialized = False

    def __init__(self, db: AsyncSession):
        self._db = db
        self._signed_url_cache = {}  # Instance-level cache for signed URLs

        # Use shared credentials (initialized once per application lifecycle)
        self.storage_client = PostsService._shared_storage_client
        self.signing_credentials = PostsService._shared_signing_credentials
        self.iam_client = PostsService._shared_iam_client
        self.service_account_email = PostsService._shared_service_account_email
        self.bucket = PostsService._shared_bucket

        # Initialize credentials if not already done
        if settings.environment != "test" and not PostsService._credentials_initialized:
            # Use synchronous initialization since __init__ can't be async
            # This will only run once per application lifecycle
            self._ensure_credentials_initialized()

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

    @classmethod
    def _ensure_credentials_initialized(cls):
        """Ensure credentials are initialized exactly once per application lifecycle."""
        if cls._credentials_initialized:
            return

        try:
            logger.info("Initializing GCS credentials (one-time setup)")

            # Initialize credentials for signing
            cls._initialize_shared_credentials()

            # Initialize storage client
            cls._shared_storage_client = storage.Client(
                credentials=cls._shared_signing_credentials
            )

            # For impersonated credentials, create proper signing credentials
            if not cls._has_private_key_static(cls._shared_signing_credentials):
                try:
                    # Get service account email from settings or detect from environment
                    cls._shared_service_account_email = (
                        settings.gcp_app_service_account_email
                        or cls._get_service_account_email_static()
                    )

                    if cls._shared_service_account_email:
                        # Create impersonated credentials for signing
                        source_credentials = cls._shared_signing_credentials
                        target_scopes = [
                            "https://www.googleapis.com/auth/cloud-platform"
                        ]

                        cls._shared_signing_credentials = (
                            impersonated_credentials.Credentials(
                                source_credentials=source_credentials,
                                target_principal=cls._shared_service_account_email,
                                target_scopes=target_scopes,
                                delegates=[],
                            )
                        )

                        logger.info(
                            f"Created impersonated credentials for service account: {cls._shared_service_account_email}"
                        )

                        # Initialize IAM client as fallback
                        cls._shared_iam_client = (
                            iam_credentials_v1.IAMCredentialsClient()
                        )
                    else:
                        logger.warning(
                            "Could not detect service account email for impersonation"
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to initialize impersonated credentials: {e}"
                    )

            if settings.post_media_bucket_name:
                cls._shared_bucket = cls._shared_storage_client.bucket(
                    settings.post_media_bucket_name
                )

            # Mark as initialized
            cls._credentials_initialized = True
            logger.info("GCS credentials initialization completed")

        except Exception as e:
            # Log but do not raise in non-test environments to keep app running.
            logger.warning(
                f"Failed to initialize GCS client (env={settings.environment}): {e}"
            )

    @classmethod
    def _initialize_shared_credentials(cls):
        """Initialize service account credentials for GCS signing (class-level)."""
        try:
            # Try to use service account key file if provided
            if settings.gcp_service_account_key_path and os.path.exists(
                settings.gcp_service_account_key_path
            ):
                logger.info(
                    f"Using service account key file: {settings.gcp_service_account_key_path}"
                )
                cls._shared_signing_credentials = (
                    service_account.Credentials.from_service_account_file(
                        settings.gcp_service_account_key_path
                    )
                )
            else:
                # Try to get default credentials and check their type
                credentials, project = default()
                credential_type = type(credentials).__name__

                logger.info(f"Detected credential type: {credential_type}")

                # Check if we're running on GCP with service account credentials
                if hasattr(credentials, "service_account_email") and hasattr(
                    credentials, "_private_key"
                ):
                    logger.info(
                        "Using GCP service account credentials with private key"
                    )
                    cls._shared_signing_credentials = credentials
                elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                    # Try to load from the credentials file
                    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                    logger.info(
                        f"Using credentials from GOOGLE_APPLICATION_CREDENTIALS: {cred_path}"
                    )
                    cls._shared_signing_credentials = (
                        service_account.Credentials.from_service_account_file(cred_path)
                    )
                else:
                    # Check if these are user OAuth2 credentials (from gcloud auth application-default login)
                    if (
                        "UserAccessTokenCredentials" in credential_type
                        or "oauth2" in credential_type.lower()
                    ):
                        logger.warning(
                            "Detected user OAuth2 credentials (from 'gcloud auth application-default login'). "
                            "These cannot be used for signing URLs. Consider using a service account key file "
                            "or setting GOOGLE_APPLICATION_CREDENTIALS to a service account key."
                        )
                    else:
                        logger.warning(
                            f"Using default credentials of type {credential_type}. "
                            "Signed URLs may not work if these credentials lack private keys."
                        )

                    cls._shared_signing_credentials = credentials

        except Exception as e:
            logger.error(f"Failed to initialize signing credentials: {e}")
            # Use default credentials as fallback
            try:
                credentials, project = default()
                cls._shared_signing_credentials = credentials
            except Exception as fallback_e:
                logger.error(f"Failed to get default credentials: {fallback_e}")
                cls._shared_signing_credentials = None

    @staticmethod
    def _has_private_key_static(credentials) -> bool:
        """Static version of _has_private_key for class-level initialization."""
        if not credentials:
            return False

        # Check for service account credentials with private key
        if hasattr(credentials, "_private_key") and credentials._private_key:
            return True

        # Check for other credential types that might have private keys
        if hasattr(credentials, "private_key") and credentials.private_key:
            return True

        return False

    @staticmethod
    def _get_service_account_email_static() -> Optional[str]:
        """Static version of _get_service_account_email for class-level initialization."""
        try:
            # Try to get from default credentials
            credentials, project = default()
            if hasattr(credentials, "service_account_email"):
                return credentials.service_account_email

            # Try to get from metadata server (GCP environments only)
            # This will fail for local development, which is expected
            import requests

            metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
            headers = {"Metadata-Flavor": "Google"}
            response = requests.get(metadata_url, headers=headers, timeout=5)
            if response.status_code == 200:
                email = response.text.strip()
                logger.debug(f"Detected service account email from metadata: {email}")
                return email
        except Exception as e:
            logger.debug(f"Could not detect service account email: {e}")

        return None

    def _has_private_key(self, credentials) -> bool:
        """Check if credentials have a private key for signing (instance method for compatibility)."""
        return PostsService._has_private_key_static(credentials)

    def _is_impersonated_credentials(self, credentials) -> bool:
        """Check if credentials are impersonated credentials."""
        if not credentials:
            return False

        # Check if these are impersonated credentials
        return isinstance(credentials, impersonated_credentials.Credentials)

    def _get_cache_key(self, storage_path: str, expiration_hours: int = 1) -> str:
        """Generate cache key for signed URL."""
        return f"signed_url:{storage_path}:{expiration_hours}"

    def _is_url_expired(self, cached_data: Dict) -> bool:
        """Check if cached signed URL is expired or will expire soon (within 5 minutes)."""
        if "expires_at" not in cached_data:
            return True

        expires_at = datetime.fromisoformat(cached_data["expires_at"])
        # Consider expired if it expires within 5 minutes
        buffer_time = timedelta(minutes=5)
        return datetime.now(timezone.utc) + buffer_time >= expires_at

    def _generate_signed_url(
        self, storage_path: str, expiration_hours: int = 1
    ) -> Optional[str]:
        """Generate a signed URL for a GCS object with caching."""
        if not self.bucket or not storage_path:
            return None

        cache_key = self._get_cache_key(storage_path, expiration_hours)

        # Check cache first
        if cache_key in self._signed_url_cache:
            cached_data = self._signed_url_cache[cache_key]
            if not self._is_url_expired(cached_data):
                logger.debug(f"Using cached signed URL for {storage_path}")
                return cached_data["url"]
            else:
                # Remove expired entry
                del self._signed_url_cache[cache_key]

        try:
            blob = self.bucket.blob(storage_path)
            expiration = timedelta(hours=expiration_hours)

            # Try to generate signed URL with different methods
            signed_url = None

            # Method 1: Use credentials with private key (works locally with service account files and impersonated credentials)
            if self._has_private_key(
                self.signing_credentials
            ) or self._is_impersonated_credentials(self.signing_credentials):
                credential_type = (
                    "private key"
                    if self._has_private_key(self.signing_credentials)
                    else "impersonated"
                )
                logger.debug(f"Using {credential_type} credentials for {storage_path}")
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET",
                    credentials=self.signing_credentials,
                )
            # Method 2: Use IAM Service Account Credentials API (fallback for GCP environments)
            elif self.iam_client and self.service_account_email:
                logger.debug(f"Using IAM credentials API fallback for {storage_path}")
                signed_url = self._generate_signed_url_with_iam(
                    blob, expiration, storage_path
                )
            else:
                # Method 3: Final fallback - try with default credentials anyway
                # This will likely fail for user OAuth2 credentials, but we'll try
                credential_type = (
                    type(self.signing_credentials).__name__
                    if self.signing_credentials
                    else "None"
                )
                logger.debug(
                    f"Attempting final fallback signing for {storage_path} with {credential_type}"
                )

                # For user OAuth2 credentials, this will fail with a helpful error message
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=expiration,
                    method="GET",
                    credentials=self.signing_credentials,
                )

            if signed_url:
                # Cache the signed URL
                expires_at = datetime.now(timezone.utc) + expiration
                self._signed_url_cache[cache_key] = {
                    "url": signed_url,
                    "expires_at": expires_at.isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }

                logger.debug(f"Generated and cached signed URL for {storage_path}")
                return signed_url
            else:
                logger.error(f"Failed to generate signed URL for {storage_path}")
                return None

        except Exception as e:
            logger.error(f"Error generating signed URL for {storage_path}: {e}")
            return None

    def _generate_signed_url_with_iam(
        self, blob, expiration: timedelta, storage_path: str
    ) -> Optional[str]:
        """Generate signed URL using IAM Service Account Credentials API."""
        try:
            import base64
            import urllib.parse
            from datetime import datetime, timezone

            # Calculate expiration timestamp
            expires_timestamp = int(
                (datetime.now(timezone.utc) + expiration).timestamp()
            )

            # Build the string to sign
            http_verb = "GET"
            content_md5 = ""
            content_type = ""
            expires = str(expires_timestamp)
            canonicalized_extension_headers = ""
            canonicalized_resource = f"/{self.bucket.name}/{storage_path}"

            string_to_sign = "\n".join(
                [
                    http_verb,
                    content_md5,
                    content_type,
                    expires,
                    canonicalized_extension_headers + canonicalized_resource,
                ]
            )

            # Use IAM service to sign the string
            name = f"projects/-/serviceAccounts/{self.service_account_email}"
            payload = string_to_sign.encode("utf-8")

            request = iam_credentials_v1.SignBlobRequest(name=name, payload=payload)

            response = self.iam_client.sign_blob(request=request)
            signature = base64.b64encode(response.signed_blob).decode("utf-8")

            # Build the signed URL
            query_params = {
                "GoogleAccessId": self.service_account_email,
                "Expires": expires,
                "Signature": signature,
            }

            query_string = urllib.parse.urlencode(query_params)
            signed_url = f"https://storage.googleapis.com/{self.bucket.name}/{storage_path}?{query_string}"

            return signed_url

        except Exception as e:
            logger.error(
                f"Error generating signed URL with IAM for {storage_path}: {e}"
            )
            return None

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

            # Enhanced date filtering logic for calendar queries
            if after_date or before_date:
                date_filters = []

                # For scheduled posts, filter by scheduled_at
                if after_date and before_date:
                    scheduled_filter = and_(
                        Post.scheduled_at >= after_date,
                        Post.scheduled_at <= before_date,
                        Post.status == "scheduled",
                    )
                    posted_filter = and_(
                        Post.posted_at >= after_date,
                        Post.posted_at <= before_date,
                        Post.status == "posted",
                    )
                    date_filters.extend([scheduled_filter, posted_filter])
                elif after_date:
                    scheduled_filter = and_(
                        Post.scheduled_at >= after_date, Post.status == "scheduled"
                    )
                    posted_filter = and_(
                        Post.posted_at >= after_date, Post.status == "posted"
                    )
                    date_filters.extend([scheduled_filter, posted_filter])
                elif before_date:
                    scheduled_filter = and_(
                        Post.scheduled_at <= before_date, Post.status == "scheduled"
                    )
                    posted_filter = and_(
                        Post.posted_at <= before_date, Post.status == "posted"
                    )
                    date_filters.extend([scheduled_filter, posted_filter])

                # If we have multiple status types and date filters, we need to handle them properly
                if (
                    status
                    and len(status) > 1
                    and ("scheduled" in status and "posted" in status)
                ):
                    # For calendar queries with both scheduled and posted posts
                    from sqlalchemy import or_

                    filters.append(or_(*date_filters))
                elif status and "scheduled" in status and "posted" not in status:
                    # Only scheduled posts
                    if after_date:
                        filters.append(Post.scheduled_at >= after_date)
                    if before_date:
                        filters.append(Post.scheduled_at <= before_date)
                elif status and "posted" in status and "scheduled" not in status:
                    # Only posted posts
                    if after_date:
                        filters.append(Post.posted_at >= after_date)
                    if before_date:
                        filters.append(Post.posted_at <= before_date)
                else:
                    # Default behavior for backward compatibility
                    if after_date:
                        filters.append(Post.scheduled_at >= after_date)
                    if before_date:
                        filters.append(Post.scheduled_at <= before_date)

            count_query = select(func.count()).select_from(Post).where(and_(*filters))
            count_result = await self._db.execute(count_query)
            total = count_result.scalar() or 0
            total_pages = math.ceil(total / size) if size > 0 else 0

            # Handle multiple order_by fields for calendar queries
            order_fields = []
            if "," in order_by:
                # Multiple order fields (e.g., "scheduled_at,posted_at")
                for field in order_by.split(","):
                    field = field.strip()
                    if hasattr(Post, field):
                        if order_direction == "desc":
                            order_fields.append(desc(getattr(Post, field)))
                        else:
                            order_fields.append(getattr(Post, field))
            else:
                # Single order field
                if hasattr(Post, order_by):
                    if order_direction == "desc":
                        order_fields.append(desc(getattr(Post, order_by)))
                    else:
                        order_fields.append(getattr(Post, order_by))
                else:
                    # Fallback to created_at if order_by field doesn't exist
                    order_fields.append(desc(Post.created_at))

            query = (
                select(Post)
                .where(and_(*filters))
                .options(selectinload(Post.media))
                .order_by(*order_fields)
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
                # Generate signed URL with caching
                signed_url = self._generate_signed_url(
                    media.storage_path, expiration_hours=1
                )
                if signed_url:
                    # Do not persist to DB; modify in-memory only
                    media.gcs_url = signed_url  # type: ignore
                    media_items.append(media)
                else:
                    logger.warning(
                        f"Failed to generate signed URL for {media.storage_path}, skipping media item"
                    )
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

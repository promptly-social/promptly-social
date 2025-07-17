"""
Service for managing post scheduling and corresponding GCP Cloud Scheduler jobs.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from google.cloud import scheduler_v1
from google.api_core.exceptions import GoogleAPICallError
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.config import settings
from app.models.posts import Post

# Constants for GCP project/location
GCP_PROJECT = settings.gcp_project_id
GCP_LOCATION = settings.gcp_location
JOB_PREFIX = "share-post-"


def _get_job_name(post_id: UUID) -> str:
    """Generate deterministic Cloud Scheduler job name for a post."""
    return f"{JOB_PREFIX}{post_id}"


def _datetime_to_cron(dt: datetime, timezone: str = "UTC") -> str:
    """Convert datetime to cron expression."""
    # Format: minute hour day month day_of_week
    return f"{dt.minute} {dt.hour} {dt.day} {dt.month} *"


class PostScheduleService:
    """Business logic for post scheduling and Cloud Scheduler sync."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # Cloud Scheduler client is synchronous; we can instantiate lazily.
        self._scheduler_client: Optional[scheduler_v1.CloudSchedulerClient] = None

    # ----- Internal helpers -----
    def _client(self) -> Optional[scheduler_v1.CloudSchedulerClient]:
        if self._scheduler_client is None:
            try:
                self._scheduler_client = scheduler_v1.CloudSchedulerClient()
            except Exception as e:
                # Likely missing credentials in local/dev environment
                logger.warning(
                    f"Could not initialize CloudSchedulerClient: {e}. Skipping job sync."
                )
                return None
        return self._scheduler_client

    def _parent_path(self) -> str:
        project = GCP_PROJECT or settings.environment  # fallback; adjust as necessary
        if not GCP_PROJECT:
            logger.warning(
                "GCP_PROJECT_ID env not set; Cloud Scheduler operations will fail."
            )
        return f"projects/{project}/locations/{GCP_LOCATION}"

    def _create_scheduler_job(
        self,
        post_id: UUID,
        user_id: UUID,
        scheduled_at: datetime,
        timezone: str = "UTC",
    ) -> str:
        """Create Cloud Scheduler job for the post."""
        client = self._client()
        if client is None:
            return ""  # Skip sync when client unavailable

        job_name = _get_job_name(post_id)
        cron_expression = _datetime_to_cron(scheduled_at, timezone)

        payload = json.dumps({"user_id": str(user_id), "post_id": str(post_id)}).encode(
            "utf-8"
        )

        full_job_name = f"{self._parent_path()}/jobs/{job_name}"

        # Create the job configuration
        job = {
            "name": full_job_name,
            "schedule": cron_expression,
            "time_zone": timezone,
            "http_target": {
                "http_method": "POST",
                "uri": settings.gcp_share_post_function_url,
                "headers": {"Content-Type": "application/json"},
                "body": payload,
            },
            "attempt_deadline": "300s",  # 5 minutes timeout
        }

        # Add OIDC token if service account email is set
        if settings.gcp_app_service_account_email:
            job["http_target"]["oidc_token"] = {
                "service_account_email": settings.gcp_app_service_account_email
            }

        try:
            client.create_job(
                parent=self._parent_path(),
                job=job,
            )
            logger.info(f"Created Cloud Scheduler job {full_job_name}")
            return job_name
        except GoogleAPICallError as e:
            logger.error(
                f"Failed to create Cloud Scheduler job {full_job_name}: {e.message if hasattr(e, 'message') else e}"
            )
            return ""

    def _update_scheduler_job(
        self, job_name: str, scheduled_at: datetime, timezone: str = "UTC"
    ) -> bool:
        """Update existing Cloud Scheduler job."""
        client = self._client()
        if client is None:
            return False

        cron_expression = _datetime_to_cron(scheduled_at, timezone)
        full_job_name = f"{self._parent_path()}/jobs/{job_name}"

        update_mask = {
            "paths": [
                "schedule",
                "time_zone",
            ]
        }

        try:
            client.update_job(
                job={
                    "name": full_job_name,
                    "schedule": cron_expression,
                    "time_zone": timezone,
                },
                update_mask=update_mask,
            )
            logger.info(f"Updated Cloud Scheduler job {full_job_name}")
            return True
        except GoogleAPICallError as e:
            logger.error(
                f"Failed to update Cloud Scheduler job {full_job_name}: {e.message if hasattr(e, 'message') else e}"
            )
            return False

    def _delete_scheduler_job(self, job_name: str) -> bool:
        """Delete Cloud Scheduler job."""
        client = self._client()
        if client is None:
            return False

        full_job_name = f"{self._parent_path()}/jobs/{job_name}"
        try:
            client.delete_job(name=full_job_name)
            logger.info(f"Deleted Cloud Scheduler job {full_job_name}")
            return True
        except Exception as e:
            logger.warning(f"Could not delete Cloud Scheduler job {full_job_name}: {e}")
            return False

    # ----- Public methods -----
    async def schedule_post(
        self,
        user_id: UUID,
        post_id: UUID,
        scheduled_at: datetime,
        timezone: str = "UTC",
    ) -> Optional[str]:
        """Schedule a post for sharing."""
        # Get the post
        query = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            logger.error(f"Post {post_id} not found for user {user_id}")
            return None

        # Create scheduler job
        job_name = ""
        try:
            job_name = await asyncio.get_event_loop().run_in_executor(
                None,
                self._create_scheduler_job,
                post_id,
                user_id,
                scheduled_at,
                timezone,
            )
        except Exception as e:
            logger.error(f"Failed to create scheduler job: {e}")
            return None

        if not job_name:
            return None

        # Update post with scheduling information
        post.scheduled_at = scheduled_at
        post.scheduler_job_name = job_name
        post.status = "scheduled"

        await self.db.commit()
        await self.db.refresh(post)

        logger.info(f"Scheduled post {post_id} for {scheduled_at}")
        return job_name

    async def unschedule_post(self, user_id: UUID, post_id: UUID) -> bool:
        """Unschedule a post."""
        # Get the post
        query = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            logger.error(f"Post {post_id} not found for user {user_id}")
            return False

        if not post.scheduler_job_name:
            logger.warning(f"Post {post_id} has no scheduler job to delete")
            return True  # Already unscheduled

        # Delete scheduler job
        success = False
        try:
            success = await asyncio.get_event_loop().run_in_executor(
                None, self._delete_scheduler_job, post.scheduler_job_name
            )
        except Exception as e:
            logger.error(f"Failed to delete scheduler job: {e}")

        # Update post regardless of scheduler job deletion success
        post.scheduled_at = None
        post.scheduler_job_name = None
        post.status = "draft"  # Reset to draft status

        await self.db.commit()
        await self.db.refresh(post)

        logger.info(f"Unscheduled post {post_id}")
        return success

    async def reschedule_post(
        self,
        user_id: UUID,
        post_id: UUID,
        new_scheduled_at: datetime,
        timezone: str = "UTC",
    ) -> Optional[str]:
        """Reschedule a post to a new time."""
        # Get the post
        query = select(Post).where(Post.id == post_id, Post.user_id == user_id)
        result = await self.db.execute(query)
        post = result.scalar_one_or_none()

        if not post:
            logger.error(f"Post {post_id} not found for user {user_id}")
            return None

        # If post has existing scheduler job, update it
        if post.scheduler_job_name:
            success = False
            try:
                success = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._update_scheduler_job,
                    post.scheduler_job_name,
                    new_scheduled_at,
                    timezone,
                )
            except Exception as e:
                logger.error(f"Failed to update scheduler job: {e}")
                return None

            if success:
                # Update post with new scheduling information
                post.scheduled_at = new_scheduled_at
                await self.db.commit()
                await self.db.refresh(post)

                logger.info(f"Rescheduled post {post_id} to {new_scheduled_at}")
                return post.scheduler_job_name
            else:
                return None
        else:
            # No existing job, create a new one
            return await self.schedule_post(
                user_id, post_id, new_scheduled_at, timezone
            )

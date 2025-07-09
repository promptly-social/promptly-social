"""
Service for managing daily suggestion schedules and corresponding GCP Cloud Scheduler jobs.
"""

from __future__ import annotations

import json
from typing import Optional
from uuid import UUID

from google.cloud import scheduler_v1
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from anyio import to_thread

from app.core.config import settings
from app.models.daily_suggestion_schedule import DailySuggestionSchedule
from app.schemas.daily_suggestion_schedule import (
    DailySuggestionScheduleCreate,
    DailySuggestionScheduleUpdate,
)

# Constants for GCP project/location
GCP_PROJECT = settings.gcp_project_id
GCP_LOCATION = settings.gcp_location
JOB_PREFIX = "daily-suggestion-"


def _get_job_name(user_id: UUID) -> str:
    """Generate deterministic Cloud Scheduler job name for a user."""
    return f"{JOB_PREFIX}{user_id}"


class DailySuggestionScheduleService:
    """Business logic for CRUD operations and Cloud Scheduler sync."""

    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
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

    # Note: CloudSchedulerClient is synchronous; ensure not blocking heavy loops.

    def _parent_path(self) -> str:
        project = GCP_PROJECT or settings.environment  # fallback; adjust as necessary
        if not GCP_PROJECT:
            logger.warning(
                "GCP_PROJECT_ID env not set; Cloud Scheduler operations will fail."
            )
        return f"projects/{project}/locations/{GCP_LOCATION}"

    def _upsert_job(self, schedule: DailySuggestionSchedule):
        """Create or update Cloud Scheduler job for the schedule."""
        client = self._client()
        if client is None:
            return  # Skip sync when client unavailable

        payload = json.dumps({"user_id": str(self.user_id)}).encode(
            "utf-8"
        )  # bytes for body

        name = f"{self._parent_path()}/jobs/{_get_job_name(schedule.user_id)}"
        http_target_kwargs = {
            "http_method": scheduler_v1.HttpMethod.POST,
            "uri": settings.gcp_generate_suggestions_function_url,
            "headers": {"Content-Type": "application/json"},
            "body": payload,
        }

        if settings.gcp_app_service_account_email:
            http_target_kwargs["oidc_token"] = scheduler_v1.OidcToken(
                service_account_email=settings.gcp_app_service_account_email
            )

        job = scheduler_v1.Job(
            name=name,
            schedule=schedule.cron_expression,
            time_zone=schedule.timezone,
            http_target=scheduler_v1.HttpTarget(**http_target_kwargs),
        )

        try:
            client.get_job(name=name)
            client.update_job(job=job)
            logger.info(f"Updated Cloud Scheduler job {name}")
        except Exception:
            client.create_job(parent=self._parent_path(), job=job)
            logger.info(f"Created Cloud Scheduler job {name}")

    def _delete_job(self, user_id: UUID):
        client = self._client()
        if client is None:
            return

        name = f"{self._parent_path()}/jobs/{_get_job_name(user_id)}"
        try:
            client.delete_job(name=name)
            logger.info(f"Deleted Cloud Scheduler job {name}")
        except Exception as e:
            logger.warning(f"Could not delete Cloud Scheduler job {name}: {e}")

    # ----- Public CRUD -----
    async def get_schedule(self, user_id: UUID) -> Optional[DailySuggestionSchedule]:
        query = select(DailySuggestionSchedule).where(
            DailySuggestionSchedule.user_id == user_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_schedule(
        self, user_id: UUID, data: DailySuggestionScheduleCreate
    ) -> DailySuggestionSchedule:
        existing = await self.get_schedule(user_id)
        if existing:
            raise ValueError("Schedule already exists; use update instead.")
        schedule = DailySuggestionSchedule(
            user_id=user_id,
            cron_expression=data.cron_expression,
            timezone=data.timezone,
        )
        self.db.add(schedule)
        await self.db.commit()
        await self.db.refresh(schedule)

        # Sync with Cloud Scheduler (blocking call; consider background tasks)
        try:
            asyncio.create_task(to_thread.run_sync(self._upsert_job, schedule))
        except Exception as e:
            logger.error(f"Failed to schedule Cloud Scheduler sync task: {e}")
        return schedule

    async def update_schedule(
        self, user_id: UUID, data: DailySuggestionScheduleUpdate
    ) -> Optional[DailySuggestionSchedule]:
        schedule = await self.get_schedule(user_id)
        if not schedule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        await self.db.commit()
        await self.db.refresh(schedule)

        # Sync job
        try:
            asyncio.create_task(to_thread.run_sync(self._upsert_job, schedule))
        except Exception as e:
            logger.error(f"Failed to schedule Cloud Scheduler sync task: {e}")
        return schedule

    async def delete_schedule(self, user_id: UUID) -> bool:
        schedule = await self.get_schedule(user_id)
        if not schedule:
            return False
        await self.db.delete(schedule)
        await self.db.commit()
        # try deleting job
        try:
            asyncio.create_task(to_thread.run_sync(self._delete_job, user_id))
        except Exception as e:
            logger.error(f"Failed to schedule Cloud Scheduler delete task: {e}")
        return True

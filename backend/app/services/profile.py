"""
Content service for handling content-related business logic.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

import httpx
from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import SocialConnection, UserPreferences, WritingStyleAnalysis
from app.schemas.profile import SocialConnectionUpdate, UserPreferencesUpdate


class ProfileService:
    """Service class for profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # User Preferences Operations
    async def get_user_preferences(self, user_id: UUID) -> Optional[UserPreferences]:
        """Get user preferences."""
        try:
            query = select(UserPreferences).where(UserPreferences.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user preferences for {user_id}: {e}")
            raise

    async def upsert_user_preferences(
        self, user_id: UUID, preferences_data: UserPreferencesUpdate
    ) -> UserPreferences:
        """Create or update user preferences."""
        try:
            # Check if preferences exist
            existing = await self.get_user_preferences(user_id)

            if existing:
                # Update existing preferences
                update_dict = preferences_data.model_dump()
                update_dict["updated_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated user preferences for {user_id}")
                return existing
            else:
                # Create new preferences
                preferences = UserPreferences(
                    user_id=user_id, **preferences_data.model_dump()
                )
                self.db.add(preferences)
                await self.db.commit()
                await self.db.refresh(preferences)
                logger.info(f"Created user preferences for {user_id}")
                return preferences

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error upserting user preferences for {user_id}: {e}")
            raise

    # Social Connections Operations
    async def get_social_connections(self, user_id: UUID) -> List[SocialConnection]:
        """Get all social connections for a user."""
        try:
            query = select(SocialConnection).where(SocialConnection.user_id == user_id)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting social connections for {user_id}: {e}")
            raise

    async def get_social_connection(
        self, user_id: UUID, platform: str
    ) -> Optional[SocialConnection]:
        """Get a specific social connection."""
        try:
            query = select(SocialConnection).where(
                and_(
                    SocialConnection.user_id == user_id,
                    SocialConnection.platform == platform,
                    SocialConnection.is_active,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting social connection {platform} for {user_id}: {e}"
            )
            raise

    async def get_social_connection_for_analysis(
        self, user_id: UUID, platform: str
    ) -> Optional[SocialConnection]:
        """Get a specific social connection for analysis (doesn't filter by is_active)."""
        try:
            query = select(SocialConnection).where(
                and_(
                    SocialConnection.user_id == user_id,
                    SocialConnection.platform == platform,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting social connection {platform} for analysis for {user_id}: {e}"
            )
            raise

    async def upsert_social_connection(
        self, user_id: UUID, platform: str, connection_data: SocialConnectionUpdate
    ) -> SocialConnection:
        """Create or update a social connection."""
        try:
            # Check if connection exists
            existing = await self.get_social_connection_for_analysis(user_id, platform)

            if existing:
                # Update existing connection
                update_dict = connection_data.model_dump(exclude_unset=True)
                update_dict["updated_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated social connection {platform} for {user_id}")
                return existing
            else:
                # Create new connection
                connection = SocialConnection(
                    user_id=user_id,
                    platform=platform,
                    **connection_data.model_dump(exclude_unset=True),
                )
                self.db.add(connection)
                await self.db.commit()
                await self.db.refresh(connection)
                logger.info(f"Created social connection {platform} for {user_id}")
                return connection

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error upserting social connection {platform} for {user_id}: {e}"
            )
            raise

    async def analyze_substack(self, user_id: UUID) -> Optional[SocialConnection]:
        """
        Analyze Substack content for a user.

        This method:
        1. Sets analysis_started_at timestamp
        2. Triggers async edge function for analysis
        3. Edge function will set analysis_completed_at when done

        Args:
            user_id: UUID of the user to analyze

        Returns:
            Updated SocialConnection with analysis_started_at set
        """
        try:
            # Get the Substack connection
            connection = await self.get_social_connection_for_analysis(
                user_id, "substack"
            )

            if not connection:
                logger.warning(f"No Substack connection found for user {user_id}")
                return None

            if not connection.platform_username:
                logger.warning(
                    f"No platform username set for Substack connection for user {user_id}"
                )
                return None

            # Set analysis_started_at timestamp
            connection.analysis_started_at = datetime.now(timezone.utc)
            connection.analysis_completed_at = None  # Reset completed timestamp

            await self.db.commit()
            await self.db.refresh(connection)

            logger.info(f"Started substack analysis for user {user_id}")

            # Trigger async edge function
            await self._trigger_substack_analysis(user_id, connection.platform_username)

            return connection

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error starting substack analysis for {user_id}: {e}")
            raise

    async def _trigger_substack_analysis(
        self, user_id: UUID, platform_username: str
    ) -> None:
        """
        Trigger the Supabase Edge Function for Substack analysis.
        Made configurable to switch to GCP Cloud Run later.
        """
        try:
            await self._trigger_gcp_cloud_run(user_id, platform_username)

        except Exception as e:
            logger.error(f"Error triggering edge function for user {user_id}: {e}")
            raise

    async def _trigger_gcp_cloud_run(
        self, user_id: UUID, platform_username: str
    ) -> None:
        """Trigger GCP Cloud Run function for analysis."""
        try:
            gcp_function_url = os.getenv("GCP_ANALYSIS_FUNCTION_URL")

            if not gcp_function_url:
                logger.error("Missing GCP Cloud Run function URL")
                return

            payload = {"user_id": str(user_id), "platform_username": platform_username}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    gcp_function_url,
                    json=payload,
                    timeout=10.0,  # Don't wait for completion, just trigger
                )

                if response.status_code not in [200, 202]:
                    logger.error(
                        f"Failed to trigger GCP function: {response.status_code} - {response.text}"
                    )
                else:
                    logger.info(
                        f"Successfully triggered GCP Cloud Run function for user {user_id}"
                    )

        except Exception as e:
            logger.error(f"Error triggering GCP Cloud Run function: {e}")
            raise

    # Writing Style Analysis Operations
    async def get_writing_style_analysis(
        self, user_id: UUID, platform: str
    ) -> Optional[WritingStyleAnalysis]:
        """Get writing style analysis for a platform."""
        try:
            query = select(WritingStyleAnalysis).where(
                and_(
                    WritingStyleAnalysis.user_id == user_id,
                    WritingStyleAnalysis.platform == platform,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting writing style analysis {platform} for {user_id}: {e}"
            )
            raise

    async def upsert_writing_style_analysis(
        self, user_id: UUID, platform: str, analysis_data: str
    ) -> WritingStyleAnalysis:
        """Create or update writing style analysis."""
        try:
            # Check if analysis exists
            existing = await self.get_writing_style_analysis(user_id, platform)

            if existing:
                # Update existing analysis
                update_dict = {"analysis_data": analysis_data}
                update_dict["updated_at"] = datetime.now(timezone.utc)
                if (
                    "last_analyzed_at" not in update_dict
                    or update_dict["last_analyzed_at"] is None
                ):
                    update_dict["last_analyzed_at"] = datetime.now(timezone.utc)

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated writing style analysis {platform} for {user_id}")
                return existing
            else:
                analysis = WritingStyleAnalysis(
                    user_id=user_id,
                    platform=platform,
                    analysis_data=analysis_data,
                )
                self.db.add(analysis)
                await self.db.commit()
                await self.db.refresh(analysis)
                logger.info(f"Created writing style analysis {platform} for {user_id}")
                return analysis

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error upserting writing style analysis {platform} for {user_id}: {e}"
            )
            raise

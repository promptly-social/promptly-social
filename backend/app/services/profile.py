"""
Content service for handling content-related business logic.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from loguru import logger

from app.models.profile import (
    UserPreferences,
    SocialConnection,
    WritingStyleAnalysis,
)
from app.schemas.profile import (
    UserPreferencesUpdate,
    SocialConnectionUpdate,
    WritingStyleAnalysisUpdate,
)


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
                update_dict["updated_at"] = datetime.utcnow()

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

    async def upsert_social_connection(
        self, user_id: UUID, platform: str, connection_data: SocialConnectionUpdate
    ) -> SocialConnection:
        """Create or update a social connection."""
        try:
            # Check if connection exists
            existing = await self.get_social_connection(user_id, platform)

            if existing:
                # Update existing connection
                update_dict = connection_data.model_dump(exclude_unset=True)
                update_dict["updated_at"] = datetime.utcnow()

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
        self, user_id: UUID, platform: str, analysis_data: WritingStyleAnalysisUpdate
    ) -> WritingStyleAnalysis:
        """Create or update writing style analysis."""
        try:
            # Check if analysis exists
            existing = await self.get_writing_style_analysis(user_id, platform)

            if existing:
                # Update existing analysis
                update_dict = analysis_data.model_dump(exclude_unset=True)
                update_dict["updated_at"] = datetime.utcnow()
                if (
                    "last_analyzed_at" not in update_dict
                    or update_dict["last_analyzed_at"] is None
                ):
                    update_dict["last_analyzed_at"] = datetime.utcnow()

                for key, value in update_dict.items():
                    setattr(existing, key, value)

                await self.db.commit()
                await self.db.refresh(existing)
                logger.info(f"Updated writing style analysis {platform} for {user_id}")
                return existing
            else:
                # Create new analysis
                create_dict = analysis_data.model_dump(exclude_unset=True)
                if "analysis_data" not in create_dict:
                    raise ValueError("analysis_data is required for new analysis")

                analysis = WritingStyleAnalysis(
                    user_id=user_id,
                    platform=platform,
                    analysis_data=create_dict["analysis_data"],
                    content_count=create_dict.get("content_count", 0),
                    last_analyzed_at=create_dict.get("last_analyzed_at")
                    or datetime.utcnow(),
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

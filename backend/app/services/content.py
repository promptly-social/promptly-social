"""
Content service for handling content-related business logic.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, desc, asc
from loguru import logger

from app.models.content import (
    ContentIdea,
    UserPreferences,
    SocialConnection,
    WritingStyleAnalysis,
)
from app.schemas.content import (
    ContentIdeaCreate,
    ContentIdeaUpdate,
    UserPreferencesUpdate,
    SocialConnectionUpdate,
    WritingStyleAnalysisUpdate,
)


class ContentService:
    """Service class for content operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Content Ideas Operations
    async def get_content_ideas(
        self,
        user_id: UUID,
        status: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc",
    ) -> Dict[str, Any]:
        """Get content ideas with filtering and pagination."""
        try:
            query = select(ContentIdea).where(ContentIdea.user_id == user_id)

            # Apply filters
            if status:
                query = query.where(ContentIdea.status.in_(status))
            if content_type:
                query = query.where(ContentIdea.content_type == content_type)

            # Apply ordering with special handling for specific statuses
            if status and "published" in status:
                # For published posts, prioritize published_date with nulls last
                query = query.order_by(
                    desc(ContentIdea.published_date).nulls_last(),
                    desc(ContentIdea.created_at),
                )
            elif status and "scheduled" in status:
                # For scheduled posts, order by scheduled date
                query = query.order_by(asc(ContentIdea.scheduled_date))
            else:
                # Default ordering
                order_column = getattr(ContentIdea, order_by, ContentIdea.created_at)
                if order_direction.lower() == "desc":
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))

            # Count total items
            count_query = select(ContentIdea).where(ContentIdea.user_id == user_id)
            if status:
                count_query = count_query.where(ContentIdea.status.in_(status))
            if content_type:
                count_query = count_query.where(
                    ContentIdea.content_type == content_type
                )

            total_result = await self.db.execute(count_query)
            total = len(total_result.scalars().all())

            # Apply pagination
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            result = await self.db.execute(query)
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "has_next": total > page * size,
            }

        except Exception as e:
            logger.error(f"Error getting content ideas: {e}")
            raise

    async def get_content_idea(
        self, user_id: UUID, content_id: UUID
    ) -> Optional[ContentIdea]:
        """Get a specific content idea."""
        try:
            query = select(ContentIdea).where(
                and_(ContentIdea.id == content_id, ContentIdea.user_id == user_id)
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting content idea {content_id}: {e}")
            raise

    async def create_content_idea(
        self, user_id: UUID, content_data: ContentIdeaCreate
    ) -> ContentIdea:
        """Create a new content idea."""
        try:
            content_idea = ContentIdea(
                user_id=str(user_id), **content_data.model_dump()
            )
            self.db.add(content_idea)
            await self.db.commit()
            await self.db.refresh(content_idea)
            logger.info(f"Created content idea {content_idea.id} for user {user_id}")
            return content_idea
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating content idea: {e}")
            raise

    async def update_content_idea(
        self, user_id: UUID, content_id: UUID, update_data: ContentIdeaUpdate
    ) -> Optional[ContentIdea]:
        """Update a content idea."""
        try:
            query = select(ContentIdea).where(
                and_(ContentIdea.id == content_id, ContentIdea.user_id == user_id)
            )
            result = await self.db.execute(query)
            content_idea = result.scalar_one_or_none()

            if not content_idea:
                return None

            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                update_dict["updated_at"] = datetime.utcnow()
                for key, value in update_dict.items():
                    setattr(content_idea, key, value)

                await self.db.commit()
                await self.db.refresh(content_idea)
                logger.info(f"Updated content idea {content_id} for user {user_id}")

            return content_idea
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating content idea {content_id}: {e}")
            raise

    async def delete_content_idea(self, user_id: UUID, content_id: UUID) -> bool:
        """Delete a content idea."""
        try:
            query = delete(ContentIdea).where(
                and_(ContentIdea.id == content_id, ContentIdea.user_id == user_id)
            )
            result = await self.db.execute(query)
            await self.db.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted content idea {content_id} for user {user_id}")
            return deleted
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting content idea {content_id}: {e}")
            raise

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

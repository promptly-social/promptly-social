"""
Content service for handling content-related business logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, asc, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content import Content, Publication
from app.schemas.content import (ContentCreate, ContentUpdate,
                                 PublicationCreate, PublicationUpdate)


class ContentService:
    """Service class for content operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # Content Operations
    async def get_content_list(
        self,
        user_id: UUID,
        status: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc",
    ) -> Dict[str, Any]:
        """Get content with filtering and pagination."""
        try:
            query = select(Content).where(Content.user_id == str(user_id))

            # Apply filters
            if status:
                query = query.where(Content.status.in_(status))
            if content_type:
                query = query.where(Content.content_type == content_type)

            # Apply ordering
            order_column = getattr(Content, order_by, Content.created_at)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

            # Count total items
            count_query = select(Content).where(Content.user_id == str(user_id))
            if status:
                count_query = count_query.where(Content.status.in_(status))
            if content_type:
                count_query = count_query.where(Content.content_type == content_type)

            total_result = await self.db.execute(count_query)
            total = len(total_result.scalars().all())

            # Apply pagination
            offset = (page - 1) * size
            query = query.offset(offset).limit(size)

            # Load with publications
            query = query.options(selectinload(Content.publications))

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
            logger.error(f"Error getting content list: {e}")
            raise

    async def get_content(self, user_id: UUID, content_id: UUID) -> Optional[Content]:
        """Get a specific content item."""
        try:
            query = (
                select(Content)
                .where(
                    and_(Content.id == str(content_id), Content.user_id == str(user_id))
                )
                .options(selectinload(Content.publications))
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting content {content_id}: {e}")
            raise

    async def create_content(
        self, user_id: UUID, content_data: ContentCreate
    ) -> Content:
        """Create a new content item."""
        try:
            # Convert UUID to string for consistent storage across databases
            content = Content(user_id=str(user_id), **content_data.model_dump())
            self.db.add(content)
            await self.db.commit()
            await self.db.refresh(content)
            logger.info(f"Created content {content.id} for user {user_id}")
            return content
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating content: {e}")
            raise

    async def update_content(
        self, user_id: UUID, content_id: UUID, update_data: ContentUpdate
    ) -> Optional[Content]:
        """Update a content item."""
        try:
            query = select(Content).where(
                and_(Content.id == str(content_id), Content.user_id == str(user_id))
            )
            result = await self.db.execute(query)
            content = result.scalar_one_or_none()

            if not content:
                return None

            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                update_dict["updated_at"] = datetime.now(timezone.utc)
                for key, value in update_dict.items():
                    setattr(content, key, value)

                await self.db.commit()
                await self.db.refresh(content)
                logger.info(f"Updated content {content_id} for user {user_id}")

            return content
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating content {content_id}: {e}")
            raise

    async def delete_content(self, user_id: UUID, content_id: UUID) -> bool:
        """Delete a content item."""
        try:
            query = delete(Content).where(
                and_(Content.id == str(content_id), Content.user_id == str(user_id))
            )
            result = await self.db.execute(query)
            await self.db.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted content {content_id} for user {user_id}")
            return deleted
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting content {content_id}: {e}")
            raise

    # Publication Operations
    async def create_publication(
        self, user_id: UUID, publication_data: PublicationCreate
    ) -> Publication:
        """Create a new publication."""
        try:
            # Verify content belongs to user
            content = await self.get_content(user_id, publication_data.content_id)
            if not content:
                raise ValueError("Content not found or not owned by user")

            # Convert UUIDs to strings for SQLite compatibility
            publication_dict = publication_data.model_dump()
            publication_dict["content_id"] = str(publication_dict["content_id"])
            publication = Publication(**publication_dict)
            self.db.add(publication)
            await self.db.commit()
            await self.db.refresh(publication)
            logger.info(
                f"Created publication {publication.id} for content {publication_data.content_id}"
            )
            return publication
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating publication: {e}")
            raise

    async def update_publication(
        self, user_id: UUID, publication_id: UUID, update_data: PublicationUpdate
    ) -> Optional[Publication]:
        """Update a publication."""
        try:
            # Find publication through content ownership
            query = (
                select(Publication)
                .join(Content)
                .where(
                    and_(
                        Publication.id == str(publication_id),
                        Content.user_id == str(user_id),
                    )
                )
            )
            result = await self.db.execute(query)
            publication = result.scalar_one_or_none()

            if not publication:
                return None

            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                update_dict["updated_at"] = datetime.now(timezone.utc)
                for key, value in update_dict.items():
                    setattr(publication, key, value)

                await self.db.commit()
                await self.db.refresh(publication)
                logger.info(f"Updated publication {publication_id}")

            return publication
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating publication {publication_id}: {e}")
            raise

    async def delete_publication(self, user_id: UUID, publication_id: UUID) -> bool:
        """Delete a publication."""
        try:
            # Find publication through content ownership
            query = (
                select(Publication)
                .join(Content)
                .where(
                    and_(
                        Publication.id == str(publication_id),
                        Content.user_id == str(user_id),
                    )
                )
            )
            result = await self.db.execute(query)
            publication = result.scalar_one_or_none()

            if not publication:
                return False

            await self.db.delete(publication)
            await self.db.commit()
            logger.info(f"Deleted publication {publication_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting publication {publication_id}: {e}")
            raise

    async def get_publications_by_content(
        self, user_id: UUID, content_id: UUID
    ) -> List[Publication]:
        """Get all publications for a content item."""
        try:
            query = (
                select(Publication)
                .join(Content)
                .where(
                    and_(
                        Publication.content_id == str(content_id),
                        Content.user_id == str(user_id),
                    )
                )
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting publications for content {content_id}: {e}")
            raise

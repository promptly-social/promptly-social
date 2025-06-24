"""
Idea Bank service for handling idea bank related business logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, asc, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idea_bank import IdeaBank
from app.schemas.idea_bank import IdeaBankCreate, IdeaBankUpdate


class IdeaBankService:
    """Service class for idea bank operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_idea_bank_list(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        order_by: str = "updated_at",
        order_direction: str = "desc",
    ) -> Dict[str, Any]:
        """Get idea banks with filtering and pagination."""
        try:
            query = select(IdeaBank).where(IdeaBank.user_id == str(user_id))

            # Apply ordering
            order_column = getattr(IdeaBank, order_by, IdeaBank.updated_at)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

            # Count total items
            count_query = select(IdeaBank).where(IdeaBank.user_id == str(user_id))
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
            logger.error(f"Error getting idea bank list: {e}")
            raise

    async def get_idea_bank(
        self, user_id: UUID, idea_bank_id: UUID
    ) -> Optional[IdeaBank]:
        """Get a specific idea bank item."""
        try:
            query = select(IdeaBank).where(
                and_(IdeaBank.id == str(idea_bank_id), IdeaBank.user_id == str(user_id))
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting idea bank {idea_bank_id}: {e}")
            raise

    async def create_idea_bank(
        self, user_id: UUID, idea_bank_data: IdeaBankCreate
    ) -> IdeaBank:
        """Create a new idea bank item."""
        try:
            # Convert UUID to string for consistent storage across databases
            idea_bank = IdeaBank(user_id=str(user_id), **idea_bank_data.model_dump())
            self.db.add(idea_bank)
            await self.db.commit()
            await self.db.refresh(idea_bank)
            logger.info(f"Created idea bank {idea_bank.id} for user {user_id}")
            return idea_bank
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating idea bank: {e}")
            raise

    async def update_idea_bank(
        self, user_id: UUID, idea_bank_id: UUID, update_data: IdeaBankUpdate
    ) -> Optional[IdeaBank]:
        """Update an idea bank item."""
        try:
            query = select(IdeaBank).where(
                and_(IdeaBank.id == str(idea_bank_id), IdeaBank.user_id == str(user_id))
            )
            result = await self.db.execute(query)
            idea_bank = result.scalar_one_or_none()

            if not idea_bank:
                return None

            update_dict = update_data.model_dump(exclude_unset=True)
            if update_dict:
                update_dict["updated_at"] = datetime.now(timezone.utc)
                for key, value in update_dict.items():
                    setattr(idea_bank, key, value)

                await self.db.commit()
                await self.db.refresh(idea_bank)
                logger.info(f"Updated idea bank {idea_bank_id} for user {user_id}")

            return idea_bank
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating idea bank {idea_bank_id}: {e}")
            raise

    async def delete_idea_bank(self, user_id: UUID, idea_bank_id: UUID) -> bool:
        """Delete an idea bank item."""
        try:
            query = delete(IdeaBank).where(
                and_(IdeaBank.id == str(idea_bank_id), IdeaBank.user_id == str(user_id))
            )
            result = await self.db.execute(query)
            await self.db.commit()

            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted idea bank {idea_bank_id} for user {user_id}")
            return deleted
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting idea bank {idea_bank_id}: {e}")
            raise

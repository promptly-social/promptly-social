"""
Idea Bank service for business logic.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, desc, func, select, Boolean, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.idea_bank import IdeaBank
from app.models.posts import Post
from app.schemas.idea_bank import IdeaBankCreate, IdeaBankUpdate


class IdeaBankService:
    """Service for idea bank operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_idea_banks_list(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        order_by: str = "updated_at",
        order_direction: str = "desc",
        ai_suggested: Optional[bool] = None,
        evergreen: Optional[bool] = None,
        has_post: Optional[bool] = None,
        post_status: Optional[str] = None,
    ) -> Dict:
        """Get idea banks with filtering and pagination."""
        try:
            # Build filters
            filters = [IdeaBank.user_id == user_id]

            # Note: JSON field filtering is handled in Python after retrieval
            # since our custom JSONType doesn't support SQLAlchemy JSON operators

            # For has_post and post_status filters, we need to join with posts
            join_posts = has_post is not None or post_status is not None

            if join_posts:
                # Build the main query with join
                query_base = select(IdeaBank).join(
                    Post,
                    IdeaBank.id == Post.idea_bank_id,
                    isouter=True,
                )
                count_query_base = select(func.count(IdeaBank.id.distinct())).join(
                    Post,
                    IdeaBank.id == Post.idea_bank_id,
                    isouter=True,
                )

                if has_post is not None:
                    if has_post:
                        filters.append(Post.id.isnot(None))
                    else:
                        filters.append(Post.id.is_(None))

                if post_status:
                    filters.append(Post.status == post_status)
            else:
                query_base = select(IdeaBank)
                count_query_base = select(func.count()).select_from(IdeaBank)

            # Build query for total count
            count_query = count_query_base.where(and_(*filters))
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Build main query with pagination
            offset = (page - 1) * size

            # Order by
            order_column = getattr(IdeaBank, order_by, IdeaBank.updated_at)
            if order_direction.lower() == "desc":
                order_column = desc(order_column)

            query = (
                query_base.where(and_(*filters))
                .order_by(order_column)
                .offset(offset)
                .limit(size)
            )

            if join_posts:
                query = query.distinct()

            result = await self.db.execute(query)
            idea_banks = result.scalars().all()

            # Apply JSON field filtering in Python since our JSONType doesn't support SQL operators
            filtered_idea_banks = []
            for idea_bank in idea_banks:
                data = idea_bank.data or {}

                # Filter by AI suggested
                if ai_suggested is not None:
                    bank_ai_suggested = data.get("ai_suggested", False)
                    if isinstance(bank_ai_suggested, str):
                        bank_ai_suggested = bank_ai_suggested.lower() == "true"
                    if bank_ai_suggested != ai_suggested:
                        continue

                # Filter by evergreen (inverse of time_sensitive)
                if evergreen is not None:
                    bank_time_sensitive = data.get("time_sensitive", False)
                    if isinstance(bank_time_sensitive, str):
                        bank_time_sensitive = bank_time_sensitive.lower() == "true"

                    if (
                        evergreen and bank_time_sensitive
                    ):  # Want evergreen but it's time sensitive
                        continue
                    if (
                        not evergreen and not bank_time_sensitive
                    ):  # Want time sensitive but it's evergreen
                        continue

                filtered_idea_banks.append(idea_bank)

            # Recalculate pagination for filtered results
            filtered_total = len(filtered_idea_banks)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_banks = filtered_idea_banks[start_idx:end_idx]

            return {
                "items": paginated_banks,
                "total": filtered_total,
                "page": page,
                "size": size,
                "has_next": filtered_total > page * size,
            }

        except Exception as e:
            logger.error(f"Error getting idea banks list: {e}")
            raise

    async def get_idea_banks_with_latest_posts(
        self,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        order_by: str = "updated_at",
        order_direction: str = "desc",
        ai_suggested: Optional[bool] = None,
        evergreen: Optional[bool] = None,
        has_post: Optional[bool] = None,
        post_status: Optional[List[str]] = None,
    ) -> Dict:
        """Get idea banks with their latest suggested posts."""
        try:
            # Build filters for idea banks
            filters = [IdeaBank.user_id == user_id]

            # Note: JSON field filtering is handled in Python after retrieval
            # since our custom JSONType doesn't support SQLAlchemy JSON operators

            # Build subquery for latest posts
            latest_post_subquery = (
                select(
                    Post.idea_bank_id,
                    func.max(Post.updated_at).label("latest_updated_at"),
                )
                .group_by(Post.idea_bank_id)
                .subquery()
            )

            # Build main query
            query_base = (
                select(IdeaBank, Post)
                .outerjoin(
                    latest_post_subquery,
                    IdeaBank.id == latest_post_subquery.c.idea_bank_id,
                )
                .outerjoin(
                    Post,
                    and_(
                        Post.idea_bank_id == latest_post_subquery.c.idea_bank_id,
                        Post.updated_at == latest_post_subquery.c.latest_updated_at,
                    ),
                )
            )

            # Apply post-related filters
            if has_post is not None:
                if has_post:
                    filters.append(Post.id.isnot(None))
                else:
                    filters.append(Post.id.is_(None))

            if post_status and len(post_status) > 0:
                # Include idea banks without posts OR with posts matching the status
                filters.append(
                    or_(
                        Post.id.is_(None),  # No posts
                        Post.status.in_(post_status),  # Posts with matching status
                    )
                )

            # Count query
            count_query = select(func.count(IdeaBank.id.distinct())).select_from(
                query_base.where(and_(*filters)).subquery()
            )
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Main query with pagination
            offset = (page - 1) * size
            order_column = getattr(IdeaBank, order_by, IdeaBank.updated_at)
            if order_direction.lower() == "desc":
                order_column = desc(order_column)

            query = (
                query_base.where(and_(*filters))
                .order_by(order_column)
                .offset(offset)
                .limit(size)
                .distinct()
            )

            result = await self.db.execute(query)
            rows = result.all()

            # Format the response and apply JSON field filtering in Python
            items = []
            for row in rows:
                idea_bank = row[0]  # First element is IdeaBank
                post = row[1] if len(row) > 1 else None  # Second element is Post

                # Apply JSON field filtering since our JSONType doesn't support SQL operators
                data = idea_bank.data or {}

                # Filter by AI suggested
                if ai_suggested is not None:
                    bank_ai_suggested = data.get("ai_suggested", False)
                    if isinstance(bank_ai_suggested, str):
                        bank_ai_suggested = bank_ai_suggested.lower() == "true"
                    if bank_ai_suggested != ai_suggested:
                        continue

                # Filter by evergreen (inverse of time_sensitive)
                if evergreen is not None:
                    bank_time_sensitive = data.get("time_sensitive", False)
                    if isinstance(bank_time_sensitive, str):
                        bank_time_sensitive = bank_time_sensitive.lower() == "true"

                    if (
                        evergreen and bank_time_sensitive
                    ):  # Want evergreen but it's time sensitive
                        continue
                    if (
                        not evergreen and not bank_time_sensitive
                    ):  # Want time sensitive but it's evergreen
                        continue

                items.append({"idea_bank": idea_bank, "latest_post": post})

            # Recalculate total for filtered results
            filtered_total = len(items)

            return {
                "items": items,
                "total": filtered_total,
                "page": page,
                "size": size,
                "has_next": filtered_total > page * size,
            }

        except Exception as e:
            logger.error(f"Error getting idea banks with latest posts: {e}")
            raise

    async def get_idea_bank(
        self, user_id: UUID, idea_bank_id: UUID
    ) -> Optional[IdeaBank]:
        """Get a specific idea bank."""
        try:
            query = select(IdeaBank).where(
                and_(
                    IdeaBank.id == idea_bank_id,
                    IdeaBank.user_id == user_id,
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting idea bank {idea_bank_id}: {e}")
            raise

    async def get_idea_bank_with_latest_post(
        self, user_id: UUID, idea_bank_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get a specific idea bank with its latest post."""
        try:
            # Get the idea bank
            idea_bank = await self.get_idea_bank(user_id, idea_bank_id)
            if not idea_bank:
                return None

            # Get the latest post for this idea bank
            latest_post_query = (
                select(Post)
                .where(Post.idea_bank_id == idea_bank_id)
                .order_by(desc(Post.updated_at))
                .limit(1)
            )
            latest_post_result = await self.db.execute(latest_post_query)
            latest_post = latest_post_result.scalar_one_or_none()

            return {"idea_bank": idea_bank, "latest_post": latest_post}

        except Exception as e:
            logger.error(
                f"Error getting idea bank with latest post {idea_bank_id}: {e}"
            )
            raise

    async def create_idea_bank(
        self, user_id: UUID, idea_bank_data: IdeaBankCreate
    ) -> IdeaBank:
        """Create a new idea bank."""
        try:
            idea_bank = IdeaBank(
                user_id=user_id,
                data=idea_bank_data.data.model_dump(),
            )

            self.db.add(idea_bank)
            await self.db.commit()
            await self.db.refresh(idea_bank)
            return idea_bank

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating idea bank: {e}")
            raise

    async def update_idea_bank(
        self, user_id: UUID, idea_bank_id: UUID, update_data: IdeaBankUpdate
    ) -> Optional[IdeaBank]:
        """Update an idea bank."""
        try:
            idea_bank = await self.get_idea_bank(user_id, idea_bank_id)
            if not idea_bank:
                return None

            # Update the data field
            if update_data.data:
                idea_bank.data = update_data.data.model_dump()

            await self.db.commit()
            await self.db.refresh(idea_bank)
            return idea_bank

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating idea bank {idea_bank_id}: {e}")
            raise

    async def delete_idea_bank(self, user_id: UUID, idea_bank_id: UUID) -> bool:
        """Delete an idea bank."""
        try:
            idea_bank = await self.get_idea_bank(user_id, idea_bank_id)
            if not idea_bank:
                return False

            await self.db.delete(idea_bank)
            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting idea bank {idea_bank_id}: {e}")
            raise

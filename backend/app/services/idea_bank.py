"""
Idea Bank service for handling idea bank related business logic.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, asc, delete, desc, func, select, or_, Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.idea_bank import IdeaBank
from app.models.suggested_posts import SuggestedPost
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
        ai_suggested: Optional[bool] = None,
        evergreen: Optional[bool] = None,
        has_post: Optional[bool] = None,
        post_status: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get idea banks with filtering and pagination."""
        try:
            # Base query
            query = select(IdeaBank).where(IdeaBank.user_id == str(user_id))

            # Apply filters
            if ai_suggested is not None:
                query = query.where(
                    IdeaBank.data["ai_suggested"].astext.cast(Boolean) == ai_suggested
                )

            if evergreen is not None:
                # Evergreen means NOT time_sensitive
                query = query.where(
                    IdeaBank.data["time_sensitive"].astext.cast(Boolean) != evergreen
                )

            # For has_post and post_status filters, we need to join with suggested_posts
            if has_post is not None or post_status is not None:
                # Create subquery to get latest post for each idea_bank_id
                latest_post_subquery = (
                    select(
                        SuggestedPost.idea_bank_id,
                        func.max(SuggestedPost.created_at).label("latest_created_at"),
                    )
                    .where(SuggestedPost.user_id == str(user_id))
                    .group_by(SuggestedPost.idea_bank_id)
                    .subquery()
                )

                # Join with the subquery to get the actual latest posts
                latest_posts = (
                    select(SuggestedPost)
                    .join(
                        latest_post_subquery,
                        and_(
                            SuggestedPost.idea_bank_id
                            == latest_post_subquery.c.idea_bank_id,
                            SuggestedPost.created_at
                            == latest_post_subquery.c.latest_created_at,
                        ),
                    )
                    .subquery()
                )

                if has_post is True:
                    # Only show ideas that have posts
                    query = query.join(
                        latest_posts, IdeaBank.id == latest_posts.c.idea_bank_id
                    )
                elif has_post is False:
                    # Only show ideas that don't have posts
                    query = query.outerjoin(
                        latest_posts, IdeaBank.id == latest_posts.c.idea_bank_id
                    )
                    query = query.where(latest_posts.c.id.is_(None))
                else:
                    # has_post is None (All), but we have post_status filter
                    # Use left join to include ideas without posts
                    if post_status is not None:
                        query = query.outerjoin(
                            latest_posts, IdeaBank.id == latest_posts.c.idea_bank_id
                        )

                if post_status is not None:
                    if has_post is True:
                        # Already joined above, just filter by status
                        query = query.where(latest_posts.c.status.in_(post_status))
                    elif has_post is False:
                        # This case doesn't make sense - can't have no posts but filter by status
                        # We'll ignore the post_status filter in this case
                        pass
                    else:
                        # has_post is None (All) - include ideas without posts OR with matching status
                        query = query.where(
                            or_(
                                latest_posts.c.id.is_(None),  # No posts
                                latest_posts.c.status.in_(
                                    post_status
                                ),  # Or matching status
                            )
                        )

            # Apply ordering
            order_column = getattr(IdeaBank, order_by, IdeaBank.updated_at)
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

            # Count total items with same filters
            count_query = select(func.count(IdeaBank.id)).where(
                IdeaBank.user_id == str(user_id)
            )

            # Apply same filters to count query
            if ai_suggested is not None:
                count_query = count_query.where(
                    IdeaBank.data["ai_suggested"].astext.cast(Boolean) == ai_suggested
                )

            if evergreen is not None:
                count_query = count_query.where(
                    IdeaBank.data["time_sensitive"].astext.cast(Boolean) != evergreen
                )

            if has_post is not None or post_status is not None:
                # Apply same join logic for count
                latest_post_subquery_count = (
                    select(
                        SuggestedPost.idea_bank_id,
                        func.max(SuggestedPost.created_at).label("latest_created_at"),
                    )
                    .where(SuggestedPost.user_id == str(user_id))
                    .group_by(SuggestedPost.idea_bank_id)
                    .subquery()
                )

                latest_posts_count = (
                    select(SuggestedPost)
                    .join(
                        latest_post_subquery_count,
                        and_(
                            SuggestedPost.idea_bank_id
                            == latest_post_subquery_count.c.idea_bank_id,
                            SuggestedPost.created_at
                            == latest_post_subquery_count.c.latest_created_at,
                        ),
                    )
                    .subquery()
                )

                if has_post is True:
                    count_query = count_query.join(
                        latest_posts_count,
                        IdeaBank.id == latest_posts_count.c.idea_bank_id,
                    )
                elif has_post is False:
                    count_query = count_query.outerjoin(
                        latest_posts_count,
                        IdeaBank.id == latest_posts_count.c.idea_bank_id,
                    )
                    count_query = count_query.where(latest_posts_count.c.id.is_(None))
                else:
                    # has_post is None (All), but we have post_status filter
                    # Use left join to include ideas without posts
                    if post_status is not None:
                        count_query = count_query.outerjoin(
                            latest_posts_count,
                            IdeaBank.id == latest_posts_count.c.idea_bank_id,
                        )

                if post_status is not None:
                    if has_post is True:
                        # Already joined above, just filter by status
                        count_query = count_query.where(
                            latest_posts_count.c.status.in_(post_status)
                        )
                    elif has_post is False:
                        # This case doesn't make sense - can't have no posts but filter by status
                        # We'll ignore the post_status filter in this case
                        pass
                    else:
                        # has_post is None (All) - include ideas without posts OR with matching status
                        count_query = count_query.where(
                            or_(
                                latest_posts_count.c.id.is_(None),  # No posts
                                latest_posts_count.c.status.in_(
                                    post_status
                                ),  # Or matching status
                            )
                        )

            total_result = await self.db.execute(count_query)
            total = total_result.scalar()

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

    async def get_idea_bank_with_latest_post(
        self, user_id: UUID, idea_bank_id: UUID
    ) -> Dict[str, Any]:
        """Get an idea bank item with its latest suggested post."""
        try:
            # Get the idea bank
            idea_bank_query = select(IdeaBank).where(
                and_(IdeaBank.id == str(idea_bank_id), IdeaBank.user_id == str(user_id))
            )
            idea_bank_result = await self.db.execute(idea_bank_query)
            idea_bank = idea_bank_result.scalar_one_or_none()

            if not idea_bank:
                return None

            # Get the latest suggested post for this idea bank
            latest_post_query = (
                select(SuggestedPost)
                .where(
                    and_(
                        SuggestedPost.idea_bank_id == str(idea_bank_id),
                        SuggestedPost.user_id == str(user_id),
                    )
                )
                .order_by(desc(SuggestedPost.created_at))
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
    ) -> Dict[str, Any]:
        """Get idea banks with their latest suggested posts."""
        try:
            # Get the filtered idea banks
            idea_banks_result = await self.get_idea_bank_list(
                user_id=user_id,
                page=page,
                size=size,
                order_by=order_by,
                order_direction=order_direction,
                ai_suggested=ai_suggested,
                evergreen=evergreen,
                has_post=has_post,
                post_status=post_status,
            )

            idea_banks = idea_banks_result["items"]

            # Get latest posts for each idea bank
            idea_bank_ids = [idea_bank.id for idea_bank in idea_banks]

            if idea_bank_ids:
                # Get latest post for each idea bank
                latest_posts_subquery = (
                    select(
                        SuggestedPost.idea_bank_id,
                        func.max(SuggestedPost.created_at).label("latest_created_at"),
                    )
                    .where(
                        and_(
                            SuggestedPost.idea_bank_id.in_(idea_bank_ids),
                            SuggestedPost.user_id == str(user_id),
                        )
                    )
                    .group_by(SuggestedPost.idea_bank_id)
                    .subquery()
                )

                latest_posts_query = select(SuggestedPost).join(
                    latest_posts_subquery,
                    and_(
                        SuggestedPost.idea_bank_id
                        == latest_posts_subquery.c.idea_bank_id,
                        SuggestedPost.created_at
                        == latest_posts_subquery.c.latest_created_at,
                    ),
                )

                latest_posts_result = await self.db.execute(latest_posts_query)
                latest_posts = latest_posts_result.scalars().all()

                # Create a mapping of idea_bank_id to latest_post
                posts_by_idea_bank = {post.idea_bank_id: post for post in latest_posts}
            else:
                posts_by_idea_bank = {}

            # Combine idea banks with their latest posts
            enriched_items = []
            for idea_bank in idea_banks:
                latest_post = posts_by_idea_bank.get(idea_bank.id)
                enriched_items.append(
                    {"idea_bank": idea_bank, "latest_post": latest_post}
                )

            return {
                "items": enriched_items,
                "total": idea_banks_result["total"],
                "page": idea_banks_result["page"],
                "size": idea_banks_result["size"],
                "has_next": idea_banks_result["has_next"],
            }

        except Exception as e:
            logger.error(f"Error getting idea banks with latest posts: {e}")
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

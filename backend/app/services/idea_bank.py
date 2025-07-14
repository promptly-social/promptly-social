"""
Idea Bank service for business logic.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import and_, desc, func, select, Boolean, text, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.idea_bank import IdeaBank
from app.models.posts import Post
from app.models.profile import UserPreferences, WritingStyleAnalysis
from app.models.content_strategies import ContentStrategy
from app.schemas.idea_bank import IdeaBankCreate, IdeaBankUpdate
from app.schemas.posts import PostCreate, PostResponse
from app.services.post_generator import post_generator_service
from app.services.profile import ProfileService


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

            # For has_post and post_status filters, we need to join with posts
            join_posts = has_post is not None or post_status is not None

            # Determine if we need to filter in-memory for JSON fields
            in_memory_filter = ai_suggested is not None or evergreen is not None

            if join_posts:
                query_base = select(IdeaBank).join(
                    Post, IdeaBank.id == Post.idea_bank_id, isouter=True
                )
                if has_post is not None:
                    filters.append(
                        Post.id.isnot(None) if has_post else Post.id.is_(None)
                    )
                if post_status:
                    filters.append(Post.status == post_status)
            else:
                query_base = select(IdeaBank)

            query = query_base.where(and_(*filters))

            if in_memory_filter:
                # Fetch all results from DB if we have in-memory filters
                result = await self.db.execute(query.distinct())
                all_idea_banks = result.scalars().all()

                # In-memory filtering
                filtered_idea_banks = []
                for idea_bank in all_idea_banks:
                    data = idea_bank.data or {}
                    # AI suggested filter
                    if ai_suggested is not None:
                        bank_ai_suggested = data.get("ai_suggested", False)
                        if isinstance(bank_ai_suggested, str):
                            bank_ai_suggested = bank_ai_suggested.lower() == "true"
                        if bank_ai_suggested != ai_suggested:
                            continue
                    # Evergreen filter
                    if evergreen is not None:
                        bank_time_sensitive = data.get("time_sensitive", False)
                        if isinstance(bank_time_sensitive, str):
                            bank_time_sensitive = bank_time_sensitive.lower() == "true"
                        if (evergreen and bank_time_sensitive) or (
                            not evergreen and not bank_time_sensitive
                        ):
                            continue
                    filtered_idea_banks.append(idea_bank)

                # In-memory sorting
                reverse = order_direction.lower() == "desc"
                filtered_idea_banks.sort(
                    key=lambda ib: getattr(ib, order_by, ib.updated_at),
                    reverse=reverse,
                )

                # In-memory pagination
                total = len(filtered_idea_banks)
                offset = (page - 1) * size
                paginated_banks = filtered_idea_banks[offset : offset + size]

                return {
                    "items": paginated_banks,
                    "total": total,
                    "page": page,
                    "size": size,
                    "has_next": total > page * size,
                }

            # Original path (no in-memory filtering)
            count_query_base = select(
                func.count(IdeaBank.id.distinct() if join_posts else IdeaBank.id)
            ).select_from(query.subquery())
            count_result = await self.db.execute(count_query_base)
            total = count_result.scalar() or 0

            offset = (page - 1) * size
            order_column = getattr(IdeaBank, order_by, IdeaBank.updated_at)
            if order_direction.lower() == "desc":
                order_column = desc(order_column)

            paginated_query = query.order_by(order_column).offset(offset).limit(size)
            if join_posts:
                paginated_query = paginated_query.distinct()

            result = await self.db.execute(paginated_query)
            idea_banks = result.scalars().all()

            return {
                "items": idea_banks,
                "total": total,
                "page": page,
                "size": size,
                "has_next": total > page * size,
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
        has_post: Optional[bool] = None,
    ) -> Dict:
        """Get idea banks with their latest suggested posts."""
        try:
            # Build filters for idea banks
            filters = [IdeaBank.user_id == user_id]

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

            # Base query with filters
            query = query_base.where(and_(*filters))

            # If filtering on a JSON field, we must fetch all, then filter/sort/paginate in memory.
            if ai_suggested is not None:
                result = await self.db.execute(query.distinct())
                all_rows = result.all()

                # In-memory filtering
                items = []
                for row in all_rows:
                    idea_bank, post = row[0], row[1] if len(row) > 1 else None
                    data = idea_bank.data or {}

                    # Filter by AI suggested
                    bank_ai_suggested = data.get("ai_suggested", False)
                    if isinstance(bank_ai_suggested, str):
                        bank_ai_suggested = bank_ai_suggested.lower() == "true"
                    if bank_ai_suggested != ai_suggested:
                        continue

                    items.append({"idea_bank": idea_bank, "latest_post": post})

                # In-memory sorting
                reverse = order_direction.lower() == "desc"
                items.sort(
                    key=lambda x: getattr(
                        x["idea_bank"], order_by, x["idea_bank"].updated_at
                    ),
                    reverse=reverse,
                )

                # In-memory pagination
                total = len(items)
                offset = (page - 1) * size
                paginated_items = items[offset : offset + size]

                return {
                    "items": paginated_items,
                    "total": total,
                    "page": page,
                    "size": size,
                    "has_next": total > page * size,
                }

            # Original path (no JSON filtering)
            count_query = select(func.count(IdeaBank.id.distinct())).select_from(
                query.subquery()
            )
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0

            # Main query with pagination
            offset = (page - 1) * size
            order_column = getattr(IdeaBank, order_by, IdeaBank.updated_at)
            if order_direction.lower() == "desc":
                order_column = desc(order_column)

            paginated_query = (
                query.order_by(order_column).offset(offset).limit(size).distinct()
            )

            result = await self.db.execute(paginated_query)
            rows = result.all()

            # Format the response
            items = [
                {"idea_bank": row[0], "latest_post": row[1] if len(row) > 1 else None}
                for row in rows
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "size": size,
                "has_next": total > page * size,
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
        """Update an idea bank entry."""
        try:
            idea_bank = await self.get_idea_bank(user_id, idea_bank_id)
            if not idea_bank:
                return None

            update_data_dict = update_data.model_dump(exclude_unset=True)

            if "data" in update_data_dict:
                idea_bank.data = update_data_dict["data"]
                # Required for JSON mutation to be detected by SQLAlchemy
                idea_bank.updated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(idea_bank)
            logger.info(f"Updated idea bank {idea_bank_id} for user {user_id}")
            return idea_bank
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating idea bank {idea_bank_id}: {e}")
            raise

    async def generate_post_from_idea(
        self, user_id: UUID, idea_bank_id: UUID
    ) -> Optional[PostResponse]:
        """Generate a new post from an idea bank entry."""
        try:
            # 1. Fetch the idea bank entry
            idea_bank = await self.get_idea_bank(user_id, idea_bank_id)
            if not idea_bank or not idea_bank.data:
                logger.warning(f"Idea bank {idea_bank_id} not found for user {user_id}")
                return None

            # 2. Fetch user profile information
            profile_service = ProfileService(self.db)
            preferences = await profile_service.get_user_preferences(user_id)
            latest_analysis = await profile_service.get_latest_writing_style_analysis(
                user_id
            )
            content_strategies = await profile_service.get_content_strategies(user_id)

            linkedin_strategy = next(
                (s for s in content_strategies if s.platform == "linkedin"), None
            )

            # 3. Generate the post using the appropriate AI service method based on type
            idea_type = idea_bank.data.get("type", "text")

            if idea_type == "product":
                # For product type, use the product-specific generator
                product_name = idea_bank.data.get("product_name", "")
                product_description = idea_bank.data.get("product_description", "")
                product_url = idea_bank.data.get("value", "")

                generated_data = await post_generator_service.generate_post_for_product(
                    product_name=product_name,
                    product_description=product_description,
                    product_url=product_url,
                    bio=preferences.bio if preferences else "Bio not provided",
                    writing_style=latest_analysis.analysis_data
                    if latest_analysis
                    else "Writing style not provided",
                    linkedin_post_strategy=linkedin_strategy.strategy
                    if linkedin_strategy
                    else "LinkedIn post strategy not provided",
                )
            else:
                # For url and text types, use the regular generator
                idea_content = idea_bank.data.get("value", "")
                if idea_bank.data.get("title"):
                    idea_content = f"{idea_bank.data['title']}\\n\\n{idea_content}"

                generated_data = await post_generator_service.generate_post(
                    idea_content=idea_content,
                    bio=preferences.bio if preferences else "Bio not provided",
                    writing_style=latest_analysis.analysis_data
                    if latest_analysis
                    else "Writing style not provided",
                    linkedin_post_strategy=linkedin_strategy.strategy
                    if linkedin_strategy
                    else "LinkedIn post strategy not provided",
                )

            # 4. Save the new post to the database
            new_post_data = PostCreate(
                content=generated_data.linkedin_post,
                idea_bank_id=idea_bank_id,
                status="suggested",
                topics=generated_data.topics,
            )

            new_post = Post(user_id=user_id, **new_post_data.model_dump())
            self.db.add(new_post)
            await self.db.commit()
            await self.db.refresh(new_post)

            logger.info(f"Generated new post {new_post.id} from idea {idea_bank_id}")

            return PostResponse.model_validate(new_post)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error generating post from idea {idea_bank_id}: {e}")
            raise

    async def delete_idea_bank(self, user_id: UUID, idea_bank_id: UUID) -> bool:
        """Delete an idea bank entry."""
        try:
            idea_bank = await self.get_idea_bank(user_id, idea_bank_id)
            if not idea_bank:
                return False

            # Disassociate posts from the idea bank before deleting
            update_stmt = (
                update(Post)
                .where(Post.idea_bank_id == idea_bank_id)
                .values(idea_bank_id=None)
            )
            await self.db.execute(update_stmt)

            await self.db.delete(idea_bank)
            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting idea bank {idea_bank_id}: {e}")
            raise

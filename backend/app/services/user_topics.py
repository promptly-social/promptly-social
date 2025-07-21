"""
User Topics service for managing user topics and their colors.
"""

from typing import Dict, List, Optional, Set
from uuid import UUID

from loguru import logger
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_topics import UserTopic
from app.models.posts import Post
from app.schemas.user_topics import UserTopicCreate, UserTopicUpdate


class UserTopicsService:
    """Service for managing user topics and their colors."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_topics(self, user_id: UUID) -> List[UserTopic]:
        """Get all topics for a user."""
        try:
            result = await self.db.execute(
                select(UserTopic)
                .where(UserTopic.user_id == user_id)
                .order_by(UserTopic.topic)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user topics for user {user_id}: {e}")
            raise

    async def get_user_topic(
        self, user_id: UUID, topic_id: UUID
    ) -> Optional[UserTopic]:
        """Get a specific topic for a user."""
        try:
            result = await self.db.execute(
                select(UserTopic).where(
                    and_(UserTopic.user_id == user_id, UserTopic.id == topic_id)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user topic {topic_id} for user {user_id}: {e}")
            raise

    async def get_user_topic_by_name(
        self, user_id: UUID, topic_name: str
    ) -> Optional[UserTopic]:
        """Get a specific topic by name for a user."""
        try:
            result = await self.db.execute(
                select(UserTopic).where(
                    and_(UserTopic.user_id == user_id, UserTopic.topic == topic_name)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting user topic '{topic_name}' for user {user_id}: {e}"
            )
            raise

    async def create_user_topic(
        self, user_id: UUID, topic_data: UserTopicCreate
    ) -> UserTopic:
        """Create a new topic for a user."""
        try:
            # Check if topic already exists for this user
            existing_topic = await self.get_user_topic_by_name(
                user_id, topic_data.topic
            )
            if existing_topic:
                raise ValueError(f"Topic '{topic_data.topic}' already exists for user")

            # Create new topic with color (use provided color or generate random)
            if topic_data.color:
                new_topic = UserTopic(
                    user_id=user_id, topic=topic_data.topic, color=topic_data.color
                )
            else:
                new_topic = UserTopic.create_with_random_color(
                    user_id, topic_data.topic
                )

            self.db.add(new_topic)
            await self.db.commit()
            await self.db.refresh(new_topic)

            logger.info(f"Created topic '{topic_data.topic}' for user {user_id}")
            return new_topic
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user topic for user {user_id}: {e}")
            raise

    async def update_user_topic(
        self, user_id: UUID, topic_id: UUID, update_data: UserTopicUpdate
    ) -> Optional[UserTopic]:
        """Update a user topic."""
        try:
            topic = await self.get_user_topic(user_id, topic_id)
            if not topic:
                return None

            # Check if new topic name conflicts with existing topics
            if update_data.topic and update_data.topic != topic.topic:
                existing_topic = await self.get_user_topic_by_name(
                    user_id, update_data.topic
                )
                if existing_topic:
                    raise ValueError(
                        f"Topic '{update_data.topic}' already exists for user"
                    )

            # Update fields
            if update_data.topic is not None:
                topic.topic = update_data.topic
            if update_data.color is not None:
                topic.color = update_data.color

            await self.db.commit()
            await self.db.refresh(topic)

            logger.info(f"Updated topic {topic_id} for user {user_id}")
            return topic
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating user topic {topic_id} for user {user_id}: {e}"
            )
            raise

    async def delete_user_topic(self, user_id: UUID, topic_id: UUID) -> bool:
        """Delete a user topic."""
        try:
            topic = await self.get_user_topic(user_id, topic_id)
            if not topic:
                return False

            await self.db.delete(topic)
            await self.db.commit()

            logger.info(f"Deleted topic {topic_id} for user {user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error deleting user topic {topic_id} for user {user_id}: {e}"
            )
            raise

    async def get_topic_colors_map(self, user_id: UUID) -> Dict[str, str]:
        """Get a mapping of topic names to colors for a user."""
        try:
            topics = await self.get_user_topics(user_id)
            return {topic.topic: topic.color for topic in topics}
        except Exception as e:
            logger.error(f"Error getting topic colors map for user {user_id}: {e}")
            raise

    async def sync_topics_from_posts(self, user_id: UUID) -> List[UserTopic]:
        """
        Sync topics from user's posts to create UserTopic entries for any missing topics.
        Returns list of newly created topics.
        """
        try:
            # Get all unique topics from user's posts
            result = await self.db.execute(
                select(Post.topics)
                .where(Post.user_id == user_id)
                .where(Post.topics.isnot(None))
            )

            all_post_topics: Set[str] = set()
            for post_topics in result.scalars():
                if post_topics:
                    all_post_topics.update(post_topics)

            # Get existing user topics
            existing_topics = await self.get_user_topics(user_id)
            existing_topic_names = {topic.topic for topic in existing_topics}

            # Find topics that don't have UserTopic entries
            missing_topics = all_post_topics - existing_topic_names

            # Create UserTopic entries for missing topics
            new_topics = []
            for topic_name in missing_topics:
                new_topic = UserTopic.create_with_random_color(user_id, topic_name)
                self.db.add(new_topic)
                new_topics.append(new_topic)

            if new_topics:
                await self.db.commit()
                for topic in new_topics:
                    await self.db.refresh(topic)

                logger.info(f"Created {len(new_topics)} new topics for user {user_id}")

            return new_topics
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error syncing topics from posts for user {user_id}: {e}")
            raise

    async def bulk_create_topics(
        self, user_id: UUID, topic_names: List[str]
    ) -> List[UserTopic]:
        """
        Bulk create topics for a user, skipping any that already exist.
        Returns list of newly created topics.
        """
        try:
            # Get existing topics to avoid duplicates
            existing_topics = await self.get_user_topics(user_id)
            existing_topic_names = {topic.topic for topic in existing_topics}

            # Filter out existing topics
            new_topic_names = [
                name for name in topic_names if name not in existing_topic_names
            ]

            # Create new topics
            new_topics = []
            for topic_name in new_topic_names:
                new_topic = UserTopic.create_with_random_color(user_id, topic_name)
                self.db.add(new_topic)
                new_topics.append(new_topic)

            if new_topics:
                await self.db.commit()
                for topic in new_topics:
                    await self.db.refresh(topic)

                logger.info(f"Bulk created {len(new_topics)} topics for user {user_id}")

            return new_topics
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error bulk creating topics for user {user_id}: {e}")
            raise

"""
Database query layer for user activity analysis.

This module provides efficient queries for counting posts, messages, and retrieving
content for analysis. It supports incremental analysis by filtering content based
on timestamps and last analyzed content IDs.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.chat import Conversation, Message
from app.models.posts import Post
from app.models.user_activity_analysis import UserAnalysisTracking


class ActivityQueryLayer:
    """
    Database query layer for user activity analysis.

    Provides efficient queries for:
    - Counting posts and messages since last analysis
    - Retrieving new content for analysis
    - Managing analysis state tracking
    """

    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session

    def get_post_counts_since_analysis(
        self, user_id: UUID, since_timestamp: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get counts of scheduled and dismissed posts since last analysis.

        Args:
            user_id: User ID to query for
            since_timestamp: Only count posts created after this timestamp

        Returns:
            Dictionary with 'scheduled_count' and 'dismissed_count'
        """
        base_query = select(Post).where(Post.user_id == user_id)

        if since_timestamp:
            base_query = base_query.where(Post.created_at > since_timestamp)

        # Count scheduled posts (status = 'scheduled' or 'posted')
        scheduled_query = base_query.where(
            or_(Post.status == "scheduled", Post.status == "posted")
        )
        scheduled_count = len(self.session.execute(scheduled_query).scalars().all())

        # Count dismissed posts (status = 'dismissed' or user_feedback = 'negative')
        dismissed_query = base_query.where(
            or_(Post.status == "dismissed", Post.user_feedback == "negative")
        )
        dismissed_count = len(self.session.execute(dismissed_query).scalars().all())

        return {"scheduled_count": scheduled_count, "dismissed_count": dismissed_count}

    def get_message_count_since_analysis(
        self,
        user_id: UUID,
        since_timestamp: Optional[datetime] = None,
        exclude_idea_bank_first_messages: bool = True,
    ) -> int:
        """
        Get count of conversation messages since last analysis.

        Args:
            user_id: User ID to query for
            since_timestamp: Only count messages created after this timestamp
            exclude_idea_bank_first_messages: If True, exclude first user message
                from conversations attached to idea banks

        Returns:
            Total count of messages
        """
        # Base query for conversations by user
        conversation_query = select(Conversation).where(Conversation.user_id == user_id)

        if since_timestamp:
            conversation_query = conversation_query.where(
                Conversation.created_at > since_timestamp
            )

        conversations = self.session.execute(conversation_query).scalars().all()

        total_message_count = 0

        for conversation in conversations:
            # Get messages for this conversation
            message_query = (
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .where(Message.role == "user")  # Only count user messages
            )

            if since_timestamp:
                message_query = message_query.where(
                    Message.created_at > since_timestamp
                )

            messages = (
                self.session.execute(message_query.order_by(Message.created_at))
                .scalars()
                .all()
            )

            message_count = len(messages)

            # Exclude first message if conversation is attached to idea bank
            if (
                exclude_idea_bank_first_messages
                and conversation.idea_bank_id is not None
                and message_count > 0
            ):
                message_count -= 1

            total_message_count += message_count

        return total_message_count

    def get_posts_for_analysis(
        self,
        user_id: UUID,
        since_timestamp: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> Tuple[List[Post], List[Post]]:
        """
        Get posts for analysis, separated into scheduled and dismissed.

        Args:
            user_id: User ID to query for
            since_timestamp: Only get posts created after this timestamp
            limit: Maximum number of posts to return per category

        Returns:
            Tuple of (scheduled_posts, dismissed_posts)
        """
        base_query = select(Post).where(Post.user_id == user_id)

        if since_timestamp:
            base_query = base_query.where(Post.created_at > since_timestamp)

        # Get scheduled posts
        scheduled_query = base_query.where(
            or_(Post.status == "scheduled", Post.status == "posted")
        ).order_by(desc(Post.created_at))

        if limit:
            scheduled_query = scheduled_query.limit(limit)

        scheduled_posts = self.session.execute(scheduled_query).scalars().all()

        # Get dismissed posts
        dismissed_query = base_query.where(
            or_(Post.status == "dismissed", Post.user_feedback == "negative")
        ).order_by(desc(Post.created_at))

        if limit:
            dismissed_query = dismissed_query.limit(limit)

        dismissed_posts = self.session.execute(dismissed_query).scalars().all()

        return scheduled_posts, dismissed_posts

    def get_messages_for_analysis(
        self,
        user_id: UUID,
        since_timestamp: Optional[datetime] = None,
        exclude_idea_bank_first_messages: bool = True,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Get user messages for analysis.

        Args:
            user_id: User ID to query for
            since_timestamp: Only get messages created after this timestamp
            exclude_idea_bank_first_messages: If True, exclude first user message
                from conversations attached to idea banks
            limit: Maximum number of messages to return

        Returns:
            List of Message objects
        """
        # Get conversations for user
        conversation_query = select(Conversation).where(Conversation.user_id == user_id)

        if since_timestamp:
            conversation_query = conversation_query.where(
                Conversation.created_at > since_timestamp
            )

        conversations = self.session.execute(conversation_query).scalars().all()

        all_messages = []

        for conversation in conversations:
            # Get user messages for this conversation
            message_query = select(Message).where(
                and_(Message.conversation_id == conversation.id, Message.role == "user")
            )

            if since_timestamp:
                message_query = message_query.where(
                    Message.created_at > since_timestamp
                )

            messages = (
                self.session.execute(message_query.order_by(Message.created_at))
                .scalars()
                .all()
            )

            # Exclude first message if conversation is attached to idea bank
            if (
                exclude_idea_bank_first_messages
                and conversation.idea_bank_id is not None
                and len(messages) > 0
            ):
                messages = messages[1:]  # Skip first message

            all_messages.extend(messages)

        # Sort all messages by creation time (most recent first)
        all_messages.sort(key=lambda m: m.created_at, reverse=True)

        if limit:
            all_messages = all_messages[:limit]

        return all_messages

    def get_user_analysis_tracking(
        self, user_id: UUID
    ) -> Optional[UserAnalysisTracking]:
        """
        Get analysis tracking record for a user.

        Args:
            user_id: User ID to query for

        Returns:
            UserAnalysisTracking record or None if not found
        """
        query = select(UserAnalysisTracking).where(
            UserAnalysisTracking.user_id == user_id
        )

        result = self.session.execute(query).scalar_one_or_none()
        return result

    def create_or_update_analysis_tracking(
        self,
        user_id: UUID,
        analysis_timestamp: datetime,
        posts_analyzed: Dict,
        messages_analyzed: Dict,
        analysis_types: List[str],
        last_post_id: Optional[UUID] = None,
        last_message_id: Optional[UUID] = None,
    ) -> UserAnalysisTracking:
        """
        Create or update analysis tracking record for a user.

        Args:
            user_id: User ID
            analysis_timestamp: When analysis was completed
            posts_analyzed: Dictionary with post analysis details
            messages_analyzed: Dictionary with message analysis details
            analysis_types: List of analysis types performed
            last_post_id: ID of last post analyzed
            last_message_id: ID of last message analyzed

        Returns:
            Updated UserAnalysisTracking record
        """
        tracking = self.get_user_analysis_tracking(user_id)

        if tracking is None:
            # Create new tracking record
            tracking = UserAnalysisTracking(user_id=user_id)
            self.session.add(tracking)

        # Update tracking record
        tracking.update_analysis_completion(
            analysis_timestamp=analysis_timestamp,
            posts_analyzed=posts_analyzed,
            messages_analyzed=messages_analyzed,
            analysis_types=analysis_types,
            last_post_id=last_post_id,
            last_message_id=last_message_id,
        )

        self.session.commit()
        return tracking

    def get_users_needing_analysis(
        self, post_threshold: int = 5, message_threshold: int = 10
    ) -> List[Tuple[UUID, Dict[str, int]]]:
        """
        Get users who need analysis based on activity thresholds.

        Args:
            post_threshold: Minimum posts (scheduled + dismissed) to trigger analysis
            message_threshold: Minimum messages to trigger analysis

        Returns:
            List of tuples (user_id, activity_counts)
        """
        # Get all users with their last analysis timestamps
        tracking_query = select(UserAnalysisTracking)
        tracking_records = self.session.execute(tracking_query).scalars().all()

        users_needing_analysis = []

        for tracking in tracking_records:
            user_id = tracking.user_id
            last_analysis = tracking.last_analysis_at

            # Get activity counts since last analysis
            post_counts = self.get_post_counts_since_analysis(user_id, last_analysis)
            message_count = self.get_message_count_since_analysis(
                user_id, last_analysis
            )

            total_posts = (
                post_counts["scheduled_count"] + post_counts["dismissed_count"]
            )

            # Check if user meets thresholds
            if total_posts >= post_threshold or message_count >= message_threshold:
                activity_counts = {
                    "scheduled_posts": post_counts["scheduled_count"],
                    "dismissed_posts": post_counts["dismissed_count"],
                    "total_posts": total_posts,
                    "messages": message_count,
                }
                users_needing_analysis.append((user_id, activity_counts))

        return users_needing_analysis

    def get_content_summary_for_analysis(
        self, user_id: UUID, since_timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Get a summary of content available for analysis.

        Args:
            user_id: User ID to query for
            since_timestamp: Only include content created after this timestamp

        Returns:
            Dictionary with content summary
        """
        post_counts = self.get_post_counts_since_analysis(user_id, since_timestamp)
        message_count = self.get_message_count_since_analysis(user_id, since_timestamp)

        # Get latest post and message IDs for tracking
        latest_post_id = None
        latest_message_id = None

        # Get latest post
        post_query = select(Post).where(Post.user_id == user_id)
        if since_timestamp:
            post_query = post_query.where(Post.created_at > since_timestamp)

        latest_post = self.session.execute(
            post_query.order_by(desc(Post.created_at)).limit(1)
        ).scalar_one_or_none()

        if latest_post:
            latest_post_id = latest_post.id

        # Get latest message
        message_query = (
            select(Message).join(Conversation).where(Conversation.user_id == user_id)
        )
        if since_timestamp:
            message_query = message_query.where(Message.created_at > since_timestamp)

        latest_message = self.session.execute(
            message_query.order_by(desc(Message.created_at)).limit(1)
        ).scalar_one_or_none()

        if latest_message:
            latest_message_id = latest_message.id

        return {
            "posts": post_counts,
            "messages": {"total_count": message_count},
            "latest_post_id": latest_post_id,
            "latest_message_id": latest_message_id,
            "analysis_timestamp": datetime.now(),
        }


class AsyncActivityQueryLayer:
    """
    Async version of ActivityQueryLayer for use with async database sessions.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with async database session."""
        self.session = session

    async def get_post_counts_since_analysis(
        self, user_id: UUID, since_timestamp: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Async version of get_post_counts_since_analysis."""
        base_query = select(Post).where(Post.user_id == user_id)

        if since_timestamp:
            base_query = base_query.where(Post.created_at > since_timestamp)

        # Count scheduled posts
        scheduled_query = base_query.where(
            or_(Post.status == "scheduled", Post.status == "posted")
        )
        scheduled_result = await self.session.execute(scheduled_query)
        scheduled_count = len(scheduled_result.scalars().all())

        # Count dismissed posts
        dismissed_query = base_query.where(
            or_(Post.status == "dismissed", Post.user_feedback == "negative")
        )
        dismissed_result = await self.session.execute(dismissed_query)
        dismissed_count = len(dismissed_result.scalars().all())

        return {"scheduled_count": scheduled_count, "dismissed_count": dismissed_count}

    async def get_message_count_since_analysis(
        self,
        user_id: UUID,
        since_timestamp: Optional[datetime] = None,
        exclude_idea_bank_first_messages: bool = True,
    ) -> int:
        """Async version of get_message_count_since_analysis."""
        conversation_query = select(Conversation).where(Conversation.user_id == user_id)

        if since_timestamp:
            conversation_query = conversation_query.where(
                Conversation.created_at > since_timestamp
            )

        conversations_result = await self.session.execute(conversation_query)
        conversations = conversations_result.scalars().all()

        total_message_count = 0

        for conversation in conversations:
            message_query = select(Message).where(
                and_(Message.conversation_id == conversation.id, Message.role == "user")
            )

            if since_timestamp:
                message_query = message_query.where(
                    Message.created_at > since_timestamp
                )

            messages_result = await self.session.execute(
                message_query.order_by(Message.created_at)
            )
            messages = messages_result.scalars().all()

            message_count = len(messages)

            # Exclude first message if conversation is attached to idea bank
            if (
                exclude_idea_bank_first_messages
                and conversation.idea_bank_id is not None
                and message_count > 0
            ):
                message_count -= 1

            total_message_count += message_count

        return total_message_count

    async def get_user_analysis_tracking(
        self, user_id: UUID
    ) -> Optional[UserAnalysisTracking]:
        """Async version of get_user_analysis_tracking."""
        query = select(UserAnalysisTracking).where(
            UserAnalysisTracking.user_id == user_id
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

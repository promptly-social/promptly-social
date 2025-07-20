"""
Activity threshold checking system for user activity analysis.

This module provides the ActivityThresholdChecker class that determines when users
need analysis based on their activity levels (posts and messages) since the last
analysis. It implements the business logic for threshold validation and user
qualification according to requirements 2.1, 2.2, 2.3, and 2.4.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID

# from shared.cloud_sql_client import CloudSQLClient


class ActivityThresholdChecker:
    """
    Checks user activity levels against thresholds to determine analysis eligibility.
    
    This class implements the core logic for:
    - Counting scheduled and dismissed posts since last analysis
    - Counting conversation messages with idea bank exclusion rules
    - Applying timestamp-based filtering for incremental analysis
    - Validating thresholds and determining user qualification
    
    Requirements implemented:
    - 2.1: Trigger analysis when user has >5 scheduled or dismissed posts
    - 2.2: Trigger analysis when user has >10 conversation messages
    - 2.3: Exclude first user message from idea bank conversations
    - 2.4: Process all qualifying users in current batch
    """

    def __init__(self, db_client):
        """
        Initialize the threshold checker with database client.
        
        Args:
            db_client: Database client instance for database operations
        """
        self.db_client = db_client
        self.post_threshold = 5  # Minimum posts to trigger analysis
        self.message_threshold = 10  # Minimum messages to trigger analysis

    async def check_user_activity(
        self, 
        user_id: UUID, 
        last_analysis_at: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Check activity levels for a single user since last analysis.
        
        Args:
            user_id: User ID to check activity for
            last_analysis_at: Timestamp of last analysis (None for first-time analysis)
            
        Returns:
            Dictionary with activity counts:
            {
                'scheduled_posts': int,
                'dismissed_posts': int,
                'total_posts': int,
                'messages': int,
                'meets_threshold': bool
            }
        """
        # Get post counts since last analysis
        post_counts = await self.get_post_counts(user_id, last_analysis_at)
        
        # Get message count since last analysis
        message_count = await self.get_message_counts(user_id, last_analysis_at)
        
        # Calculate totals
        total_posts = post_counts['scheduled_count'] + post_counts['dismissed_count']
        
        # Check if user meets thresholds
        meets_threshold = (
            total_posts >= self.post_threshold or 
            message_count >= self.message_threshold
        )
        
        return {
            'scheduled_posts': post_counts['scheduled_count'],
            'dismissed_posts': post_counts['dismissed_count'],
            'total_posts': total_posts,
            'messages': message_count,
            'meets_threshold': meets_threshold
        }

    async def get_post_counts(
        self, 
        user_id: UUID, 
        since_timestamp: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Count scheduled and dismissed posts for a user since given timestamp.
        
        Args:
            user_id: User ID to count posts for
            since_timestamp: Only count posts created after this timestamp
            
        Returns:
            Dictionary with 'scheduled_count' and 'dismissed_count'
        """
        # Build base query with user filter
        base_conditions = ["user_id = %s"]
        params = [str(user_id)]
        
        # Add timestamp filter if provided
        if since_timestamp:
            base_conditions.append("created_at > %s")
            params.append(since_timestamp)
        
        base_where = " AND ".join(base_conditions)
        
        # Count scheduled posts (status = 'scheduled' OR status = 'posted')
        scheduled_query = f"""
            SELECT COUNT(*) as count
            FROM posts 
            WHERE {base_where}
            AND (status = 'scheduled' OR status = 'posted')
        """
        
        scheduled_result = await self.db_client.fetch_one(scheduled_query, params)
        scheduled_count = scheduled_result['count'] if scheduled_result else 0
        
        # Count dismissed posts (status = 'dismissed' OR user_feedback = 'negative')
        dismissed_query = f"""
            SELECT COUNT(*) as count
            FROM posts 
            WHERE {base_where}
            AND (status = 'dismissed' OR user_feedback = 'negative')
        """
        
        dismissed_result = await self.db_client.fetch_one(dismissed_query, params)
        dismissed_count = dismissed_result['count'] if dismissed_result else 0
        
        return {
            'scheduled_count': scheduled_count,
            'dismissed_count': dismissed_count
        }

    async def get_message_counts(
        self, 
        user_id: UUID, 
        since_timestamp: Optional[datetime] = None
    ) -> int:
        """
        Count conversation messages for a user with idea bank exclusion rules.
        
        Implements requirement 2.3: When counting conversation messages AND the 
        conversation is attached to an idea bank THEN exclude the first user message.
        
        Args:
            user_id: User ID to count messages for
            since_timestamp: Only count messages created after this timestamp
            
        Returns:
            Total count of messages (excluding first messages from idea bank conversations)
        """
        # Get conversations for the user
        conversation_conditions = ["user_id = %s"]
        conversation_params = [str(user_id)]
        
        if since_timestamp:
            conversation_conditions.append("created_at > %s")
            conversation_params.append(since_timestamp)
        
        conversation_where = " AND ".join(conversation_conditions)
        
        conversations_query = f"""
            SELECT id, idea_bank_id, created_at
            FROM conversations 
            WHERE {conversation_where}
            ORDER BY created_at
        """
        
        conversations = await self.db_client.fetch_all(conversations_query, conversation_params)
        
        total_message_count = 0
        
        for conversation in conversations:
            conversation_id = conversation['id']
            idea_bank_id = conversation['idea_bank_id']
            
            # Build message query conditions
            message_conditions = [
                "conversation_id = %s",
                "role = 'user'"  # Only count user messages
            ]
            message_params = [str(conversation_id)]
            
            if since_timestamp:
                message_conditions.append("created_at > %s")
                message_params.append(since_timestamp)
            
            message_where = " AND ".join(message_conditions)
            
            # Get messages for this conversation ordered by creation time
            messages_query = f"""
                SELECT id, created_at
                FROM messages 
                WHERE {message_where}
                ORDER BY created_at
            """
            
            messages = await self.db_client.fetch_all(messages_query, message_params)
            message_count = len(messages)
            
            # Apply idea bank exclusion rule (requirement 2.3)
            if idea_bank_id is not None and message_count > 0:
                # Exclude first user message from idea bank conversations
                message_count -= 1
            
            total_message_count += message_count
        
        return total_message_count

    async def get_users_needing_analysis(
        self, 
        post_threshold: Optional[int] = None,
        message_threshold: Optional[int] = None
    ) -> List[Tuple[UUID, Dict[str, int]]]:
        """
        Get all users who need analysis based on activity thresholds.
        
        Implements requirement 2.4: Process all qualifying users in current batch.
        
        Args:
            post_threshold: Override default post threshold (default: 5)
            message_threshold: Override default message threshold (default: 10)
            
        Returns:
            List of tuples (user_id, activity_counts) for users needing analysis
        """
        # Use provided thresholds or defaults
        post_thresh = post_threshold if post_threshold is not None else self.post_threshold
        message_thresh = message_threshold if message_threshold is not None else self.message_threshold
        
        # Get all users with their analysis tracking data
        tracking_query = """
            SELECT 
                uat.user_id,
                uat.last_analysis_at,
                u.email
            FROM user_analysis_tracking uat
            JOIN users u ON uat.user_id = u.id
            WHERE u.is_active = true
            AND u.deleted_at IS NULL
        """
        
        tracking_records = await self.db_client.fetch_all(tracking_query)
        
        users_needing_analysis = []
        
        for record in tracking_records:
            user_id = UUID(record['user_id'])
            last_analysis_at = record['last_analysis_at']
            
            # Check activity for this user
            activity = await self.check_user_activity(user_id, last_analysis_at)
            
            # Check if user meets thresholds
            if (activity['total_posts'] >= post_thresh or 
                activity['messages'] >= message_thresh):
                
                users_needing_analysis.append((user_id, activity))
        
        return users_needing_analysis

    async def validate_user_qualification(
        self, 
        user_id: UUID, 
        last_analysis_at: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Validate if a user qualifies for analysis and provide detailed breakdown.
        
        Args:
            user_id: User ID to validate
            last_analysis_at: Timestamp of last analysis
            
        Returns:
            Dictionary with qualification details:
            {
                'qualifies': bool,
                'reason': str,
                'activity': Dict[str, int],
                'thresholds': Dict[str, int],
                'next_check_recommendation': str
            }
        """
        activity = await self.check_user_activity(user_id, last_analysis_at)
        
        thresholds = {
            'post_threshold': self.post_threshold,
            'message_threshold': self.message_threshold
        }
        
        # Determine qualification reason
        if activity['total_posts'] >= self.post_threshold:
            reason = f"Post threshold met: {activity['total_posts']} >= {self.post_threshold}"
            qualifies = True
        elif activity['messages'] >= self.message_threshold:
            reason = f"Message threshold met: {activity['messages']} >= {self.message_threshold}"
            qualifies = True
        else:
            reason = (
                f"Thresholds not met: posts={activity['total_posts']}/{self.post_threshold}, "
                f"messages={activity['messages']}/{self.message_threshold}"
            )
            qualifies = False
        
        # Provide recommendation for next check
        posts_needed = max(0, self.post_threshold - activity['total_posts'])
        messages_needed = max(0, self.message_threshold - activity['messages'])
        
        if not qualifies:
            if posts_needed <= messages_needed:
                next_check = f"Need {posts_needed} more posts to trigger analysis"
            else:
                next_check = f"Need {messages_needed} more messages to trigger analysis"
        else:
            next_check = "User qualifies for immediate analysis"
        
        return {
            'qualifies': qualifies,
            'reason': reason,
            'activity': activity,
            'thresholds': thresholds,
            'next_check_recommendation': next_check
        }

    async def get_batch_analysis_summary(
        self, 
        post_threshold: Optional[int] = None,
        message_threshold: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Get summary of users needing analysis for batch processing.
        
        Args:
            post_threshold: Override default post threshold
            message_threshold: Override default message threshold
            
        Returns:
            Dictionary with batch analysis summary
        """
        users_needing_analysis = await self.get_users_needing_analysis(
            post_threshold, message_threshold
        )
        
        # Calculate summary statistics
        total_users = len(users_needing_analysis)
        post_triggered = sum(1 for _, activity in users_needing_analysis 
                           if activity['total_posts'] >= (post_threshold or self.post_threshold))
        message_triggered = sum(1 for _, activity in users_needing_analysis 
                              if activity['messages'] >= (message_threshold or self.message_threshold))
        both_triggered = sum(1 for _, activity in users_needing_analysis 
                           if (activity['total_posts'] >= (post_threshold or self.post_threshold) and
                               activity['messages'] >= (message_threshold or self.message_threshold)))
        
        # Calculate activity totals
        total_posts = sum(activity['total_posts'] for _, activity in users_needing_analysis)
        total_messages = sum(activity['messages'] for _, activity in users_needing_analysis)
        
        return {
            'total_users_needing_analysis': total_users,
            'users_triggered_by_posts': post_triggered,
            'users_triggered_by_messages': message_triggered,
            'users_triggered_by_both': both_triggered,
            'total_posts_to_analyze': total_posts,
            'total_messages_to_analyze': total_messages,
            'thresholds_used': {
                'post_threshold': post_threshold or self.post_threshold,
                'message_threshold': message_threshold or self.message_threshold
            },
            'user_ids': [str(user_id) for user_id, _ in users_needing_analysis]
        }

    def set_thresholds(self, post_threshold: int, message_threshold: int) -> None:
        """
        Update the threshold values for analysis triggering.
        
        Args:
            post_threshold: New post threshold value
            message_threshold: New message threshold value
        """
        if post_threshold < 1 or message_threshold < 1:
            raise ValueError("Thresholds must be positive integers")
        
        self.post_threshold = post_threshold
        self.message_threshold = message_threshold

    def get_current_thresholds(self) -> Dict[str, int]:
        """
        Get current threshold values.
        
        Returns:
            Dictionary with current threshold values
        """
        return {
            'post_threshold': self.post_threshold,
            'message_threshold': self.message_threshold
        }
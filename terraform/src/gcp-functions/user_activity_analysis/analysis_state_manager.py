"""
Analysis state management system for user activity analysis.

This module provides comprehensive state management for tracking analysis progress,
recording analysis scope, and determining new content for incremental processing.

Features:
- Analysis timestamp tracking for incremental processing
- Analysis scope recording and retrieval
- New content detection since last analysis
- State validation and consistency checking
- Recovery mechanisms for interrupted analysis

Requirements implemented:
- 7.1: Analysis start/completion timestamp recording
- 7.2: Analysis scope tracking for incremental processing
- 7.3: New content detection based on timestamps
- 7.4: State validation and consistency checking
- 7.5: Recovery mechanisms for failed analysis
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import json

# from shared.cloud_sql_client import CloudSQLClient

logger = logging.getLogger(__name__)


class AnalysisStateManager:
    """
    Manages analysis state tracking for user activity analysis.
    
    This class provides methods for:
    - Tracking analysis timestamps for incremental processing
    - Recording and retrieving analysis scope data
    - Determining new content since last analysis
    - State validation and consistency checking
    - Recovery mechanisms for interrupted analysis
    
    Requirements implemented:
    - 7.1: Record analysis start and completion timestamps
    - 7.2: Track analysis scope for subsequent runs
    - 7.3: Filter for new content only using timestamps
    - 7.4: Validate analysis state consistency
    - 7.5: Handle failed analysis cleanup
    """

    def __init__(self, db_client):
        """
        Initialize the analysis state manager.
        
        Args:
            db_client: Database client for state operations
        """
        self.db_client = db_client

    async def get_last_analysis_timestamp(self, user_id: UUID) -> Optional[datetime]:
        """
        Get the timestamp of the last completed analysis for a user.
        
        Args:
            user_id: User ID to get timestamp for
            
        Returns:
            Last analysis timestamp or None if never analyzed
            
        Requirements: 7.1, 7.3
        """
        query = """
            SELECT last_analysis_at
            FROM user_analysis_tracking
            WHERE user_id = :user_id
        """
        
        try:
            results = await self.db_client.execute_query_async(query, {"user_id": str(user_id)})
            
            if results and results[0]['last_analysis_at']:
                timestamp = results[0]['last_analysis_at']
                # Ensure timezone awareness
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                return timestamp
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting last analysis timestamp for user {user_id}: {e}")
            raise

    async def record_analysis_start(self, user_id: UUID) -> None:
        """
        Record the start of analysis for a user.
        
        This creates or updates the tracking record to indicate analysis has begun
        but does not update the last_analysis_at timestamp until completion.
        
        Args:
            user_id: User ID starting analysis
            
        Requirements: 7.1, 7.5
        """
        query = """
            INSERT INTO user_analysis_tracking (user_id, created_at, updated_at)
            VALUES (:user_id, NOW(), NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET updated_at = NOW()
        """
        
        try:
            await self.db_client.execute_update_async(query, {"user_id": str(user_id)})
            logger.debug(f"Recorded analysis start for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording analysis start for user {user_id}: {e}")
            raise

    async def record_analysis_completion(
        self,
        user_id: UUID,
        analysis_timestamp: datetime,
        analysis_scope: Dict[str, Any],
        last_post_id: Optional[UUID] = None,
        last_message_id: Optional[UUID] = None
    ) -> None:
        """
        Record successful completion of analysis for a user.
        
        Args:
            user_id: User ID completing analysis
            analysis_timestamp: When the analysis was completed
            analysis_scope: Detailed scope of what was analyzed
            last_post_id: ID of the last post analyzed (for incremental processing)
            last_message_id: ID of the last message analyzed (for incremental processing)
            
        Requirements: 7.1, 7.2, 7.3
        """
        # Ensure timezone awareness
        if analysis_timestamp.tzinfo is None:
            analysis_timestamp = analysis_timestamp.replace(tzinfo=timezone.utc)
        
        # Validate analysis scope structure
        validation_result = self._validate_analysis_scope(analysis_scope)
        if not validation_result['is_valid']:
            raise ValueError(f"Invalid analysis scope: {validation_result['issues']}")
        
        query = """
            INSERT INTO user_analysis_tracking (
                user_id, 
                last_analysis_at, 
                last_analyzed_post_id, 
                last_analyzed_message_id, 
                analysis_scope,
                created_at,
                updated_at
            )
            VALUES (:user_id, :analysis_timestamp, :last_post_id, :last_message_id, :analysis_scope, NOW(), NOW())
            ON CONFLICT (user_id) 
            DO UPDATE SET
                last_analysis_at = EXCLUDED.last_analysis_at,
                last_analyzed_post_id = EXCLUDED.last_analyzed_post_id,
                last_analyzed_message_id = EXCLUDED.last_analyzed_message_id,
                analysis_scope = EXCLUDED.analysis_scope,
                updated_at = EXCLUDED.updated_at
        """
        
        params = {
            "user_id": str(user_id),
            "analysis_timestamp": analysis_timestamp,
            "last_post_id": str(last_post_id) if last_post_id else None,
            "last_message_id": str(last_message_id) if last_message_id else None,
            "analysis_scope": json.dumps(analysis_scope)
        }
        
        try:
            await self.db_client.execute_update_async(query, params)
            logger.info(f"Recorded analysis completion for user {user_id} at {analysis_timestamp}")
            
        except Exception as e:
            logger.error(f"Error recording analysis completion for user {user_id}: {e}")
            raise

    async def get_analysis_scope(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the analysis scope from the last completed analysis.
        
        Args:
            user_id: User ID to get scope for
            
        Returns:
            Analysis scope dictionary or None if no previous analysis
            
        Requirements: 7.2, 7.3
        """
        query = """
            SELECT analysis_scope
            FROM user_analysis_tracking
            WHERE user_id = :user_id AND last_analysis_at IS NOT NULL
        """
        
        try:
            results = await self.db_client.execute_query_async(query, {"user_id": str(user_id)})
            
            if results and results[0]['analysis_scope']:
                return results[0]['analysis_scope']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis scope for user {user_id}: {e}")
            raise

    async def get_new_content_since_analysis(
        self, 
        user_id: UUID
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get new content (posts and messages) created since last analysis.
        
        Args:
            user_id: User ID to get new content for
            
        Returns:
            Dictionary with 'posts' and 'messages' lists containing new content
            
        Requirements: 7.3, 1.2, 2.1, 2.2
        """
        last_analysis = await self.get_last_analysis_timestamp(user_id)
        
        content = {
            'posts': [],
            'messages': []
        }
        
        try:
            # Get new posts since last analysis
            posts_query = """
                SELECT 
                    id,
                    content,
                    status,
                    user_feedback,
                    created_at,
                    updated_at
                FROM posts
                WHERE user_id = :user_id
                AND (
                    (status = 'scheduled' OR status = 'posted') OR 
                    (status = 'dismissed' OR user_feedback = 'negative')
                )
            """
            
            posts_params = {"user_id": str(user_id)}
            
            if last_analysis:
                posts_query += " AND created_at > :last_analysis"
                posts_params["last_analysis"] = last_analysis
            
            posts_query += " ORDER BY created_at DESC"
            
            posts_result = await self.db_client.execute_query_async(posts_query, posts_params)
            
            for row in posts_result:
                content['posts'].append({
                    'id': UUID(row['id']),
                    'content': row['content'],
                    'status': row['status'],
                    'user_feedback': row['user_feedback'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            # Get new messages since last analysis (excluding first messages from idea bank conversations)
            messages_query = """
                WITH ranked_messages AS (
                    SELECT 
                        m.id,
                        m.content,
                        m.created_at,
                        c.idea_bank_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY m.conversation_id 
                            ORDER BY m.created_at
                        ) as message_rank
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = :user_id AND m.role = 'user'
            """
            
            messages_params = {"user_id": str(user_id)}
            
            if last_analysis:
                messages_query += " AND c.created_at > :last_analysis AND m.created_at > :last_analysis"
                messages_params["last_analysis"] = last_analysis
            
            messages_query += """
                )
                SELECT 
                    id,
                    content,
                    created_at
                FROM ranked_messages
                WHERE NOT (idea_bank_id IS NOT NULL AND message_rank = 1)
                ORDER BY created_at DESC
            """
            
            messages_result = await self.db_client.execute_query_async(messages_query, messages_params)
            
            for row in messages_result:
                content['messages'].append({
                    'id': UUID(row['id']),
                    'content': row['content'],
                    'created_at': row['created_at']
                })
            
            logger.debug(
                f"Found {len(content['posts'])} new posts and {len(content['messages'])} "
                f"new messages for user {user_id} since {last_analysis}"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Error getting new content for user {user_id}: {e}")
            raise

    async def validate_analysis_state(self, user_id: UUID) -> Dict[str, Any]:
        """
        Validate the consistency of analysis state for a user.
        
        Checks for:
        - Consistent timestamps
        - Valid analysis scope structure
        - Reasonable content counts
        - No orphaned tracking records
        
        Args:
            user_id: User ID to validate state for
            
        Returns:
            Dictionary with validation results and any issues found
            
        Requirements: 7.4
        """
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'user_id': str(user_id)
        }
        
        try:
            # Get tracking record
            tracking_query = """
                SELECT 
                    last_analysis_at,
                    last_analyzed_post_id,
                    last_analyzed_message_id,
                    analysis_scope,
                    created_at,
                    updated_at
                FROM user_analysis_tracking
                WHERE user_id = :user_id
            """
            
            tracking_results = await self.db_client.execute_query_async(tracking_query, {"user_id": str(user_id)})
            tracking_result = tracking_results[0] if tracking_results else None
            
            if not tracking_result:
                validation_result['warnings'].append("No tracking record found for user")
                return validation_result
            
            # Validate timestamps
            created_at = tracking_result['created_at']
            updated_at = tracking_result['updated_at']
            last_analysis_at = tracking_result['last_analysis_at']
            
            if updated_at < created_at:
                validation_result['is_valid'] = False
                validation_result['issues'].append("Updated timestamp is before created timestamp")
            
            if last_analysis_at and last_analysis_at < created_at:
                validation_result['is_valid'] = False
                validation_result['issues'].append("Last analysis timestamp is before record creation")
            
            # Validate analysis scope if analysis has been completed
            if last_analysis_at and tracking_result['analysis_scope']:
                try:
                    scope_validation = self._validate_analysis_scope(tracking_result['analysis_scope'])
                    if not scope_validation['is_valid']:
                        validation_result['is_valid'] = False
                        validation_result['issues'].extend(scope_validation['issues'])
                except Exception as e:
                    validation_result['is_valid'] = False
                    validation_result['issues'].append(f"Invalid analysis scope format: {e}")
            
            # Check for orphaned post/message IDs
            if tracking_result['last_analyzed_post_id']:
                post_exists_query = "SELECT 1 FROM posts WHERE id = :post_id AND user_id = :user_id"
                post_exists_results = await self.db_client.execute_query_async(
                    post_exists_query, 
                    {"post_id": tracking_result['last_analyzed_post_id'], "user_id": str(user_id)}
                )
                post_exists = post_exists_results[0] if post_exists_results else None
                if not post_exists:
                    validation_result['warnings'].append("Last analyzed post ID references non-existent post")
            
            if tracking_result['last_analyzed_message_id']:
                message_exists_query = """
                    SELECT 1 FROM messages m 
                    JOIN conversations c ON m.conversation_id = c.id 
                    WHERE m.id = :message_id AND c.user_id = :user_id
                """
                message_exists_results = await self.db_client.execute_query_async(
                    message_exists_query,
                    {"message_id": tracking_result['last_analyzed_message_id'], "user_id": str(user_id)}
                )
                message_exists = message_exists_results[0] if message_exists_results else None
                if not message_exists:
                    validation_result['warnings'].append("Last analyzed message ID references non-existent message")
            
            # Validate content counts against actual database
            if last_analysis_at and tracking_result['analysis_scope']:
                await self._validate_content_counts(user_id, tracking_result['analysis_scope'], validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating analysis state for user {user_id}: {e}")
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Validation error: {e}")
            return validation_result

    async def cleanup_failed_analysis(self, user_id: UUID) -> None:
        """
        Clean up state after a failed analysis attempt.
        
        This method:
        - Does NOT update last_analysis_at (preserving last successful analysis)
        - Updates the updated_at timestamp to indicate activity
        - Logs the cleanup for monitoring
        
        Args:
            user_id: User ID to clean up failed analysis for
            
        Requirements: 7.5, 1.4
        """
        query = """
            UPDATE user_analysis_tracking
            SET updated_at = NOW()
            WHERE user_id = :user_id
        """
        
        try:
            rows_affected = await self.db_client.execute_update_async(query, {"user_id": str(user_id)})
            
            if rows_affected > 0:
                logger.info(f"Cleaned up failed analysis state for user {user_id}")
            else:
                logger.warning(f"No tracking record found to clean up for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up failed analysis for user {user_id}: {e}")
            raise

    async def get_users_needing_analysis(
        self, 
        post_threshold: int = 5,
        message_threshold: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get users who need analysis based on activity thresholds.
        
        Args:
            post_threshold: Minimum posts needed to trigger analysis
            message_threshold: Minimum messages needed to trigger analysis
            
        Returns:
            List of user data dictionaries for users needing analysis
            
        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        # Complex query to find users with sufficient activity since last analysis
        query = """
            WITH user_activity AS (
                SELECT 
                    u.id as user_id,
                    u.email,
                    uat.last_analysis_at,
                    
                    -- Count posts since last analysis
                    COALESCE((
                        SELECT COUNT(*)
                        FROM posts p
                                WHERE p.user_id = u.id
                        AND (p.status = 'scheduled' OR p.status = 'posted' OR p.status = 'dismissed' OR p.user_feedback = 'negative')
                        AND (uat.last_analysis_at IS NULL OR p.created_at > uat.last_analysis_at)
                    ), 0) as post_count,
                    
                    -- Count messages since last analysis (excluding first messages from idea bank conversations)
                    COALESCE((
                        WITH ranked_messages AS (
                            SELECT 
                                m.id,
                                c.idea_bank_id,
                                ROW_NUMBER() OVER (PARTITION BY m.conversation_id ORDER BY m.created_at) as message_rank
                            FROM messages m
                            JOIN conversations c ON m.conversation_id = c.id
                            WHERE c.user_id = u.id 
                            AND m.role = 'user'
                            AND (uat.last_analysis_at IS NULL OR (c.created_at > uat.last_analysis_at AND m.created_at > uat.last_analysis_at))
                        )
                        SELECT COUNT(*)
                        FROM ranked_messages
                        WHERE NOT (idea_bank_id IS NOT NULL AND message_rank = 1)
                    ), 0) as message_count
                    
                FROM users u
                LEFT JOIN user_analysis_tracking uat ON u.id = uat.user_id
                WHERE u.is_active = true AND u.deleted_at IS NULL
            )
            SELECT 
                user_id,
                email,
                last_analysis_at,
                post_count,
                message_count
            FROM user_activity
            WHERE post_count >= :post_threshold OR message_count >= :message_threshold
            ORDER BY 
                CASE WHEN last_analysis_at IS NULL THEN 0 ELSE 1 END,  -- Prioritize never-analyzed users
                last_analysis_at ASC NULLS FIRST,  -- Then by oldest analysis
                (post_count + message_count) DESC  -- Then by activity level
        """
        
        try:
            results = await self.db_client.execute_query_async(query, {
                "post_threshold": post_threshold, 
                "message_threshold": message_threshold
            })
            
            users_needing_analysis = []
            for row in results:
                users_needing_analysis.append({
                    'user_id': UUID(row['user_id']),
                    'email': row['email'],
                    'last_analysis_at': row['last_analysis_at'],
                    'post_count': row['post_count'],
                    'message_count': row['message_count'],
                    'needs_analysis': True
                })
            
            logger.info(f"Found {len(users_needing_analysis)} users needing analysis")
            return users_needing_analysis
            
        except Exception as e:
            logger.error(f"Error getting users needing analysis: {e}")
            raise

    async def get_analysis_progress_summary(self) -> Dict[str, Any]:
        """
        Get a summary of analysis progress across all users.
        
        Returns:
            Dictionary with analysis progress statistics
            
        Requirements: 8.1, 8.2
        """
        try:
            summary_query = """
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(uat.user_id) as users_with_tracking,
                    COUNT(uat.last_analysis_at) as users_analyzed,
                    COUNT(CASE WHEN uat.last_analysis_at IS NULL THEN 1 END) as users_never_analyzed,
                    AVG(EXTRACT(EPOCH FROM (NOW() - uat.last_analysis_at))/3600) as avg_hours_since_analysis,
                    MIN(uat.last_analysis_at) as oldest_analysis,
                    MAX(uat.last_analysis_at) as newest_analysis
                FROM users u
                LEFT JOIN user_analysis_tracking uat ON u.id = uat.user_id
                WHERE u.is_active = true AND u.deleted_at IS NULL
            """
            
            results = await self.db_client.execute_query_async(summary_query)
            result = results[0] if results else None
            
            if not result:
                return {
                    'total_users': 0,
                    'users_with_tracking': 0,
                    'users_analyzed': 0,
                    'users_never_analyzed': 0,
                    'avg_hours_since_analysis': 0,
                    'oldest_analysis': None,
                    'newest_analysis': None
                }
            
            return {
                'total_users': result['total_users'],
                'users_with_tracking': result['users_with_tracking'],
                'users_analyzed': result['users_analyzed'],
                'users_never_analyzed': result['users_never_analyzed'],
                'avg_hours_since_analysis': round(result['avg_hours_since_analysis'] or 0, 2),
                'oldest_analysis': result['oldest_analysis'],
                'newest_analysis': result['newest_analysis']
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis progress summary: {e}")
            raise

    def _validate_analysis_scope(self, analysis_scope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the structure and content of an analysis scope dictionary.
        
        Args:
            analysis_scope: Analysis scope to validate
            
        Returns:
            Dictionary with validation results
            
        Requirements: 7.4
        """
        validation_result = {
            'is_valid': True,
            'issues': []
        }
        
        required_keys = ['posts_analyzed', 'messages_analyzed', 'analysis_types_performed']
        
        # Check required top-level keys
        for key in required_keys:
            if key not in analysis_scope:
                validation_result['is_valid'] = False
                validation_result['issues'].append(f"Missing required key: {key}")
        
        # Validate posts_analyzed structure
        if 'posts_analyzed' in analysis_scope:
            posts_data = analysis_scope['posts_analyzed']
            if not isinstance(posts_data, dict):
                validation_result['is_valid'] = False
                validation_result['issues'].append("posts_analyzed must be a dictionary")
            else:
                required_post_keys = ['scheduled_count', 'dismissed_count']
                for key in required_post_keys:
                    if key not in posts_data:
                        validation_result['is_valid'] = False
                        validation_result['issues'].append(f"Missing posts_analyzed key: {key}")
                    elif not isinstance(posts_data[key], int) or posts_data[key] < 0:
                        validation_result['is_valid'] = False
                        validation_result['issues'].append(f"posts_analyzed.{key} must be a non-negative integer")
        
        # Validate messages_analyzed structure
        if 'messages_analyzed' in analysis_scope:
            messages_data = analysis_scope['messages_analyzed']
            if not isinstance(messages_data, dict):
                validation_result['is_valid'] = False
                validation_result['issues'].append("messages_analyzed must be a dictionary")
            else:
                if 'total_count' not in messages_data:
                    validation_result['is_valid'] = False
                    validation_result['issues'].append("Missing messages_analyzed key: total_count")
                elif not isinstance(messages_data['total_count'], int) or messages_data['total_count'] < 0:
                    validation_result['is_valid'] = False
                    validation_result['issues'].append("messages_analyzed.total_count must be a non-negative integer")
        
        # Validate analysis_types_performed
        if 'analysis_types_performed' in analysis_scope:
            analysis_types = analysis_scope['analysis_types_performed']
            if not isinstance(analysis_types, list):
                validation_result['is_valid'] = False
                validation_result['issues'].append("analysis_types_performed must be a list")
            else:
                valid_types = ['writing_style', 'topics_of_interest', 'bio_update', 'negative_analysis']
                for analysis_type in analysis_types:
                    if analysis_type not in valid_types:
                        validation_result['issues'].append(f"Unknown analysis type: {analysis_type}")
        
        return validation_result

    async def _validate_content_counts(
        self, 
        user_id: UUID, 
        analysis_scope: Dict[str, Any], 
        validation_result: Dict[str, Any]
    ) -> None:
        """
        Validate that content counts in analysis scope match actual database counts.
        
        Args:
            user_id: User ID to validate counts for
            analysis_scope: Analysis scope with recorded counts
            validation_result: Validation result dictionary to update
            
        Requirements: 7.4
        """
        try:
            # Get actual post counts from database
            posts_query = """
                SELECT 
                    COUNT(CASE WHEN (status = 'scheduled' OR status = 'posted') THEN 1 END) as scheduled_count,
                    COUNT(CASE WHEN (status = 'dismissed' OR user_feedback = 'negative') THEN 1 END) as dismissed_count
                FROM posts
                WHERE user_id = :user_id
            """
            
            posts_results = await self.db_client.execute_query_async(posts_query, {"user_id": str(user_id)})
            posts_result = posts_results[0] if posts_results else None
            
            if posts_result and 'posts_analyzed' in analysis_scope:
                recorded_scheduled = analysis_scope['posts_analyzed'].get('scheduled_count', 0)
                recorded_dismissed = analysis_scope['posts_analyzed'].get('dismissed_count', 0)
                
                actual_scheduled = posts_result['scheduled_count']
                actual_dismissed = posts_result['dismissed_count']
                
                # Allow for some variance due to timing of analysis vs current state
                if recorded_scheduled > actual_scheduled:
                    validation_result['warnings'].append(
                        f"Recorded scheduled posts ({recorded_scheduled}) exceeds actual count ({actual_scheduled})"
                    )
                
                if recorded_dismissed > actual_dismissed:
                    validation_result['warnings'].append(
                        f"Recorded dismissed posts ({recorded_dismissed}) exceeds actual count ({actual_dismissed})"
                    )
            
            # Get actual message counts from database
            messages_query = """
                WITH ranked_messages AS (
                    SELECT 
                        m.id,
                        c.idea_bank_id,
                        ROW_NUMBER() OVER (PARTITION BY m.conversation_id ORDER BY m.created_at) as message_rank
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = :user_id AND m.role = 'user'
                )
                SELECT COUNT(*) as total_count
                FROM ranked_messages
                WHERE NOT (idea_bank_id IS NOT NULL AND message_rank = 1)
            """
            
            messages_results = await self.db_client.execute_query_async(messages_query, {"user_id": str(user_id)})
            messages_result = messages_results[0] if messages_results else None
            
            if messages_result and 'messages_analyzed' in analysis_scope:
                recorded_messages = analysis_scope['messages_analyzed'].get('total_count', 0)
                actual_messages = messages_result['total_count']
                
                if recorded_messages > actual_messages:
                    validation_result['warnings'].append(
                        f"Recorded message count ({recorded_messages}) exceeds actual count ({actual_messages})"
                    )
                    
        except Exception as e:
            validation_result['warnings'].append(f"Could not validate content counts: {e}")
 
   # Analysis Progress Tracking and Recovery Methods - Requirement 7.1, 7.2, 7.5

    async def record_analysis_progress(
        self,
        user_id: UUID,
        progress_data: Dict[str, Any]
    ) -> None:
        """
        Record progress during long-running analysis operations.
        
        This method updates the tracking record with progress information
        without updating the completion timestamp, allowing for recovery
        if the analysis is interrupted.
        
        Args:
            user_id: User ID for progress tracking
            progress_data: Dictionary containing progress information
            
        Requirements: 7.1, 7.2, 7.5
        """
        # Validate progress data structure
        required_keys = ['step', 'total_steps', 'current_operation']
        for key in required_keys:
            if key not in progress_data:
                raise ValueError(f"Missing required progress key: {key}")
        
        # Create extended analysis scope with progress info
        extended_scope = {
            "progress": progress_data,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "status": "in_progress"
        }
        
        query = """
            UPDATE user_analysis_tracking
            SET 
                analysis_scope = COALESCE(analysis_scope, '{}')::jsonb || :progress_scope::jsonb,
                updated_at = NOW()
            WHERE user_id = :user_id
        """
        
        try:
            await self.db_client.execute_update_async(query, {
                "user_id": str(user_id),
                "progress_scope": json.dumps(extended_scope)
            })
            
            logger.debug(f"Recorded analysis progress for user {user_id}: {progress_data['current_operation']}")
            
        except Exception as e:
            logger.error(f"Error recording analysis progress for user {user_id}: {e}")
            raise

    async def get_analysis_progress(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get current analysis progress for a user.
        
        Args:
            user_id: User ID to get progress for
            
        Returns:
            Progress data dictionary or None if no progress recorded
            
        Requirements: 7.2, 7.5
        """
        query = """
            SELECT analysis_scope
            FROM user_analysis_tracking
            WHERE user_id = :user_id
        """
        
        try:
            results = await self.db_client.execute_query_async(query, {"user_id": str(user_id)})
            
            if results and results[0]['analysis_scope']:
                analysis_scope = results[0]['analysis_scope']
                return analysis_scope.get('progress')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting analysis progress for user {user_id}: {e}")
            raise

    async def detect_interrupted_analysis(
        self, 
        timeout_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Detect users with interrupted analysis that need recovery.
        
        Identifies users who have progress recorded but no completion
        timestamp within the timeout period.
        
        Args:
            timeout_minutes: Minutes after which analysis is considered interrupted
            
        Returns:
            List of user data for interrupted analyses
            
        Requirements: 7.5, 1.4
        """
        timeout_threshold = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        
        query = """
            SELECT 
                user_id,
                analysis_scope,
                updated_at,
                last_analysis_at
            FROM user_analysis_tracking
            WHERE 
                analysis_scope IS NOT NULL
                AND analysis_scope->>'status' = 'in_progress'
                AND updated_at < :timeout_threshold
                AND (
                    last_analysis_at IS NULL 
                    OR last_analysis_at < updated_at
                )
        """
        
        try:
            results = await self.db_client.execute_query_async(query, {
                "timeout_threshold": timeout_threshold
            })
            
            interrupted_analyses = []
            for row in results:
                progress_data = row['analysis_scope'].get('progress', {}) if row['analysis_scope'] else {}
                
                interrupted_analyses.append({
                    'user_id': UUID(row['user_id']),
                    'last_updated': row['updated_at'],
                    'last_analysis_at': row['last_analysis_at'],
                    'progress': progress_data,
                    'minutes_since_update': (datetime.now(timezone.utc) - row['updated_at']).total_seconds() / 60
                })
            
            logger.info(f"Found {len(interrupted_analyses)} interrupted analyses")
            return interrupted_analyses
            
        except Exception as e:
            logger.error(f"Error detecting interrupted analyses: {e}")
            raise

    async def recover_interrupted_analysis(self, user_id: UUID) -> Dict[str, Any]:
        """
        Recover from an interrupted analysis by cleaning up progress state.
        
        This method:
        - Removes progress tracking from analysis scope
        - Preserves any completed analysis data
        - Logs the recovery for monitoring
        
        Args:
            user_id: User ID to recover analysis for
            
        Returns:
            Dictionary with recovery information
            
        Requirements: 7.5, 1.4
        """
        recovery_info = {
            'user_id': str(user_id),
            'recovery_timestamp': datetime.now(timezone.utc),
            'recovered': False,
            'previous_progress': None
        }
        
        try:
            # Get current state
            current_progress = await self.get_analysis_progress(user_id)
            if current_progress:
                recovery_info['previous_progress'] = current_progress
            
            # Clean up progress state while preserving completed analysis data
            query = """
                UPDATE user_analysis_tracking
                SET 
                    analysis_scope = CASE 
                        WHEN analysis_scope IS NOT NULL THEN
                            (analysis_scope - 'progress' - 'status')
                        ELSE NULL
                    END,
                    updated_at = NOW()
                WHERE user_id = :user_id
                AND analysis_scope->>'status' = 'in_progress'
            """
            
            rows_affected = await self.db_client.execute_update_async(query, {"user_id": str(user_id)})
            
            if rows_affected > 0:
                recovery_info['recovered'] = True
                logger.info(f"Recovered interrupted analysis for user {user_id}")
            else:
                logger.warning(f"No interrupted analysis found to recover for user {user_id}")
            
            return recovery_info
            
        except Exception as e:
            logger.error(f"Error recovering interrupted analysis for user {user_id}: {e}")
            recovery_info['error'] = str(e)
            raise

    async def cleanup_stale_progress(self, max_age_hours: int = 24) -> int:
        """
        Clean up stale progress records that are too old to be useful.
        
        Args:
            max_age_hours: Maximum age in hours before progress is considered stale
            
        Returns:
            Number of records cleaned up
            
        Requirements: 7.5
        """
        stale_threshold = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        query = """
            UPDATE user_analysis_tracking
            SET 
                analysis_scope = CASE 
                    WHEN analysis_scope IS NOT NULL THEN
                        (analysis_scope - 'progress' - 'status')
                    ELSE NULL
                END,
                updated_at = NOW()
            WHERE 
                analysis_scope->>'status' = 'in_progress'
                AND updated_at < :stale_threshold
        """
        
        try:
            rows_affected = await self.db_client.execute_update_async(query, {
                "stale_threshold": stale_threshold
            })
            
            if rows_affected > 0:
                logger.info(f"Cleaned up {rows_affected} stale progress records")
            
            return rows_affected
            
        except Exception as e:
            logger.error(f"Error cleaning up stale progress records: {e}")
            raise

    async def get_analysis_recovery_summary(self) -> Dict[str, Any]:
        """
        Get a summary of analysis recovery statistics.
        
        Returns:
            Dictionary with recovery statistics
            
        Requirements: 8.1, 8.2
        """
        try:
            # Get counts of different analysis states
            summary_query = """
                SELECT 
                    COUNT(*) as total_tracking_records,
                    COUNT(CASE WHEN analysis_scope->>'status' = 'in_progress' THEN 1 END) as in_progress_count,
                    COUNT(CASE WHEN last_analysis_at IS NOT NULL THEN 1 END) as completed_count,
                    COUNT(CASE WHEN analysis_scope->>'status' = 'in_progress' 
                               AND updated_at < NOW() - INTERVAL '1 hour' THEN 1 END) as potentially_stale_count,
                    AVG(EXTRACT(EPOCH FROM (NOW() - updated_at))/60) as avg_minutes_since_update
                FROM user_analysis_tracking
                WHERE analysis_scope IS NOT NULL
            """
            
            results = await self.db_client.execute_query_async(summary_query)
            result = results[0] if results else None
            
            if not result:
                return {
                    'total_tracking_records': 0,
                    'in_progress_count': 0,
                    'completed_count': 0,
                    'potentially_stale_count': 0,
                    'avg_minutes_since_update': 0
                }
            
            return {
                'total_tracking_records': result['total_tracking_records'],
                'in_progress_count': result['in_progress_count'],
                'completed_count': result['completed_count'],
                'potentially_stale_count': result['potentially_stale_count'],
                'avg_minutes_since_update': round(result['avg_minutes_since_update'] or 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting analysis recovery summary: {e}")
            raise

    async def batch_recover_interrupted_analyses(
        self, 
        timeout_minutes: int = 60,
        max_recoveries: int = 100
    ) -> Dict[str, Any]:
        """
        Batch recovery of multiple interrupted analyses.
        
        Args:
            timeout_minutes: Minutes after which analysis is considered interrupted
            max_recoveries: Maximum number of recoveries to perform in one batch
            
        Returns:
            Dictionary with batch recovery results
            
        Requirements: 7.5, 1.4
        """
        batch_results = {
            'total_detected': 0,
            'total_recovered': 0,
            'failed_recoveries': 0,
            'recovery_details': []
        }
        
        try:
            # Detect interrupted analyses
            interrupted_analyses = await self.detect_interrupted_analysis(timeout_minutes)
            batch_results['total_detected'] = len(interrupted_analyses)
            
            # Limit to max_recoveries
            analyses_to_recover = interrupted_analyses[:max_recoveries]
            
            # Recover each analysis
            for analysis_info in analyses_to_recover:
                try:
                    recovery_result = await self.recover_interrupted_analysis(analysis_info['user_id'])
                    
                    if recovery_result['recovered']:
                        batch_results['total_recovered'] += 1
                    
                    batch_results['recovery_details'].append({
                        'user_id': str(analysis_info['user_id']),
                        'recovered': recovery_result['recovered'],
                        'minutes_interrupted': analysis_info['minutes_since_update'],
                        'previous_progress': recovery_result.get('previous_progress')
                    })
                    
                except Exception as e:
                    batch_results['failed_recoveries'] += 1
                    batch_results['recovery_details'].append({
                        'user_id': str(analysis_info['user_id']),
                        'recovered': False,
                        'error': str(e)
                    })
                    logger.error(f"Failed to recover analysis for user {analysis_info['user_id']}: {e}")
            
            logger.info(
                f"Batch recovery completed: {batch_results['total_recovered']} recovered, "
                f"{batch_results['failed_recoveries']} failed out of {batch_results['total_detected']} detected"
            )
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Error in batch recovery: {e}")
            batch_results['error'] = str(e)
            raise
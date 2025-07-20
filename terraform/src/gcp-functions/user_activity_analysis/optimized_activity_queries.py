"""
Optimized database queries for activity metrics with performance monitoring.

This module provides efficient database queries for user activity analysis with:
- Proper indexing utilization
- Query performance monitoring and logging
- Batch processing capabilities for multiple users
- Connection pooling and resource management
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID
from contextlib import asynccontextmanager

# from shared.cloud_sql_client import CloudSQLClient

logger = logging.getLogger(__name__)


class OptimizedActivityQueries:
    """
    Optimized database query layer for user activity analysis.
    
    Provides high-performance queries with:
    - Index-optimized query patterns
    - Performance monitoring and logging
    - Batch processing for multiple users
    - Connection pooling and resource management
    
    Requirements implemented:
    - 1.2: Efficient querying for incremental analysis
    - 2.1, 2.2: Optimized post and message counting
    - 10.4: Proper indexing for performance
    """

    def __init__(self, db_client):
        """
        Initialize with database client.
        
        Args:
            db_client: Database client instance for operations
        """
        self.db_client = db_client
        self.query_performance_log = []

    @asynccontextmanager
    async def _monitor_query_performance(self, query_name: str, query: str, params: List = None):
        """
        Context manager for monitoring query performance.
        
        Args:
            query_name: Name of the query for logging
            query: SQL query string
            params: Query parameters
        """
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            # Log performance metrics
            performance_data = {
                'query_name': query_name,
                'execution_time_ms': round(execution_time * 1000, 2),
                'timestamp': datetime.now(),
                'query_length': len(query),
                'param_count': len(params) if params else 0
            }
            
            self.query_performance_log.append(performance_data)
            
            # Log slow queries (>100ms)
            if execution_time > 0.1:
                logger.warning(
                    f"Slow query detected: {query_name} took {execution_time:.3f}s"
                )
            else:
                logger.debug(
                    f"Query {query_name} completed in {execution_time:.3f}s"
                )

    async def get_optimized_post_counts(
        self, 
        user_id: UUID, 
        since_timestamp: Optional[datetime] = None
    ) -> Dict[str, int]:
        """
        Get post counts using optimized queries with proper indexing.
        
        Uses idx_posts_user_created_status index for efficient filtering.
        
        Args:
            user_id: User ID to count posts for
            since_timestamp: Only count posts created after this timestamp
            
        Returns:
            Dictionary with 'scheduled_count' and 'dismissed_count'
        """
        # Build optimized query using covering index
        base_conditions = ["user_id = %s"]
        params = [str(user_id)]
        
        if since_timestamp:
            base_conditions.append("created_at > %s")
            params.append(since_timestamp)
        
        base_where = " AND ".join(base_conditions)
        
        # Single query to get both counts using CASE statements for efficiency
        optimized_query = f"""
            SELECT 
                COUNT(CASE WHEN (status = 'scheduled' OR status = 'posted') THEN 1 END) as scheduled_count,
                COUNT(CASE WHEN (status = 'dismissed' OR user_feedback = 'negative') THEN 1 END) as dismissed_count
            FROM posts 
            WHERE {base_where}
        """
        
        async with self._monitor_query_performance("get_optimized_post_counts", optimized_query, params):
            result = await self.db_client.fetch_one(optimized_query, params)
        
        return {
            'scheduled_count': result['scheduled_count'] if result else 0,
            'dismissed_count': result['dismissed_count'] if result else 0
        }

    async def get_optimized_message_counts(
        self, 
        user_id: UUID, 
        since_timestamp: Optional[datetime] = None
    ) -> int:
        """
        Get message counts using optimized queries with idea bank exclusion.
        
        Uses idx_conversations_user_idea_created and idx_messages_conversation_created
        indexes for efficient filtering.
        
        Args:
            user_id: User ID to count messages for
            since_timestamp: Only count messages created after this timestamp
            
        Returns:
            Total count of messages (excluding first messages from idea bank conversations)
        """
        # Optimized query using JOINs and window functions
        conditions = ["c.user_id = %s", "m.role = 'user'"]
        params = [str(user_id)]
        
        if since_timestamp:
            conditions.extend([
                "c.created_at > %s",
                "m.created_at > %s"
            ])
            params.extend([since_timestamp, since_timestamp])
        
        where_clause = " AND ".join(conditions)
        
        # Use window function to identify first messages in idea bank conversations
        optimized_query = f"""
            WITH ranked_messages AS (
                SELECT 
                    m.id,
                    c.idea_bank_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY m.conversation_id 
                        ORDER BY m.created_at
                    ) as message_rank
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE {where_clause}
            )
            SELECT COUNT(*) as total_count
            FROM ranked_messages
            WHERE NOT (idea_bank_id IS NOT NULL AND message_rank = 1)
        """
        
        async with self._monitor_query_performance("get_optimized_message_counts", optimized_query, params):
            result = await self.db_client.fetch_one(optimized_query, params)
        
        return result['total_count'] if result else 0

    async def get_batch_user_activity_counts(
        self, 
        user_ids: List[UUID],
        since_timestamps: Optional[Dict[UUID, datetime]] = None
    ) -> Dict[UUID, Dict[str, int]]:
        """
        Get activity counts for multiple users in a single batch operation.
        
        Optimized for processing multiple users efficiently using batch queries.
        
        Args:
            user_ids: List of user IDs to process
            since_timestamps: Optional dict mapping user_id to their last analysis timestamp
            
        Returns:
            Dictionary mapping user_id to their activity counts
        """
        if not user_ids:
            return {}
        
        # Convert UUIDs to strings for database query
        user_id_strings = [str(uid) for uid in user_ids]
        
        # Build batch post counts query
        post_query_conditions = ["user_id = ANY(%s)"]
        post_params = [user_id_strings]
        
        # Add timestamp conditions if provided
        timestamp_conditions = []
        if since_timestamps:
            for user_id, timestamp in since_timestamps.items():
                if timestamp:
                    timestamp_conditions.append(
                        f"(user_id = '{user_id}' AND created_at > '{timestamp}')"
                    )
        
        if timestamp_conditions:
            post_query_conditions.append(f"({' OR '.join(timestamp_conditions)})")
        
        post_where = " AND ".join(post_query_conditions)
        
        # Batch query for post counts
        batch_post_query = f"""
            SELECT 
                user_id,
                COUNT(CASE WHEN (status = 'scheduled' OR status = 'posted') THEN 1 END) as scheduled_count,
                COUNT(CASE WHEN (status = 'dismissed' OR user_feedback = 'negative') THEN 1 END) as dismissed_count
            FROM posts 
            WHERE {post_where}
            GROUP BY user_id
        """
        
        async with self._monitor_query_performance("batch_post_counts", batch_post_query, post_params):
            post_results = await self.db_client.fetch_all(batch_post_query, post_params)
        
        # Build batch message counts query
        message_conditions = ["c.user_id = ANY(%s)", "m.role = 'user'"]
        message_params = [user_id_strings]
        
        # Add timestamp conditions for messages
        if since_timestamps:
            message_timestamp_conditions = []
            for user_id, timestamp in since_timestamps.items():
                if timestamp:
                    message_timestamp_conditions.append(
                        f"(c.user_id = '{user_id}' AND c.created_at > '{timestamp}' AND m.created_at > '{timestamp}')"
                    )
            
            if message_timestamp_conditions:
                message_conditions.append(f"({' OR '.join(message_timestamp_conditions)})")
        
        message_where = " AND ".join(message_conditions)
        
        # Batch query for message counts with idea bank exclusion
        batch_message_query = f"""
            WITH ranked_messages AS (
                SELECT 
                    c.user_id,
                    m.id,
                    c.idea_bank_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY m.conversation_id 
                        ORDER BY m.created_at
                    ) as message_rank
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE {message_where}
            )
            SELECT 
                user_id,
                COUNT(*) as message_count
            FROM ranked_messages
            WHERE NOT (idea_bank_id IS NOT NULL AND message_rank = 1)
            GROUP BY user_id
        """
        
        async with self._monitor_query_performance("batch_message_counts", batch_message_query, message_params):
            message_results = await self.db_client.fetch_all(batch_message_query, message_params)
        
        # Combine results
        activity_counts = {}
        
        # Initialize all users with zero counts
        for user_id in user_ids:
            activity_counts[user_id] = {
                'scheduled_posts': 0,
                'dismissed_posts': 0,
                'total_posts': 0,
                'messages': 0
            }
        
        # Update with post counts
        for row in post_results:
            user_id = UUID(row['user_id'])
            scheduled = row['scheduled_count']
            dismissed = row['dismissed_count']
            
            activity_counts[user_id].update({
                'scheduled_posts': scheduled,
                'dismissed_posts': dismissed,
                'total_posts': scheduled + dismissed
            })
        
        # Update with message counts
        for row in message_results:
            user_id = UUID(row['user_id'])
            activity_counts[user_id]['messages'] = row['message_count']
        
        return activity_counts

    async def get_users_analysis_tracking_batch(
        self, 
        user_ids: Optional[List[UUID]] = None
    ) -> Dict[UUID, Dict[str, Any]]:
        """
        Get analysis tracking data for multiple users efficiently.
        
        Args:
            user_ids: Optional list of specific user IDs to query. If None, gets all active users.
            
        Returns:
            Dictionary mapping user_id to their tracking data
        """
        conditions = ["u.is_active = true", "u.deleted_at IS NULL"]
        params = []
        
        if user_ids:
            user_id_strings = [str(uid) for uid in user_ids]
            conditions.append("u.id = ANY(%s)")
            params.append(user_id_strings)
        
        where_clause = " AND ".join(conditions)
        
        # Optimized query with LEFT JOIN to include users without tracking records
        tracking_query = f"""
            SELECT 
                u.id as user_id,
                u.email,
                uat.last_analysis_at,
                uat.analysis_scope,
                uat.created_at as tracking_created_at,
                uat.updated_at as tracking_updated_at
            FROM users u
            LEFT JOIN user_analysis_tracking uat ON u.id = uat.user_id
            WHERE {where_clause}
            ORDER BY u.id
        """
        
        async with self._monitor_query_performance("get_users_analysis_tracking_batch", tracking_query, params):
            results = await self.db_client.fetch_all(tracking_query, params)
        
        tracking_data = {}
        for row in results:
            user_id = UUID(row['user_id'])
            tracking_data[user_id] = {
                'email': row['email'],
                'last_analysis_at': row['last_analysis_at'],
                'analysis_scope': row['analysis_scope'],
                'tracking_created_at': row['tracking_created_at'],
                'tracking_updated_at': row['tracking_updated_at'],
                'has_tracking_record': row['last_analysis_at'] is not None
            }
        
        return tracking_data

    async def get_content_for_analysis_batch(
        self, 
        user_activity_data: Dict[UUID, Dict[str, Any]]
    ) -> Dict[UUID, Dict[str, List]]:
        """
        Get content (posts and messages) for analysis for multiple users.
        
        Args:
            user_activity_data: Dict mapping user_id to their activity data including timestamps
            
        Returns:
            Dictionary mapping user_id to their content data
        """
        if not user_activity_data:
            return {}
        
        content_data = {}
        
        # Get posts for all users in batch
        user_conditions = []
        for user_id, data in user_activity_data.items():
            since_timestamp = data.get('last_analysis_at')
            if since_timestamp:
                user_conditions.append(
                    f"(user_id = '{user_id}' AND created_at > '{since_timestamp}')"
                )
            else:
                user_conditions.append(f"user_id = '{user_id}'")
        
        if user_conditions:
            posts_query = f"""
                SELECT 
                    user_id,
                    id,
                    content,
                    status,
                    user_feedback,
                    created_at,
                    CASE 
                        WHEN (status = 'scheduled' OR status = 'posted') THEN 'scheduled'
                        WHEN (status = 'dismissed' OR user_feedback = 'negative') THEN 'dismissed'
                        ELSE 'other'
                    END as post_category
                FROM posts
                WHERE ({' OR '.join(user_conditions)})
                AND (
                    (status = 'scheduled' OR status = 'posted') OR 
                    (status = 'dismissed' OR user_feedback = 'negative')
                )
                ORDER BY user_id, created_at DESC
            """
            
            async with self._monitor_query_performance("get_content_posts_batch", posts_query):
                post_results = await self.db_client.fetch_all(posts_query)
            
            # Organize posts by user and category
            for user_id in user_activity_data.keys():
                content_data[user_id] = {
                    'scheduled_posts': [],
                    'dismissed_posts': [],
                    'messages': []
                }
            
            for row in post_results:
                user_id = UUID(row['user_id'])
                post_data = {
                    'id': row['id'],
                    'content': row['content'],
                    'status': row['status'],
                    'user_feedback': row['user_feedback'],
                    'created_at': row['created_at']
                }
                
                if row['post_category'] == 'scheduled':
                    content_data[user_id]['scheduled_posts'].append(post_data)
                elif row['post_category'] == 'dismissed':
                    content_data[user_id]['dismissed_posts'].append(post_data)
        
        # Get messages for all users in batch
        message_conditions = []
        for user_id, data in user_activity_data.items():
            since_timestamp = data.get('last_analysis_at')
            if since_timestamp:
                message_conditions.append(
                    f"(c.user_id = '{user_id}' AND c.created_at > '{since_timestamp}' AND m.created_at > '{since_timestamp}')"
                )
            else:
                message_conditions.append(f"c.user_id = '{user_id}'")
        
        if message_conditions:
            messages_query = f"""
                WITH ranked_messages AS (
                    SELECT 
                        c.user_id,
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
                    WHERE ({' OR '.join(message_conditions)})
                    AND m.role = 'user'
                )
                SELECT 
                    user_id,
                    id,
                    content,
                    created_at
                FROM ranked_messages
                WHERE NOT (idea_bank_id IS NOT NULL AND message_rank = 1)
                ORDER BY user_id, created_at DESC
            """
            
            async with self._monitor_query_performance("get_content_messages_batch", messages_query):
                message_results = await self.db_client.fetch_all(messages_query)
            
            # Add messages to content data
            for row in message_results:
                user_id = UUID(row['user_id'])
                if user_id in content_data:
                    message_data = {
                        'id': row['id'],
                        'content': row['content'],
                        'created_at': row['created_at']
                    }
                    content_data[user_id]['messages'].append(message_data)
        
        return content_data

    async def update_analysis_tracking_batch(
        self, 
        tracking_updates: List[Dict[str, Any]]
    ) -> None:
        """
        Update analysis tracking records for multiple users in batch.
        
        Args:
            tracking_updates: List of tracking update data for each user
        """
        if not tracking_updates:
            return
        
        # Use UPSERT (INSERT ... ON CONFLICT) for efficient batch updates
        upsert_query = """
            INSERT INTO user_analysis_tracking (
                user_id, 
                last_analysis_at, 
                last_analyzed_post_id, 
                last_analyzed_message_id, 
                analysis_scope,
                updated_at
            ) VALUES %s
            ON CONFLICT (user_id) 
            DO UPDATE SET
                last_analysis_at = EXCLUDED.last_analysis_at,
                last_analyzed_post_id = EXCLUDED.last_analyzed_post_id,
                last_analyzed_message_id = EXCLUDED.last_analyzed_message_id,
                analysis_scope = EXCLUDED.analysis_scope,
                updated_at = EXCLUDED.updated_at
        """
        
        # Prepare batch values
        batch_values = []
        for update in tracking_updates:
            batch_values.append((
                str(update['user_id']),
                update['analysis_timestamp'],
                str(update.get('last_post_id')) if update.get('last_post_id') else None,
                str(update.get('last_message_id')) if update.get('last_message_id') else None,
                update['analysis_scope'],
                datetime.now()
            ))
        
        async with self._monitor_query_performance("update_analysis_tracking_batch", upsert_query):
            await self.db_client.execute_batch(upsert_query, batch_values)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get query performance metrics for monitoring.
        
        Returns:
            Dictionary with performance statistics
        """
        if not self.query_performance_log:
            return {
                'total_queries': 0,
                'average_execution_time_ms': 0,
                'slow_queries_count': 0,
                'queries_by_type': {}
            }
        
        total_queries = len(self.query_performance_log)
        total_time = sum(q['execution_time_ms'] for q in self.query_performance_log)
        slow_queries = [q for q in self.query_performance_log if q['execution_time_ms'] > 100]
        
        queries_by_type = {}
        for query in self.query_performance_log:
            query_name = query['query_name']
            if query_name not in queries_by_type:
                queries_by_type[query_name] = {
                    'count': 0,
                    'total_time_ms': 0,
                    'avg_time_ms': 0
                }
            
            queries_by_type[query_name]['count'] += 1
            queries_by_type[query_name]['total_time_ms'] += query['execution_time_ms']
        
        # Calculate averages
        for query_type in queries_by_type.values():
            query_type['avg_time_ms'] = round(
                query_type['total_time_ms'] / query_type['count'], 2
            )
        
        return {
            'total_queries': total_queries,
            'average_execution_time_ms': round(total_time / total_queries, 2),
            'slow_queries_count': len(slow_queries),
            'queries_by_type': queries_by_type,
            'recent_slow_queries': [
                {
                    'query_name': q['query_name'],
                    'execution_time_ms': q['execution_time_ms'],
                    'timestamp': q['timestamp'].isoformat()
                }
                for q in slow_queries[-5:]  # Last 5 slow queries
            ]
        }

    def clear_performance_log(self) -> None:
        """Clear the performance log to free memory."""
        self.query_performance_log.clear()

    async def validate_indexes(self) -> Dict[str, bool]:
        """
        Validate that required indexes exist for optimal performance.
        
        Returns:
            Dictionary mapping index name to existence status
        """
        required_indexes = [
            'idx_posts_user_created_status',
            'idx_messages_conversation_created',
            'idx_conversations_user_idea_created',
            'idx_user_analysis_tracking_user_id',
            'idx_user_analysis_tracking_last_analysis'
        ]
        
        index_check_query = """
            SELECT indexname 
            FROM pg_indexes 
            WHERE indexname = ANY(%s)
        """
        
        async with self._monitor_query_performance("validate_indexes", index_check_query, [required_indexes]):
            existing_indexes = await self.db_client.fetch_all(index_check_query, [required_indexes])
        
        existing_index_names = {row['indexname'] for row in existing_indexes}
        
        return {
            index_name: index_name in existing_index_names
            for index_name in required_indexes
        }
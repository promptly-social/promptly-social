"""
Analysis-specific database client for user activity analysis.

This module provides specialized database operations for the user activity analysis
function, including transaction handling, connection management, and analysis-specific
queries with proper error handling and cleanup.

Requirements implemented:
- 10.1, 10.2, 10.3: Proper connection management and cleanup
- Database transaction handling for analysis operations
- Analysis-specific database operations
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from uuid import UUID
from contextlib import asynccontextmanager

from shared.cloud_sql_client import CloudSQLClient

logger = logging.getLogger(__name__)


class AnalysisDatabaseClient:
    """
    Specialized database client for user activity analysis operations.
    
    This client extends the base CloudSQLClient with analysis-specific operations,
    transaction management, and proper connection cleanup for the analysis function.
    
    Requirements implemented:
    - 10.1: Proper connection management and cleanup
    - 10.2: Database transaction handling for analysis operations
    - 10.3: Analysis-specific database operations
    """
    
    def __init__(self, base_client: CloudSQLClient):
        """
        Initialize the analysis database client.
        
        Args:
            base_client: Base CloudSQLClient instance
        """
        self.base_client = base_client
        self._connection_pool_stats = {
            'active_connections': 0,
            'total_queries': 0,
            'failed_queries': 0,
            'transaction_count': 0,
            'rollback_count': 0
        }
    
    async def execute_query_async(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a query with connection tracking and error handling.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of result dictionaries
            
        Raises:
            Exception: If query execution fails
        """
        self._connection_pool_stats['total_queries'] += 1
        
        try:
            self._connection_pool_stats['active_connections'] += 1
            result = await self.base_client.execute_query_async(query, params)
            logger.debug(f"Query executed successfully: {len(result)} rows returned")
            return result
            
        except Exception as e:
            self._connection_pool_stats['failed_queries'] += 1
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Query params: {params}")
            raise
            
        finally:
            self._connection_pool_stats['active_connections'] -= 1
    
    async def execute_update_async(self, query: str, params: Dict[str, Any] = None) -> int:
        """
        Execute an update query with connection tracking and error handling.
        
        Args:
            query: SQL update query to execute
            params: Query parameters
            
        Returns:
            Number of affected rows
            
        Raises:
            Exception: If query execution fails
        """
        self._connection_pool_stats['total_queries'] += 1
        
        try:
            self._connection_pool_stats['active_connections'] += 1
            result = await self.base_client.execute_update_async(query, params)
            logger.debug(f"Update executed successfully: {result} rows affected")
            return result
            
        except Exception as e:
            self._connection_pool_stats['failed_queries'] += 1
            logger.error(f"Update execution failed: {e}")
            logger.debug(f"Failed query: {query}")
            logger.debug(f"Query params: {params}")
            raise
            
        finally:
            self._connection_pool_stats['active_connections'] -= 1
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions with proper error handling.
        
        Provides automatic transaction management with commit/rollback handling
        and connection cleanup.
        
        Usage:
            async with client.transaction():
                await client.execute_update_async(query1, params1)
                await client.execute_update_async(query2, params2)
                # Automatically commits on success, rolls back on exception
        """
        self._connection_pool_stats['transaction_count'] += 1
        
        async with self.base_client.get_async_session() as session:
            try:
                logger.debug("Starting database transaction")
                yield session
                logger.debug("Transaction completed successfully")
                
            except Exception as e:
                self._connection_pool_stats['rollback_count'] += 1
                logger.error(f"Transaction failed, rolling back: {e}")
                raise
    
    async def batch_execute_updates(self, queries_and_params: List[Tuple[str, Dict[str, Any]]]) -> List[int]:
        """
        Execute multiple update queries in a single transaction.
        
        Args:
            queries_and_params: List of (query, params) tuples
            
        Returns:
            List of affected row counts for each query
            
        Raises:
            Exception: If any query in the batch fails
        """
        results = []
        
        async with self.transaction():
            for query, params in queries_and_params:
                result = await self.execute_update_async(query, params)
                results.append(result)
        
        logger.info(f"Batch executed {len(queries_and_params)} queries successfully")
        return results
    
    async def get_user_analysis_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive analysis summary for a user.
        
        Args:
            user_id: User ID to get summary for
            
        Returns:
            Dictionary with user analysis summary
        """
        query = """
            SELECT 
                u.id as user_id,
                u.email,
                u.bio,
                u.created_at as user_created_at,
                up.writing_style_analysis,
                up.negative_analysis,
                up.topics_of_interest,
                uat.last_analysis_at,
                uat.analysis_scope,
                (
                    SELECT COUNT(*) 
                    FROM posts p 
                    WHERE p.user_id = u.id 
                    AND p.status IN ('scheduled', 'posted')
                    AND p.created_at > COALESCE(uat.last_analysis_at, '1970-01-01'::timestamp)
                ) as new_posts_count,
                (
                    SELECT COUNT(*) 
                    FROM posts p 
                    WHERE p.user_id = u.id 
                    AND p.status = 'dismissed'
                    AND p.created_at > COALESCE(uat.last_analysis_at, '1970-01-01'::timestamp)
                ) as new_dismissed_posts_count,
                (
                    SELECT COUNT(DISTINCT m.id)
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = u.id
                    AND m.created_at > COALESCE(uat.last_analysis_at, '1970-01-01'::timestamp)
                    AND NOT (c.idea_bank_id IS NOT NULL AND m.id = (
                        SELECT MIN(m2.id) FROM messages m2 WHERE m2.conversation_id = c.id
                    ))
                ) as new_messages_count
            FROM users u
            LEFT JOIN user_preferences up ON u.id = up.user_id
            LEFT JOIN user_analysis_tracking uat ON u.id = uat.user_id
            WHERE u.id = :user_id
            AND u.is_active = true
            AND u.deleted_at IS NULL
        """
        
        results = await self.execute_query_async(query, {"user_id": str(user_id)})
        
        if not results:
            raise ValueError(f"User {user_id} not found or inactive")
        
        summary = results[0]
        
        # Parse JSON fields
        if summary.get('analysis_scope'):
            try:
                summary['analysis_scope'] = json.loads(summary['analysis_scope'])
            except (json.JSONDecodeError, TypeError):
                summary['analysis_scope'] = None
        
        if summary.get('topics_of_interest'):
            try:
                summary['topics_of_interest'] = json.loads(summary['topics_of_interest']) if isinstance(summary['topics_of_interest'], str) else summary['topics_of_interest']
            except (json.JSONDecodeError, TypeError):
                summary['topics_of_interest'] = []
        
        return summary
    
    async def update_user_analysis_results(
        self,
        user_id: UUID,
        analysis_results: Dict[str, Any],
        analysis_scope: Dict[str, Any]
    ) -> None:
        """
        Update user analysis results in a single transaction.
        
        Args:
            user_id: User ID to update
            analysis_results: Analysis results by type
            analysis_scope: Analysis scope information
        """
        queries_and_params = []
        
        # Update writing style analysis if present
        if 'writing_style' in analysis_results:
            query = """
                INSERT INTO user_preferences (user_id, writing_style_analysis, updated_at)
                VALUES (:user_id, :writing_style_analysis, NOW())
                ON CONFLICT (user_id)
                DO UPDATE SET
                    writing_style_analysis = EXCLUDED.writing_style_analysis,
                    updated_at = EXCLUDED.updated_at
            """
            queries_and_params.append((query, {
                "user_id": str(user_id),
                "writing_style_analysis": analysis_results['writing_style']
            }))
        
        # Update user bio if present
        if 'bio_update' in analysis_results:
            query = """
                UPDATE users
                SET bio = :bio, updated_at = NOW()
                WHERE id = :user_id
            """
            queries_and_params.append((query, {
                "user_id": str(user_id),
                "bio": analysis_results['bio_update']
            }))
        
        # Update negative analysis if present
        if 'negative_analysis' in analysis_results:
            query = """
                INSERT INTO user_preferences (user_id, negative_analysis, updated_at)
                VALUES (:user_id, :negative_analysis, NOW())
                ON CONFLICT (user_id)
                DO UPDATE SET
                    negative_analysis = EXCLUDED.negative_analysis,
                    updated_at = EXCLUDED.updated_at
            """
            queries_and_params.append((query, {
                "user_id": str(user_id),
                "negative_analysis": analysis_results['negative_analysis']
            }))
        
        # Update analysis tracking
        tracking_query = """
            INSERT INTO user_analysis_tracking (
                user_id, 
                last_analysis_at, 
                analysis_scope,
                updated_at
            )
            VALUES (:user_id, NOW(), :analysis_scope, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                last_analysis_at = EXCLUDED.last_analysis_at,
                analysis_scope = EXCLUDED.analysis_scope,
                updated_at = EXCLUDED.updated_at
        """
        queries_and_params.append((tracking_query, {
            "user_id": str(user_id),
            "analysis_scope": json.dumps(analysis_scope)
        }))
        
        # Execute all updates in a single transaction
        await self.batch_execute_updates(queries_and_params)
        
        logger.info(f"Updated analysis results for user {user_id}: {list(analysis_results.keys())}")
    
    async def get_users_needing_analysis_batch(
        self,
        post_threshold: int,
        message_threshold: int,
        batch_size: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get a batch of users needing analysis with pagination.
        
        Args:
            post_threshold: Minimum posts to trigger analysis
            message_threshold: Minimum messages to trigger analysis
            batch_size: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of user data dictionaries
        """
        query = """
            WITH user_activity AS (
                SELECT 
                    u.id as user_id,
                    u.email,
                    COALESCE(uat.last_analysis_at, '1970-01-01'::timestamp) as last_analysis_at,
                    (
                        SELECT COUNT(*) 
                        FROM posts p 
                        WHERE p.user_id = u.id 
                        AND p.status IN ('scheduled', 'posted', 'dismissed')
                        AND p.created_at > COALESCE(uat.last_analysis_at, '1970-01-01'::timestamp)
                    ) as post_count,
                    (
                        SELECT COUNT(DISTINCT m.id)
                        FROM messages m
                        JOIN conversations c ON m.conversation_id = c.id
                        WHERE c.user_id = u.id
                        AND m.created_at > COALESCE(uat.last_analysis_at, '1970-01-01'::timestamp)
                        AND NOT (c.idea_bank_id IS NOT NULL AND m.id = (
                            SELECT MIN(m2.id) FROM messages m2 WHERE m2.conversation_id = c.id
                        ))
                    ) as message_count
                FROM users u
                LEFT JOIN user_analysis_tracking uat ON u.id = uat.user_id
                WHERE u.is_active = true 
                AND u.deleted_at IS NULL
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
                CASE 
                    WHEN last_analysis_at = '1970-01-01'::timestamp THEN 0
                    ELSE 1
                END,
                last_analysis_at ASC,
                (post_count + message_count) DESC
            LIMIT :batch_size OFFSET :offset
        """
        
        results = await self.execute_query_async(query, {
            "post_threshold": post_threshold,
            "message_threshold": message_threshold,
            "batch_size": batch_size,
            "offset": offset
        })
        
        logger.info(f"Retrieved {len(results)} users needing analysis (batch_size={batch_size}, offset={offset})")
        return results
    
    async def cleanup_stale_analysis_tracking(self, stale_hours: int = 24) -> int:
        """
        Clean up stale analysis tracking records.
        
        Args:
            stale_hours: Hours after which incomplete analysis is considered stale
            
        Returns:
            Number of records cleaned up
        """
        query = """
            DELETE FROM user_analysis_tracking
            WHERE last_analysis_at IS NULL
            AND created_at < NOW() - INTERVAL '%s hours'
        """ % stale_hours
        
        rows_affected = await self.execute_update_async(query)
        
        if rows_affected > 0:
            logger.info(f"Cleaned up {rows_affected} stale analysis tracking records")
        
        return rows_affected
    
    async def get_analysis_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for analysis operations.
        
        Returns:
            Dictionary with performance metrics
        """
        query = """
            SELECT 
                COUNT(*) as total_users,
                COUNT(CASE WHEN uat.last_analysis_at IS NOT NULL THEN 1 END) as analyzed_users,
                COUNT(CASE WHEN uat.last_analysis_at IS NULL THEN 1 END) as unanalyzed_users,
                AVG(EXTRACT(EPOCH FROM (NOW() - uat.last_analysis_at))) as avg_time_since_analysis,
                COUNT(CASE WHEN uat.last_analysis_at > NOW() - INTERVAL '24 hours' THEN 1 END) as analyzed_last_24h,
                COUNT(CASE WHEN uat.last_analysis_at > NOW() - INTERVAL '7 days' THEN 1 END) as analyzed_last_7d
            FROM users u
            LEFT JOIN user_analysis_tracking uat ON u.id = uat.user_id
            WHERE u.is_active = true AND u.deleted_at IS NULL
        """
        
        results = await self.execute_query_async(query)
        metrics = results[0] if results else {}
        
        # Add connection pool stats
        metrics.update({
            'connection_pool': self._connection_pool_stats.copy()
        })
        
        return metrics
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get current connection pool statistics.
        
        Returns:
            Dictionary with connection statistics
        """
        return self._connection_pool_stats.copy()
    
    def reset_connection_stats(self):
        """Reset connection pool statistics."""
        self._connection_pool_stats = {
            'active_connections': 0,
            'total_queries': 0,
            'failed_queries': 0,
            'transaction_count': 0,
            'rollback_count': 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.
        
        Returns:
            Dictionary with health check results
        """
        try:
            start_time = datetime.now(timezone.utc)
            
            # Simple connectivity test
            result = await self.execute_query_async("SELECT 1 as test, NOW() as server_time")
            
            end_time = datetime.now(timezone.utc)
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            if result and result[0]['test'] == 1:
                return {
                    'status': 'healthy',
                    'response_time_ms': response_time_ms,
                    'server_time': result[0]['server_time'],
                    'connection_stats': self.get_connection_stats()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'Unexpected query result',
                    'response_time_ms': response_time_ms
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connection_stats': self.get_connection_stats()
            }
    
    def close(self):
        """Close the database client and clean up connections."""
        try:
            self.base_client.close()
            logger.info("Analysis database client closed successfully")
        except Exception as e:
            logger.error(f"Error closing analysis database client: {e}")


def create_analysis_database_client() -> AnalysisDatabaseClient:
    """
    Create an analysis database client instance.
    
    Returns:
        AnalysisDatabaseClient instance
    """
    from shared.cloud_sql_client import get_cloud_sql_client
    
    base_client = get_cloud_sql_client()
    return AnalysisDatabaseClient(base_client)
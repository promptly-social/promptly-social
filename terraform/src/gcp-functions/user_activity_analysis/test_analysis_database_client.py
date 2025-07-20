"""
Tests for the analysis database client.

This module tests database operations, transaction handling, connection management,
and analysis-specific queries with proper error handling and cleanup.

Requirements tested:
- 10.1, 10.2, 10.3: Proper connection management and cleanup
- Database transaction handling for analysis operations
- Analysis-specific database operations
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from analysis_database_client import AnalysisDatabaseClient, create_analysis_database_client
from contextlib import asynccontextmanager


class TestAnalysisDatabaseClient:
    """Test analysis database client functionality."""
    
    @pytest.fixture
    def mock_base_client(self):
        """Create a mock base CloudSQL client."""
        mock_client = Mock()
        mock_client.execute_query_async = AsyncMock()
        mock_client.execute_update_async = AsyncMock()
        mock_client.get_async_session = AsyncMock()
        mock_client.close = Mock()
        return mock_client
    
    @pytest.fixture
    def analysis_client(self, mock_base_client):
        """Create an analysis database client with mocked base client."""
        return AnalysisDatabaseClient(mock_base_client)
    
    def test_initialization(self, mock_base_client):
        """Test client initialization."""
        client = AnalysisDatabaseClient(mock_base_client)
        
        assert client.base_client == mock_base_client
        assert client._connection_pool_stats['active_connections'] == 0
        assert client._connection_pool_stats['total_queries'] == 0
        assert client._connection_pool_stats['failed_queries'] == 0
        assert client._connection_pool_stats['transaction_count'] == 0
        assert client._connection_pool_stats['rollback_count'] == 0
    
    @pytest.mark.asyncio
    async def test_execute_query_async_success(self, analysis_client, mock_base_client):
        """Test successful query execution."""
        mock_result = [{'id': 1, 'name': 'test'}]
        mock_base_client.execute_query_async.return_value = mock_result
        
        result = await analysis_client.execute_query_async(
            "SELECT * FROM test", 
            {"param": "value"}
        )
        
        assert result == mock_result
        assert analysis_client._connection_pool_stats['total_queries'] == 1
        assert analysis_client._connection_pool_stats['failed_queries'] == 0
        mock_base_client.execute_query_async.assert_called_once_with(
            "SELECT * FROM test", 
            {"param": "value"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_query_async_failure(self, analysis_client, mock_base_client):
        """Test query execution failure."""
        mock_base_client.execute_query_async.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await analysis_client.execute_query_async("SELECT * FROM test")
        
        assert analysis_client._connection_pool_stats['total_queries'] == 1
        assert analysis_client._connection_pool_stats['failed_queries'] == 1
    
    @pytest.mark.asyncio
    async def test_execute_update_async_success(self, analysis_client, mock_base_client):
        """Test successful update execution."""
        mock_base_client.execute_update_async.return_value = 3
        
        result = await analysis_client.execute_update_async(
            "UPDATE test SET name = :name", 
            {"name": "updated"}
        )
        
        assert result == 3
        assert analysis_client._connection_pool_stats['total_queries'] == 1
        assert analysis_client._connection_pool_stats['failed_queries'] == 0
        mock_base_client.execute_update_async.assert_called_once_with(
            "UPDATE test SET name = :name", 
            {"name": "updated"}
        )
    
    @pytest.mark.asyncio
    async def test_execute_update_async_failure(self, analysis_client, mock_base_client):
        """Test update execution failure."""
        mock_base_client.execute_update_async.side_effect = Exception("Update failed")
        
        with pytest.raises(Exception, match="Update failed"):
            await analysis_client.execute_update_async("UPDATE test SET name = 'test'")
        
        assert analysis_client._connection_pool_stats['total_queries'] == 1
        assert analysis_client._connection_pool_stats['failed_queries'] == 1
    
    @pytest.mark.asyncio
    async def test_transaction_success(self, analysis_client, mock_base_client):
        """Test successful transaction."""
        mock_session = Mock()
        
        # Mock the async context manager properly
        @asynccontextmanager
        async def mock_get_async_session():
            yield mock_session
        
        mock_base_client.get_async_session = mock_get_async_session
        
        async with analysis_client.transaction() as session:
            assert session == mock_session
        
        assert analysis_client._connection_pool_stats['transaction_count'] == 1
        assert analysis_client._connection_pool_stats['rollback_count'] == 0
    
    @pytest.mark.asyncio
    async def test_transaction_failure(self, analysis_client, mock_base_client):
        """Test transaction failure and rollback."""
        mock_session = Mock()
        
        # Mock the async context manager properly
        @asynccontextmanager
        async def mock_get_async_session():
            yield mock_session
        
        mock_base_client.get_async_session = mock_get_async_session
        
        with pytest.raises(Exception, match="Transaction error"):
            async with analysis_client.transaction():
                raise Exception("Transaction error")
        
        assert analysis_client._connection_pool_stats['transaction_count'] == 1
        assert analysis_client._connection_pool_stats['rollback_count'] == 1
    
    @pytest.mark.asyncio
    async def test_batch_execute_updates_success(self, analysis_client, mock_base_client):
        """Test successful batch update execution."""
        mock_base_client.execute_update_async.side_effect = [2, 1, 3]
        mock_session = Mock()
        
        # Mock the async context manager properly
        @asynccontextmanager
        async def mock_get_async_session():
            yield mock_session
        
        mock_base_client.get_async_session = mock_get_async_session
        
        queries_and_params = [
            ("UPDATE table1 SET col1 = :val1", {"val1": "value1"}),
            ("UPDATE table2 SET col2 = :val2", {"val2": "value2"}),
            ("UPDATE table3 SET col3 = :val3", {"val3": "value3"})
        ]
        
        results = await analysis_client.batch_execute_updates(queries_and_params)
        
        assert results == [2, 1, 3]
        assert mock_base_client.execute_update_async.call_count == 3
    
    @pytest.mark.asyncio
    async def test_batch_execute_updates_failure(self, analysis_client, mock_base_client):
        """Test batch update execution with failure."""
        mock_base_client.execute_update_async.side_effect = [2, Exception("Batch error")]
        mock_session = Mock()
        
        # Mock the async context manager properly
        @asynccontextmanager
        async def mock_get_async_session():
            yield mock_session
        
        mock_base_client.get_async_session = mock_get_async_session
        
        queries_and_params = [
            ("UPDATE table1 SET col1 = :val1", {"val1": "value1"}),
            ("UPDATE table2 SET col2 = :val2", {"val2": "value2"})
        ]
        
        with pytest.raises(Exception, match="Batch error"):
            await analysis_client.batch_execute_updates(queries_and_params)
    
    @pytest.mark.asyncio
    async def test_get_user_analysis_summary_success(self, analysis_client, mock_base_client):
        """Test getting user analysis summary."""
        user_id = uuid4()
        mock_result = [{
            'user_id': str(user_id),
            'email': 'test@example.com',
            'bio': 'Test bio',
            'user_created_at': datetime.now(timezone.utc),
            'writing_style_analysis': 'Test analysis',
            'negative_analysis': 'Test negative',
            'topics_of_interest': '["topic1", "topic2"]',
            'last_analysis_at': datetime.now(timezone.utc),
            'analysis_scope': '{"posts": 5, "messages": 10}',
            'new_posts_count': 3,
            'new_dismissed_posts_count': 1,
            'new_messages_count': 7
        }]
        mock_base_client.execute_query_async.return_value = mock_result
        
        summary = await analysis_client.get_user_analysis_summary(user_id)
        
        assert summary['user_id'] == str(user_id)
        assert summary['email'] == 'test@example.com'
        assert summary['topics_of_interest'] == ["topic1", "topic2"]
        assert summary['analysis_scope'] == {"posts": 5, "messages": 10}
        assert summary['new_posts_count'] == 3
        assert summary['new_dismissed_posts_count'] == 1
        assert summary['new_messages_count'] == 7
    
    @pytest.mark.asyncio
    async def test_get_user_analysis_summary_not_found(self, analysis_client, mock_base_client):
        """Test getting user analysis summary for non-existent user."""
        user_id = uuid4()
        mock_base_client.execute_query_async.return_value = []
        
        with pytest.raises(ValueError, match=f"User {user_id} not found or inactive"):
            await analysis_client.get_user_analysis_summary(user_id)
    
    @pytest.mark.asyncio
    async def test_get_user_analysis_summary_invalid_json(self, analysis_client, mock_base_client):
        """Test getting user analysis summary with invalid JSON fields."""
        user_id = uuid4()
        mock_result = [{
            'user_id': str(user_id),
            'email': 'test@example.com',
            'bio': 'Test bio',
            'user_created_at': datetime.now(timezone.utc),
            'writing_style_analysis': 'Test analysis',
            'negative_analysis': 'Test negative',
            'topics_of_interest': 'invalid json',
            'last_analysis_at': datetime.now(timezone.utc),
            'analysis_scope': 'invalid json',
            'new_posts_count': 3,
            'new_dismissed_posts_count': 1,
            'new_messages_count': 7
        }]
        mock_base_client.execute_query_async.return_value = mock_result
        
        summary = await analysis_client.get_user_analysis_summary(user_id)
        
        assert summary['topics_of_interest'] == []
        assert summary['analysis_scope'] is None
    
    @pytest.mark.asyncio
    async def test_update_user_analysis_results(self, analysis_client, mock_base_client):
        """Test updating user analysis results."""
        user_id = uuid4()
        analysis_results = {
            'writing_style': 'Updated writing style',
            'bio_update': 'Updated bio',
            'negative_analysis': 'Updated negative analysis'
        }
        analysis_scope = {'posts': 5, 'messages': 10}
        
        mock_base_client.execute_update_async.return_value = 1
        mock_session = Mock()
        
        # Mock the async context manager properly
        @asynccontextmanager
        async def mock_get_async_session():
            yield mock_session
        
        mock_base_client.get_async_session = mock_get_async_session
        
        await analysis_client.update_user_analysis_results(
            user_id, analysis_results, analysis_scope
        )
        
        # Should call execute_update_async 4 times (3 for analysis results + 1 for tracking)
        assert mock_base_client.execute_update_async.call_count == 4
    
    @pytest.mark.asyncio
    async def test_update_user_analysis_results_partial(self, analysis_client, mock_base_client):
        """Test updating user analysis results with partial data."""
        user_id = uuid4()
        analysis_results = {
            'writing_style': 'Updated writing style'
        }
        analysis_scope = {'posts': 3}
        
        mock_base_client.execute_update_async.return_value = 1
        mock_session = Mock()
        
        # Mock the async context manager properly
        @asynccontextmanager
        async def mock_get_async_session():
            yield mock_session
        
        mock_base_client.get_async_session = mock_get_async_session
        
        await analysis_client.update_user_analysis_results(
            user_id, analysis_results, analysis_scope
        )
        
        # Should call execute_update_async 2 times (1 for writing style + 1 for tracking)
        assert mock_base_client.execute_update_async.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_users_needing_analysis_batch(self, analysis_client, mock_base_client):
        """Test getting users needing analysis in batches."""
        mock_result = [
            {
                'user_id': str(uuid4()),
                'email': 'user1@example.com',
                'last_analysis_at': datetime.now(timezone.utc),
                'post_count': 6,
                'message_count': 12
            },
            {
                'user_id': str(uuid4()),
                'email': 'user2@example.com',
                'last_analysis_at': datetime.now(timezone.utc),
                'post_count': 8,
                'message_count': 5
            }
        ]
        mock_base_client.execute_query_async.return_value = mock_result
        
        result = await analysis_client.get_users_needing_analysis_batch(
            post_threshold=5,
            message_threshold=10,
            batch_size=50,
            offset=0
        )
        
        assert result == mock_result
        assert len(result) == 2
        mock_base_client.execute_query_async.assert_called_once()
        
        # Check query parameters
        call_args = mock_base_client.execute_query_async.call_args
        params = call_args[0][1]
        assert params['post_threshold'] == 5
        assert params['message_threshold'] == 10
        assert params['batch_size'] == 50
        assert params['offset'] == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_stale_analysis_tracking(self, analysis_client, mock_base_client):
        """Test cleaning up stale analysis tracking records."""
        mock_base_client.execute_update_async.return_value = 3
        
        result = await analysis_client.cleanup_stale_analysis_tracking(stale_hours=48)
        
        assert result == 3
        mock_base_client.execute_update_async.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_analysis_performance_metrics(self, analysis_client, mock_base_client):
        """Test getting analysis performance metrics."""
        mock_result = [{
            'total_users': 100,
            'analyzed_users': 85,
            'unanalyzed_users': 15,
            'avg_time_since_analysis': 3600.0,
            'analyzed_last_24h': 25,
            'analyzed_last_7d': 70
        }]
        mock_base_client.execute_query_async.return_value = mock_result
        
        # Set some connection stats before the call
        analysis_client._connection_pool_stats['total_queries'] = 50
        analysis_client._connection_pool_stats['failed_queries'] = 2
        
        metrics = await analysis_client.get_analysis_performance_metrics()
        
        assert metrics['total_users'] == 100
        assert metrics['analyzed_users'] == 85
        assert metrics['unanalyzed_users'] == 15
        # The query call itself increments total_queries by 1
        assert metrics['connection_pool']['total_queries'] == 51
        assert metrics['connection_pool']['failed_queries'] == 2
    
    def test_get_connection_stats(self, analysis_client):
        """Test getting connection statistics."""
        analysis_client._connection_pool_stats['total_queries'] = 25
        analysis_client._connection_pool_stats['failed_queries'] = 1
        
        stats = analysis_client.get_connection_stats()
        
        assert stats['total_queries'] == 25
        assert stats['failed_queries'] == 1
        assert stats['active_connections'] == 0
    
    def test_reset_connection_stats(self, analysis_client):
        """Test resetting connection statistics."""
        analysis_client._connection_pool_stats['total_queries'] = 25
        analysis_client._connection_pool_stats['failed_queries'] = 1
        
        analysis_client.reset_connection_stats()
        
        assert analysis_client._connection_pool_stats['total_queries'] == 0
        assert analysis_client._connection_pool_stats['failed_queries'] == 0
        assert analysis_client._connection_pool_stats['active_connections'] == 0
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, analysis_client, mock_base_client):
        """Test successful health check."""
        mock_result = [{'test': 1, 'server_time': datetime.now(timezone.utc)}]
        mock_base_client.execute_query_async.return_value = mock_result
        
        health = await analysis_client.health_check()
        
        assert health['status'] == 'healthy'
        assert 'response_time_ms' in health
        assert 'server_time' in health
        assert 'connection_stats' in health
        assert health['response_time_ms'] >= 0
    
    @pytest.mark.asyncio
    async def test_health_check_unexpected_result(self, analysis_client, mock_base_client):
        """Test health check with unexpected result."""
        mock_result = [{'test': 0}]  # Unexpected result
        mock_base_client.execute_query_async.return_value = mock_result
        
        health = await analysis_client.health_check()
        
        assert health['status'] == 'unhealthy'
        assert health['error'] == 'Unexpected query result'
        assert 'response_time_ms' in health
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, analysis_client, mock_base_client):
        """Test health check with database failure."""
        mock_base_client.execute_query_async.side_effect = Exception("Connection failed")
        
        health = await analysis_client.health_check()
        
        assert health['status'] == 'unhealthy'
        assert health['error'] == 'Connection failed'
        assert 'connection_stats' in health
    
    def test_close(self, analysis_client, mock_base_client):
        """Test closing the client."""
        analysis_client.close()
        
        mock_base_client.close.assert_called_once()
    
    def test_close_with_error(self, analysis_client, mock_base_client):
        """Test closing the client with error."""
        mock_base_client.close.side_effect = Exception("Close error")
        
        # Should not raise exception
        analysis_client.close()
        
        mock_base_client.close.assert_called_once()


class TestCreateAnalysisDatabaseClient:
    """Test the factory function for creating analysis database client."""
    
    @patch('shared.cloud_sql_client.get_cloud_sql_client')
    def test_create_analysis_database_client(self, mock_get_client):
        """Test creating analysis database client."""
        mock_base_client = Mock()
        mock_get_client.return_value = mock_base_client
        
        client = create_analysis_database_client()
        
        assert isinstance(client, AnalysisDatabaseClient)
        assert client.base_client == mock_base_client
        mock_get_client.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
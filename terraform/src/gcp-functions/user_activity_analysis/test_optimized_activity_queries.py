"""
Unit tests for OptimizedActivityQueries class.

Tests query optimization, performance monitoring, and batch processing capabilities
as specified in requirements 1.2, 2.1, 2.2, and 10.4.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from optimized_activity_queries import OptimizedActivityQueries


class TestOptimizedActivityQueries:
    """Test cases for OptimizedActivityQueries."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mock database client."""
        mock_client = AsyncMock()
        mock_client.execute_batch = AsyncMock()
        return mock_client

    @pytest.fixture
    def optimized_queries(self, mock_db_client):
        """Create OptimizedActivityQueries instance with mock database."""
        return OptimizedActivityQueries(mock_db_client)

    @pytest.fixture
    def sample_user_ids(self):
        """Generate sample user IDs for testing."""
        return [uuid4() for _ in range(3)]

    @pytest.fixture
    def sample_timestamp(self):
        """Generate a sample timestamp for testing."""
        return datetime.now(timezone.utc) - timedelta(days=7)

    @pytest.mark.asyncio
    async def test_initialization(self, mock_db_client):
        """Test OptimizedActivityQueries initialization."""
        queries = OptimizedActivityQueries(mock_db_client)
        
        assert queries.db_client is mock_db_client
        assert queries.query_performance_log == []

    @pytest.mark.asyncio
    async def test_get_optimized_post_counts_no_timestamp(self, optimized_queries, mock_db_client):
        """Test optimized post counts without timestamp filter."""
        user_id = uuid4()
        
        # Mock database response
        mock_db_client.fetch_one.return_value = {
            'scheduled_count': 5,
            'dismissed_count': 3
        }
        
        result = await optimized_queries.get_optimized_post_counts(user_id)
        
        assert result == {
            'scheduled_count': 5,
            'dismissed_count': 3
        }
        
        # Verify query was called
        mock_db_client.fetch_one.assert_called_once()
        call_args = mock_db_client.fetch_one.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        # Verify optimized query structure
        assert "COUNT(CASE WHEN" in query
        assert "scheduled" in query.lower()
        assert "dismissed" in query.lower()
        assert str(user_id) in params

    @pytest.mark.asyncio
    async def test_get_optimized_post_counts_with_timestamp(self, optimized_queries, mock_db_client, sample_timestamp):
        """Test optimized post counts with timestamp filter."""
        user_id = uuid4()
        
        mock_db_client.fetch_one.return_value = {
            'scheduled_count': 3,
            'dismissed_count': 2
        }
        
        result = await optimized_queries.get_optimized_post_counts(user_id, sample_timestamp)
        
        assert result == {
            'scheduled_count': 3,
            'dismissed_count': 2
        }
        
        # Verify timestamp was included in query
        call_args = mock_db_client.fetch_one.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "created_at >" in query
        assert sample_timestamp in params

    @pytest.mark.asyncio
    async def test_get_optimized_post_counts_no_results(self, optimized_queries, mock_db_client):
        """Test optimized post counts when no results are returned."""
        user_id = uuid4()
        mock_db_client.fetch_one.return_value = None
        
        result = await optimized_queries.get_optimized_post_counts(user_id)
        
        assert result == {
            'scheduled_count': 0,
            'dismissed_count': 0
        }

    @pytest.mark.asyncio
    async def test_get_optimized_message_counts_no_timestamp(self, optimized_queries, mock_db_client):
        """Test optimized message counts without timestamp filter."""
        user_id = uuid4()
        
        mock_db_client.fetch_one.return_value = {'total_count': 8}
        
        result = await optimized_queries.get_optimized_message_counts(user_id)
        
        assert result == 8
        
        # Verify optimized query structure with window function
        call_args = mock_db_client.fetch_one.call_args
        query = call_args[0][0]
        
        assert "WITH ranked_messages AS" in query
        assert "ROW_NUMBER() OVER" in query
        assert "idea_bank_id IS NOT NULL AND message_rank = 1" in query

    @pytest.mark.asyncio
    async def test_get_optimized_message_counts_with_timestamp(self, optimized_queries, mock_db_client, sample_timestamp):
        """Test optimized message counts with timestamp filter."""
        user_id = uuid4()
        
        mock_db_client.fetch_one.return_value = {'total_count': 12}
        
        result = await optimized_queries.get_optimized_message_counts(user_id, sample_timestamp)
        
        assert result == 12
        
        # Verify timestamp filtering
        call_args = mock_db_client.fetch_one.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "c.created_at >" in query
        assert "m.created_at >" in query
        assert params.count(sample_timestamp) == 2  # Should appear twice

    @pytest.mark.asyncio
    async def test_get_batch_user_activity_counts(self, optimized_queries, mock_db_client, sample_user_ids):
        """Test batch processing for multiple users."""
        # Mock post results
        post_results = [
            {'user_id': str(sample_user_ids[0]), 'scheduled_count': 5, 'dismissed_count': 2},
            {'user_id': str(sample_user_ids[1]), 'scheduled_count': 3, 'dismissed_count': 1},
        ]
        
        # Mock message results
        message_results = [
            {'user_id': str(sample_user_ids[0]), 'message_count': 8},
            {'user_id': str(sample_user_ids[2]), 'message_count': 12},
        ]
        
        mock_db_client.fetch_all.side_effect = [post_results, message_results]
        
        result = await optimized_queries.get_batch_user_activity_counts(sample_user_ids)
        
        # Verify results for all users
        assert len(result) == 3
        
        # User 0: has both posts and messages
        assert result[sample_user_ids[0]] == {
            'scheduled_posts': 5,
            'dismissed_posts': 2,
            'total_posts': 7,
            'messages': 8
        }
        
        # User 1: has posts only
        assert result[sample_user_ids[1]] == {
            'scheduled_posts': 3,
            'dismissed_posts': 1,
            'total_posts': 4,
            'messages': 0
        }
        
        # User 2: has messages only
        assert result[sample_user_ids[2]] == {
            'scheduled_posts': 0,
            'dismissed_posts': 0,
            'total_posts': 0,
            'messages': 12
        }

    @pytest.mark.asyncio
    async def test_get_batch_user_activity_counts_with_timestamps(self, optimized_queries, mock_db_client, sample_user_ids, sample_timestamp):
        """Test batch processing with different timestamps per user."""
        since_timestamps = {
            sample_user_ids[0]: sample_timestamp,
            sample_user_ids[1]: None,  # No timestamp for this user
            sample_user_ids[2]: sample_timestamp - timedelta(days=1)
        }
        
        mock_db_client.fetch_all.side_effect = [[], []]  # Empty results
        
        result = await optimized_queries.get_batch_user_activity_counts(
            sample_user_ids, since_timestamps
        )
        
        # Verify all users are included with zero counts
        assert len(result) == 3
        for user_id in sample_user_ids:
            assert user_id in result
            assert result[user_id]['total_posts'] == 0
            assert result[user_id]['messages'] == 0

    @pytest.mark.asyncio
    async def test_get_users_analysis_tracking_batch_all_users(self, optimized_queries, mock_db_client):
        """Test getting analysis tracking for all active users."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        
        tracking_results = [
            {
                'user_id': str(user_id_1),
                'email': 'user1@test.com',
                'last_analysis_at': datetime.now(timezone.utc),
                'analysis_scope': {'posts': 5},
                'tracking_created_at': datetime.now(timezone.utc),
                'tracking_updated_at': datetime.now(timezone.utc)
            },
            {
                'user_id': str(user_id_2),
                'email': 'user2@test.com',
                'last_analysis_at': None,
                'analysis_scope': None,
                'tracking_created_at': None,
                'tracking_updated_at': None
            }
        ]
        
        mock_db_client.fetch_all.return_value = tracking_results
        
        result = await optimized_queries.get_users_analysis_tracking_batch()
        
        assert len(result) == 2
        assert result[user_id_1]['has_tracking_record'] is True
        assert result[user_id_2]['has_tracking_record'] is False

    @pytest.mark.asyncio
    async def test_get_users_analysis_tracking_batch_specific_users(self, optimized_queries, mock_db_client, sample_user_ids):
        """Test getting analysis tracking for specific users."""
        mock_db_client.fetch_all.return_value = []
        
        await optimized_queries.get_users_analysis_tracking_batch(sample_user_ids)
        
        # Verify query included user ID filter
        call_args = mock_db_client.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "u.id = ANY(%s)" in query
        assert len(params) == 1
        assert len(params[0]) == 3  # Three user IDs

    @pytest.mark.asyncio
    async def test_get_content_for_analysis_batch(self, optimized_queries, mock_db_client, sample_user_ids, sample_timestamp):
        """Test getting content for analysis in batch."""
        user_activity_data = {
            sample_user_ids[0]: {'last_analysis_at': sample_timestamp},
            sample_user_ids[1]: {'last_analysis_at': None},
        }
        
        # Mock post results
        post_results = [
            {
                'user_id': str(sample_user_ids[0]),
                'id': str(uuid4()),
                'content': 'Test post content',
                'status': 'scheduled',
                'user_feedback': None,
                'created_at': datetime.now(timezone.utc),
                'post_category': 'scheduled'
            }
        ]
        
        # Mock message results
        message_results = [
            {
                'user_id': str(sample_user_ids[0]),
                'id': str(uuid4()),
                'content': 'Test message content',
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        mock_db_client.fetch_all.side_effect = [post_results, message_results]
        
        result = await optimized_queries.get_content_for_analysis_batch(user_activity_data)
        
        assert len(result) == 2
        assert len(result[sample_user_ids[0]]['scheduled_posts']) == 1
        assert len(result[sample_user_ids[0]]['messages']) == 1
        assert len(result[sample_user_ids[1]]['scheduled_posts']) == 0

    @pytest.mark.asyncio
    async def test_update_analysis_tracking_batch(self, optimized_queries, mock_db_client, sample_user_ids):
        """Test batch updating of analysis tracking records."""
        tracking_updates = [
            {
                'user_id': sample_user_ids[0],
                'analysis_timestamp': datetime.now(timezone.utc),
                'last_post_id': uuid4(),
                'last_message_id': uuid4(),
                'analysis_scope': {'posts': 5, 'messages': 8}
            },
            {
                'user_id': sample_user_ids[1],
                'analysis_timestamp': datetime.now(timezone.utc),
                'analysis_scope': {'posts': 3, 'messages': 2}
            }
        ]
        
        await optimized_queries.update_analysis_tracking_batch(tracking_updates)
        
        # Verify batch execute was called
        mock_db_client.execute_batch.assert_called_once()
        call_args = mock_db_client.execute_batch.call_args
        query = call_args[0][0]
        values = call_args[0][1]
        
        assert "INSERT INTO user_analysis_tracking" in query
        assert "ON CONFLICT (user_id)" in query
        assert len(values) == 2

    @pytest.mark.asyncio
    async def test_update_analysis_tracking_batch_empty(self, optimized_queries, mock_db_client):
        """Test batch update with empty list."""
        await optimized_queries.update_analysis_tracking_batch([])
        
        # Should not call database
        mock_db_client.execute_batch.assert_not_called()

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, optimized_queries, mock_db_client):
        """Test query performance monitoring."""
        user_id = uuid4()
        mock_db_client.fetch_one.return_value = {'scheduled_count': 1, 'dismissed_count': 1}
        
        # Execute a query to generate performance data
        await optimized_queries.get_optimized_post_counts(user_id)
        
        # Check performance log
        assert len(optimized_queries.query_performance_log) == 1
        
        log_entry = optimized_queries.query_performance_log[0]
        assert log_entry['query_name'] == 'get_optimized_post_counts'
        assert 'execution_time_ms' in log_entry
        assert 'timestamp' in log_entry
        assert log_entry['execution_time_ms'] >= 0

    def test_get_performance_metrics_empty(self, optimized_queries):
        """Test performance metrics with no queries executed."""
        metrics = optimized_queries.get_performance_metrics()
        
        assert metrics['total_queries'] == 0
        assert metrics['average_execution_time_ms'] == 0
        assert metrics['slow_queries_count'] == 0
        assert metrics['queries_by_type'] == {}

    def test_get_performance_metrics_with_data(self, optimized_queries):
        """Test performance metrics with query data."""
        # Add mock performance data
        optimized_queries.query_performance_log = [
            {
                'query_name': 'test_query_1',
                'execution_time_ms': 50,
                'timestamp': datetime.now()
            },
            {
                'query_name': 'test_query_1',
                'execution_time_ms': 150,  # Slow query
                'timestamp': datetime.now()
            },
            {
                'query_name': 'test_query_2',
                'execution_time_ms': 25,
                'timestamp': datetime.now()
            }
        ]
        
        metrics = optimized_queries.get_performance_metrics()
        
        assert metrics['total_queries'] == 3
        assert metrics['average_execution_time_ms'] == 75.0  # (50 + 150 + 25) / 3
        assert metrics['slow_queries_count'] == 1  # Only the 150ms query
        assert len(metrics['queries_by_type']) == 2
        assert metrics['queries_by_type']['test_query_1']['count'] == 2
        assert metrics['queries_by_type']['test_query_1']['avg_time_ms'] == 100.0

    def test_clear_performance_log(self, optimized_queries):
        """Test clearing performance log."""
        # Add some data
        optimized_queries.query_performance_log = [{'test': 'data'}]
        
        optimized_queries.clear_performance_log()
        
        assert optimized_queries.query_performance_log == []

    @pytest.mark.asyncio
    async def test_validate_indexes(self, optimized_queries, mock_db_client):
        """Test index validation."""
        # Mock existing indexes
        mock_db_client.fetch_all.return_value = [
            {'indexname': 'idx_posts_user_created_status'},
            {'indexname': 'idx_messages_conversation_created'},
            {'indexname': 'idx_user_analysis_tracking_user_id'}
        ]
        
        result = await optimized_queries.validate_indexes()
        
        # Should return status for all required indexes
        assert 'idx_posts_user_created_status' in result
        assert 'idx_messages_conversation_created' in result
        assert 'idx_conversations_user_idea_created' in result
        assert 'idx_user_analysis_tracking_user_id' in result
        assert 'idx_user_analysis_tracking_last_analysis' in result
        
        # Check specific results
        assert result['idx_posts_user_created_status'] is True
        assert result['idx_conversations_user_idea_created'] is False  # Not in mock data

    @pytest.mark.asyncio
    async def test_batch_processing_empty_input(self, optimized_queries, mock_db_client):
        """Test batch processing with empty input."""
        result = await optimized_queries.get_batch_user_activity_counts([])
        
        assert result == {}
        mock_db_client.fetch_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_query_parameter_handling(self, optimized_queries, mock_db_client):
        """Test proper handling of query parameters."""
        user_id = uuid4()
        timestamp = datetime.now(timezone.utc)
        
        mock_db_client.fetch_one.return_value = {'scheduled_count': 1, 'dismissed_count': 1}
        
        await optimized_queries.get_optimized_post_counts(user_id, timestamp)
        
        call_args = mock_db_client.fetch_one.call_args
        params = call_args[0][1]
        
        # Verify UUID is converted to string
        assert str(user_id) in params
        assert timestamp in params

    @pytest.mark.asyncio
    async def test_error_handling_in_performance_monitoring(self, optimized_queries, mock_db_client):
        """Test that performance monitoring works even when queries fail."""
        user_id = uuid4()
        mock_db_client.fetch_one.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            await optimized_queries.get_optimized_post_counts(user_id)
        
        # Performance log should still be updated
        assert len(optimized_queries.query_performance_log) == 1
        assert optimized_queries.query_performance_log[0]['query_name'] == 'get_optimized_post_counts'

    @pytest.mark.asyncio
    async def test_concurrent_batch_processing(self, optimized_queries, mock_db_client):
        """Test that batch processing can handle concurrent operations safely."""
        user_ids_1 = [uuid4() for _ in range(2)]
        user_ids_2 = [uuid4() for _ in range(2)]
        
        # Mock different responses for different calls
        mock_db_client.fetch_all.side_effect = [
            [],  # First batch posts
            [],  # First batch messages
            [],  # Second batch posts
            []   # Second batch messages
        ]
        
        # Simulate concurrent calls
        import asyncio
        results = await asyncio.gather(
            optimized_queries.get_batch_user_activity_counts(user_ids_1),
            optimized_queries.get_batch_user_activity_counts(user_ids_2)
        )
        
        # Verify both calls completed successfully
        assert len(results[0]) == 2
        assert len(results[1]) == 2
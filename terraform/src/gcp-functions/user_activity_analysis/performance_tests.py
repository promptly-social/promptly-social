"""
Performance tests for OptimizedActivityQueries.

Tests query performance, load handling, and scalability as specified in requirement 10.4.
These tests validate that the optimized queries can handle large datasets efficiently.
"""

import pytest
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from optimized_activity_queries import OptimizedActivityQueries


class TestOptimizedActivityQueriesPerformance:
    """Performance test cases for OptimizedActivityQueries."""

    @pytest.fixture
    def mock_db_client_with_delay(self):
        """Create a mock database client that simulates realistic query times."""
        mock_client = AsyncMock()
        
        async def mock_fetch_one_with_delay(*args, **kwargs):
            # Simulate database query time (1-10ms)
            await asyncio.sleep(0.001 + (hash(str(args)) % 10) * 0.001)
            return {'scheduled_count': 5, 'dismissed_count': 3, 'total_count': 8}
        
        async def mock_fetch_all_with_delay(*args, **kwargs):
            # Simulate batch query time (5-50ms)
            await asyncio.sleep(0.005 + (hash(str(args)) % 45) * 0.001)
            return []
        
        async def mock_execute_batch_with_delay(*args, **kwargs):
            # Simulate batch update time (10-100ms)
            await asyncio.sleep(0.01 + (hash(str(args)) % 90) * 0.001)
        
        mock_client.fetch_one.side_effect = mock_fetch_one_with_delay
        mock_client.fetch_all.side_effect = mock_fetch_all_with_delay
        mock_client.execute_batch.side_effect = mock_execute_batch_with_delay
        
        return mock_client

    @pytest.fixture
    def optimized_queries_with_delay(self, mock_db_client_with_delay):
        """Create OptimizedActivityQueries with realistic database delays."""
        return OptimizedActivityQueries(mock_db_client_with_delay)

    @pytest.mark.asyncio
    async def test_single_user_query_performance(self, optimized_queries_with_delay):
        """Test performance of single user queries."""
        user_id = uuid4()
        timestamp = datetime.now(timezone.utc) - timedelta(days=7)
        
        start_time = time.time()
        
        # Execute multiple query types
        post_counts = await optimized_queries_with_delay.get_optimized_post_counts(user_id, timestamp)
        message_counts = await optimized_queries_with_delay.get_optimized_message_counts(user_id, timestamp)
        
        execution_time = time.time() - start_time
        
        # Verify results
        assert post_counts['scheduled_count'] == 5
        assert post_counts['dismissed_count'] == 3
        assert message_counts == 8
        
        # Performance assertion: should complete within reasonable time
        assert execution_time < 0.1  # 100ms for two queries
        
        # Check performance monitoring
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 2
        assert metrics['average_execution_time_ms'] > 0

    @pytest.mark.asyncio
    async def test_batch_processing_performance_small(self, optimized_queries_with_delay):
        """Test batch processing performance with small user set (10 users)."""
        user_ids = [uuid4() for _ in range(10)]
        
        start_time = time.time()
        
        result = await optimized_queries_with_delay.get_batch_user_activity_counts(user_ids)
        
        execution_time = time.time() - start_time
        
        # Verify all users processed
        assert len(result) == 10
        
        # Performance assertion: batch should be faster than individual queries
        assert execution_time < 0.2  # 200ms for 10 users in batch
        
        # Check that only 2 queries were executed (posts and messages batch)
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 2

    @pytest.mark.asyncio
    async def test_batch_processing_performance_medium(self, optimized_queries_with_delay):
        """Test batch processing performance with medium user set (100 users)."""
        user_ids = [uuid4() for _ in range(100)]
        
        start_time = time.time()
        
        result = await optimized_queries_with_delay.get_batch_user_activity_counts(user_ids)
        
        execution_time = time.time() - start_time
        
        # Verify all users processed
        assert len(result) == 100
        
        # Performance assertion: should scale well
        assert execution_time < 0.5  # 500ms for 100 users
        
        # Verify batch efficiency (only 2 queries regardless of user count)
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 2

    @pytest.mark.asyncio
    async def test_batch_processing_performance_large(self, optimized_queries_with_delay):
        """Test batch processing performance with large user set (1000 users)."""
        user_ids = [uuid4() for _ in range(1000)]
        
        start_time = time.time()
        
        result = await optimized_queries_with_delay.get_batch_user_activity_counts(user_ids)
        
        execution_time = time.time() - start_time
        
        # Verify all users processed
        assert len(result) == 1000
        
        # Performance assertion: should handle large batches
        assert execution_time < 2.0  # 2 seconds for 1000 users
        
        # Verify batch efficiency maintained
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 2

    @pytest.mark.asyncio
    async def test_concurrent_query_performance(self, optimized_queries_with_delay):
        """Test performance under concurrent load."""
        user_ids = [uuid4() for _ in range(20)]
        
        start_time = time.time()
        
        # Execute concurrent queries
        tasks = []
        for user_id in user_ids:
            task = optimized_queries_with_delay.get_optimized_post_counts(user_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        execution_time = time.time() - start_time
        
        # Verify all queries completed
        assert len(results) == 20
        
        # Performance assertion: concurrent execution should be efficient
        assert execution_time < 0.5  # 500ms for 20 concurrent queries
        
        # Check performance metrics
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 20

    @pytest.mark.asyncio
    async def test_mixed_workload_performance(self, optimized_queries_with_delay):
        """Test performance with mixed query types."""
        user_ids = [uuid4() for _ in range(50)]
        
        start_time = time.time()
        
        # Mix of individual and batch queries
        individual_tasks = []
        for i in range(0, 10):  # First 10 users individual queries
            task = optimized_queries_with_delay.get_optimized_post_counts(user_ids[i])
            individual_tasks.append(task)
        
        # Batch query for remaining users
        batch_task = optimized_queries_with_delay.get_batch_user_activity_counts(user_ids[10:])
        
        # Execute concurrently
        individual_results = await asyncio.gather(*individual_tasks)
        batch_result = await batch_task
        
        execution_time = time.time() - start_time
        
        # Verify results
        assert len(individual_results) == 10
        assert len(batch_result) == 40
        
        # Performance assertion
        assert execution_time < 1.0  # 1 second for mixed workload
        
        # Check query efficiency
        metrics = optimized_queries_with_delay.get_performance_metrics()
        # Should be 10 individual + 2 batch = 12 total queries
        assert metrics['total_queries'] == 12

    @pytest.mark.asyncio
    async def test_tracking_batch_update_performance(self, optimized_queries_with_delay):
        """Test performance of batch tracking updates."""
        user_ids = [uuid4() for _ in range(100)]
        
        # Prepare tracking updates
        tracking_updates = []
        for user_id in user_ids:
            tracking_updates.append({
                'user_id': user_id,
                'analysis_timestamp': datetime.now(timezone.utc),
                'analysis_scope': {'posts': 5, 'messages': 8}
            })
        
        start_time = time.time()
        
        await optimized_queries_with_delay.update_analysis_tracking_batch(tracking_updates)
        
        execution_time = time.time() - start_time
        
        # Performance assertion: batch update should be efficient
        assert execution_time < 0.5  # 500ms for 100 updates
        
        # Verify single batch operation
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 1

    @pytest.mark.asyncio
    async def test_content_retrieval_performance(self, optimized_queries_with_delay):
        """Test performance of content retrieval for analysis."""
        user_ids = [uuid4() for _ in range(50)]
        
        # Prepare user activity data
        user_activity_data = {}
        for user_id in user_ids:
            user_activity_data[user_id] = {
                'last_analysis_at': datetime.now(timezone.utc) - timedelta(days=7)
            }
        
        start_time = time.time()
        
        content_data = await optimized_queries_with_delay.get_content_for_analysis_batch(user_activity_data)
        
        execution_time = time.time() - start_time
        
        # Verify content retrieved for all users
        assert len(content_data) == 50
        
        # Performance assertion
        assert execution_time < 1.0  # 1 second for content retrieval
        
        # Should execute 2 queries (posts and messages)
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 2

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_dataset(self, optimized_queries_with_delay):
        """Test memory efficiency with large datasets."""
        user_ids = [uuid4() for _ in range(500)]
        
        # Clear performance log to start fresh
        optimized_queries_with_delay.clear_performance_log()
        
        # Execute batch operation
        result = await optimized_queries_with_delay.get_batch_user_activity_counts(user_ids)
        
        # Verify results
        assert len(result) == 500
        
        # Check memory usage of performance log
        metrics = optimized_queries_with_delay.get_performance_metrics()
        assert metrics['total_queries'] == 2  # Should not grow with user count
        
        # Performance log should be manageable size
        assert len(optimized_queries_with_delay.query_performance_log) == 2

    @pytest.mark.asyncio
    async def test_query_optimization_effectiveness(self, optimized_queries_with_delay):
        """Test that optimized queries are more efficient than individual queries."""
        user_ids = [uuid4() for _ in range(20)]
        
        # Test individual queries (simulating non-optimized approach)
        start_individual = time.time()
        individual_results = []
        for user_id in user_ids:
            post_counts = await optimized_queries_with_delay.get_optimized_post_counts(user_id)
            message_counts = await optimized_queries_with_delay.get_optimized_message_counts(user_id)
            individual_results.append({
                'posts': post_counts,
                'messages': message_counts
            })
        individual_time = time.time() - start_individual
        
        # Clear performance log
        optimized_queries_with_delay.clear_performance_log()
        
        # Test batch query (optimized approach)
        start_batch = time.time()
        batch_results = await optimized_queries_with_delay.get_batch_user_activity_counts(user_ids)
        batch_time = time.time() - start_batch
        
        # Verify results are equivalent
        assert len(individual_results) == 20
        assert len(batch_results) == 20
        
        # Performance assertion: batch should be significantly faster
        assert batch_time < individual_time * 0.5  # At least 50% faster
        
        # Query count should be much lower for batch
        batch_metrics = optimized_queries_with_delay.get_performance_metrics()
        assert batch_metrics['total_queries'] == 2  # vs 40 for individual

    @pytest.mark.asyncio
    async def test_performance_monitoring_overhead(self, optimized_queries_with_delay):
        """Test that performance monitoring doesn't significantly impact performance."""
        user_id = uuid4()
        
        # Execute multiple queries to build performance log
        for _ in range(100):
            await optimized_queries_with_delay.get_optimized_post_counts(user_id)
        
        # Check that performance log doesn't grow excessively
        assert len(optimized_queries_with_delay.query_performance_log) == 100
        
        # Get metrics (this processes the entire log)
        start_metrics = time.time()
        metrics = optimized_queries_with_delay.get_performance_metrics()
        metrics_time = time.time() - start_metrics
        
        # Metrics calculation should be fast
        assert metrics_time < 0.01  # 10ms
        assert metrics['total_queries'] == 100

    @pytest.mark.asyncio
    async def test_scalability_linear_growth(self, optimized_queries_with_delay):
        """Test that performance scales linearly with user count for batch operations."""
        user_counts = [10, 50, 100, 200]
        execution_times = []
        
        for count in user_counts:
            user_ids = [uuid4() for _ in range(count)]
            
            # Clear performance log
            optimized_queries_with_delay.clear_performance_log()
            
            start_time = time.time()
            result = await optimized_queries_with_delay.get_batch_user_activity_counts(user_ids)
            execution_time = time.time() - start_time
            
            execution_times.append(execution_time)
            
            # Verify all users processed
            assert len(result) == count
            
            # Query count should remain constant
            metrics = optimized_queries_with_delay.get_performance_metrics()
            assert metrics['total_queries'] == 2
        
        # Performance should scale reasonably (not exponentially)
        # Each doubling of users should not more than double execution time
        for i in range(1, len(execution_times)):
            ratio = execution_times[i] / execution_times[i-1]
            user_ratio = user_counts[i] / user_counts[i-1]
            
            # Execution time growth should be less than or equal to user growth
            assert ratio <= user_ratio * 1.5  # Allow 50% overhead for scaling

    def test_performance_metrics_accuracy(self, optimized_queries_with_delay):
        """Test accuracy of performance metrics calculation."""
        # Add known performance data
        test_data = [
            {'query_name': 'test_query', 'execution_time_ms': 100, 'timestamp': datetime.now()},
            {'query_name': 'test_query', 'execution_time_ms': 200, 'timestamp': datetime.now()},
            {'query_name': 'other_query', 'execution_time_ms': 50, 'timestamp': datetime.now()},
        ]
        
        optimized_queries_with_delay.query_performance_log = test_data
        
        metrics = optimized_queries_with_delay.get_performance_metrics()
        
        # Verify calculations
        assert metrics['total_queries'] == 3
        assert metrics['average_execution_time_ms'] == 116.67  # (100+200+50)/3
        assert metrics['slow_queries_count'] == 1  # Only 200ms query (>100ms threshold)
        
        # Verify query type aggregation
        assert metrics['queries_by_type']['test_query']['count'] == 2
        assert metrics['queries_by_type']['test_query']['avg_time_ms'] == 150.0  # (100+200)/2
        assert metrics['queries_by_type']['other_query']['count'] == 1
        assert metrics['queries_by_type']['other_query']['avg_time_ms'] == 50.0
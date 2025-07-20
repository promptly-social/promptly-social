"""
Tests for the advanced batch processor and performance optimization.

This module tests adaptive batching strategies, parallel processing,
memory monitoring, timeout handling, and graceful shutdown functionality.

Requirements tested:
- 1.3: Efficient user batching strategies and timeout handling
- 8.4: Memory and execution time monitoring
- 10.1, 10.2: Performance optimization and validation
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from batch_processor import (
    MemoryMonitor,
    AdaptiveBatchProcessor,
    GracefulShutdownHandler,
    BatchMetrics,
    PerformanceThresholds,
    AnalysisStatus,
    UserAnalysisResult
)


class TestMemoryMonitor:
    """Test memory monitoring functionality."""
    
    def test_memory_monitor_initialization(self):
        """Test memory monitor initialization."""
        monitor = MemoryMonitor()
        
        assert monitor.peak_memory_mb == 0.0
        assert monitor.memory_samples == []
        assert not monitor._monitoring
    
    def test_get_current_memory_mb(self):
        """Test getting current memory usage."""
        monitor = MemoryMonitor()
        
        memory_mb = monitor.get_current_memory_mb()
        
        assert isinstance(memory_mb, float)
        assert memory_mb > 0
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping memory monitoring."""
        monitor = MemoryMonitor()
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor._monitoring
        assert monitor._monitor_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor._monitoring
    
    def test_get_peak_memory_mb(self):
        """Test getting peak memory usage."""
        monitor = MemoryMonitor()
        
        # Initially should be 0
        assert monitor.get_peak_memory_mb() == 0.0
        
        # Set a peak value
        monitor.peak_memory_mb = 100.0
        assert monitor.get_peak_memory_mb() == 100.0
    
    def test_get_average_memory_mb_empty(self):
        """Test getting average memory with no samples."""
        monitor = MemoryMonitor()
        
        # Should return current memory when no samples
        avg_memory = monitor.get_average_memory_mb()
        current_memory = monitor.get_current_memory_mb()
        
        assert avg_memory == current_memory
    
    def test_get_average_memory_mb_with_samples(self):
        """Test getting average memory with samples."""
        monitor = MemoryMonitor()
        
        # Add some sample data
        current_time = time.time()
        monitor.memory_samples = [
            {'timestamp': current_time - 10, 'memory_mb': 100.0},
            {'timestamp': current_time - 5, 'memory_mb': 150.0},
            {'timestamp': current_time - 1, 'memory_mb': 200.0}
        ]
        
        avg_memory = monitor.get_average_memory_mb()
        expected_avg = (100.0 + 150.0 + 200.0) / 3
        
        assert avg_memory == expected_avg


class TestAdaptiveBatchProcessor:
    """Test adaptive batch processing functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create a test batch processor."""
        return AdaptiveBatchProcessor(
            initial_batch_size=10,
            max_batch_size=50,
            min_batch_size=5,
            initial_concurrency=2,
            max_concurrency=5
        )
    
    @pytest.fixture
    def sample_users(self):
        """Create sample user data."""
        return [
            {'user_id': uuid4(), 'email': f'user{i}@example.com'}
            for i in range(25)
        ]
    
    def test_processor_initialization(self, processor):
        """Test processor initialization."""
        assert processor.current_batch_size == 10
        assert processor.max_batch_size == 50
        assert processor.min_batch_size == 5
        assert processor.current_concurrency == 2
        assert processor.max_concurrency == 5
        assert not processor.shutdown_requested
        assert processor.total_users_processed == 0
    
    def test_create_adaptive_batches(self, processor, sample_users):
        """Test creating adaptive batches."""
        batches = processor._create_adaptive_batches(sample_users)
        
        # Should create 3 batches: 10, 10, 5
        assert len(batches) == 3
        assert len(batches[0]) == 10
        assert len(batches[1]) == 10
        assert len(batches[2]) == 5
        
        # All users should be included
        all_batch_users = []
        for batch in batches:
            all_batch_users.extend(batch)
        
        assert len(all_batch_users) == len(sample_users)
    
    def test_create_adaptive_batches_empty(self, processor):
        """Test creating batches with empty user list."""
        batches = processor._create_adaptive_batches([])
        
        assert batches == []
    
    def test_adjust_batch_size_insufficient_history(self, processor):
        """Test batch size adjustment with insufficient history."""
        original_size = processor.current_batch_size
        
        # Should not change with insufficient history
        processor._adjust_batch_size()
        
        assert processor.current_batch_size == original_size
    
    def test_adjust_batch_size_high_memory(self, processor):
        """Test batch size adjustment with high memory usage."""
        # Add mock batch history with high memory usage
        processor.batch_history = [
            BatchMetrics(
                batch_size=10,
                processing_time_seconds=10.0,
                memory_usage_mb=450.0,  # Above warning threshold
                peak_memory_mb=500.0,
                cpu_usage_percent=50.0,
                concurrent_tasks=2,
                throughput_users_per_second=1.0,
                success_rate=0.9
            ),
            BatchMetrics(
                batch_size=10,
                processing_time_seconds=10.0,
                memory_usage_mb=460.0,
                peak_memory_mb=500.0,
                cpu_usage_percent=50.0,
                concurrent_tasks=2,
                throughput_users_per_second=1.0,
                success_rate=0.9
            )
        ]
        
        original_size = processor.current_batch_size
        processor._adjust_batch_size()
        
        # Should reduce batch size due to high memory
        assert processor.current_batch_size < original_size
    
    def test_adjust_batch_size_good_performance(self, processor):
        """Test batch size adjustment with good performance."""
        # Add mock batch history with good performance
        processor.batch_history = [
            BatchMetrics(
                batch_size=10,
                processing_time_seconds=10.0,
                memory_usage_mb=200.0,  # Low memory usage
                peak_memory_mb=250.0,
                cpu_usage_percent=30.0,
                concurrent_tasks=2,
                throughput_users_per_second=2.0,  # Good throughput
                success_rate=0.95  # High success rate
            ),
            BatchMetrics(
                batch_size=10,
                processing_time_seconds=10.0,
                memory_usage_mb=210.0,
                peak_memory_mb=250.0,
                cpu_usage_percent=30.0,
                concurrent_tasks=2,
                throughput_users_per_second=2.0,
                success_rate=0.95
            )
        ]
        
        original_size = processor.current_batch_size
        processor._adjust_batch_size()
        
        # Should increase batch size due to good performance
        assert processor.current_batch_size > original_size
    
    def test_adjust_concurrency_high_memory(self, processor):
        """Test concurrency adjustment with high memory usage."""
        original_concurrency = processor.current_concurrency
        
        processor._adjust_concurrency(450.0, 1.0)  # High memory, normal throughput
        
        # Should reduce concurrency
        assert processor.current_concurrency < original_concurrency
    
    def test_adjust_concurrency_good_performance(self, processor):
        """Test concurrency adjustment with good performance."""
        original_concurrency = processor.current_concurrency
        
        processor._adjust_concurrency(200.0, 2.0)  # Low memory, good throughput
        
        # Should increase concurrency
        assert processor.current_concurrency > original_concurrency
    
    @pytest.mark.asyncio
    async def test_process_users_adaptively_empty(self, processor):
        """Test processing empty user list."""
        async def mock_process_function(batch):
            return []
        
        results = await processor.process_users_adaptively([], mock_process_function)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_process_users_adaptively_success(self, processor, sample_users):
        """Test successful adaptive processing."""
        async def mock_process_function(batch):
            # Simulate processing delay
            await asyncio.sleep(0.01)
            
            results = []
            for user in batch:
                result = UserAnalysisResult(
                    user_id=user['user_id'],
                    email=user['email'],
                    status=AnalysisStatus.SUCCESS,
                    analysis_types_performed=['writing_style'],
                    processing_time_seconds=0.01
                )
                results.append(result)
            return results
        
        results = await processor.process_users_adaptively(
            sample_users[:10],  # Use smaller subset for faster test
            mock_process_function,
            timeout_seconds=30
        )
        
        assert len(results) == 10
        assert all(r.status == AnalysisStatus.SUCCESS for r in results)
        assert processor.successful_batches > 0
    
    @pytest.mark.asyncio
    async def test_process_users_adaptively_timeout(self, processor, sample_users):
        """Test processing with timeout."""
        async def slow_process_function(batch):
            # Simulate slow processing
            await asyncio.sleep(2)
            return []
        
        results = await processor.process_users_adaptively(
            sample_users[:5],
            slow_process_function,
            timeout_seconds=0.1  # Very short timeout
        )
        
        # Should return timeout results
        assert len(results) == 5
        assert all(r.status == AnalysisStatus.TIMEOUT for r in results)
        assert processor.shutdown_requested
    
    @pytest.mark.asyncio
    async def test_process_single_batch_with_monitoring_success(self, processor, sample_users):
        """Test processing single batch with monitoring."""
        async def mock_process_function(batch):
            results = []
            for user in batch:
                result = UserAnalysisResult(
                    user_id=user['user_id'],
                    email=user['email'],
                    status=AnalysisStatus.SUCCESS,
                    analysis_types_performed=['writing_style'],
                    processing_time_seconds=0.01
                )
                results.append(result)
            return results
        
        semaphore = asyncio.Semaphore(1)
        batch = sample_users[:5]
        
        results = await processor._process_single_batch_with_monitoring(
            batch, mock_process_function, semaphore, 0
        )
        
        assert len(results) == 5
        assert all(r.status == AnalysisStatus.SUCCESS for r in results)
        assert len(processor.batch_history) == 1
        
        # Check batch metrics
        metrics = processor.batch_history[0]
        assert metrics.batch_size == 5
        assert metrics.processing_time_seconds > 0
        assert metrics.memory_usage_mb > 0
        # Success rate should be close to 1.0 (allowing for small floating point differences)
        assert abs(metrics.success_rate - 1.0) < 0.01
    
    @pytest.mark.asyncio
    async def test_process_single_batch_with_monitoring_error(self, processor, sample_users):
        """Test processing single batch with error."""
        async def failing_process_function(batch):
            raise Exception("Processing failed")
        
        semaphore = asyncio.Semaphore(1)
        batch = sample_users[:3]
        
        results = await processor._process_single_batch_with_monitoring(
            batch, failing_process_function, semaphore, 0
        )
        
        assert len(results) == 3
        assert all(r.status == AnalysisStatus.FAILED for r in results)
        assert all("Processing failed" in r.error_message for r in results)
    
    @pytest.mark.asyncio
    async def test_process_single_batch_shutdown_requested(self, processor, sample_users):
        """Test processing single batch when shutdown is requested."""
        processor.shutdown_requested = True
        
        async def mock_process_function(batch):
            return []
        
        semaphore = asyncio.Semaphore(1)
        batch = sample_users[:3]
        
        results = await processor._process_single_batch_with_monitoring(
            batch, mock_process_function, semaphore, 0
        )
        
        assert results == []
    
    def test_check_performance_warnings(self, processor):
        """Test performance warning detection."""
        # Create metrics with various warning conditions
        high_memory_metrics = BatchMetrics(
            batch_size=10,
            processing_time_seconds=10.0,
            memory_usage_mb=450.0,  # Above warning threshold
            peak_memory_mb=500.0,
            cpu_usage_percent=50.0,
            concurrent_tasks=2,
            throughput_users_per_second=1.0,
            success_rate=0.9
        )
        
        high_cpu_metrics = BatchMetrics(
            batch_size=10,
            processing_time_seconds=10.0,
            memory_usage_mb=200.0,
            peak_memory_mb=250.0,
            cpu_usage_percent=85.0,  # Above CPU threshold
            concurrent_tasks=2,
            throughput_users_per_second=1.0,
            success_rate=0.9
        )
        
        low_throughput_metrics = BatchMetrics(
            batch_size=10,
            processing_time_seconds=10.0,
            memory_usage_mb=200.0,
            peak_memory_mb=250.0,
            cpu_usage_percent=50.0,
            concurrent_tasks=2,
            throughput_users_per_second=0.1,  # Below threshold
            success_rate=0.9
        )
        
        low_success_metrics = BatchMetrics(
            batch_size=10,
            processing_time_seconds=10.0,
            memory_usage_mb=200.0,
            peak_memory_mb=250.0,
            cpu_usage_percent=50.0,
            concurrent_tasks=2,
            throughput_users_per_second=1.0,
            success_rate=0.7  # Below threshold
        )
        
        # Test each warning condition (these should log warnings)
        with patch('batch_processor.logger') as mock_logger:
            processor._check_performance_warnings(high_memory_metrics, 0)
            mock_logger.warning.assert_called()
            
            processor._check_performance_warnings(high_cpu_metrics, 1)
            mock_logger.warning.assert_called()
            
            processor._check_performance_warnings(low_throughput_metrics, 2)
            mock_logger.warning.assert_called()
            
            processor._check_performance_warnings(low_success_metrics, 3)
            mock_logger.warning.assert_called()
    
    def test_get_performance_metrics_empty(self, processor):
        """Test getting performance metrics with no history."""
        metrics = processor.get_performance_metrics()
        
        assert metrics == {}
    
    def test_get_performance_metrics_with_history(self, processor):
        """Test getting performance metrics with history."""
        # Add some batch history
        processor.batch_history = [
            BatchMetrics(
                batch_size=10,
                processing_time_seconds=10.0,
                memory_usage_mb=200.0,
                peak_memory_mb=250.0,
                cpu_usage_percent=50.0,
                concurrent_tasks=2,
                throughput_users_per_second=1.0,
                success_rate=0.9
            )
        ]
        processor.successful_batches = 1
        processor.failed_batches = 0
        
        metrics = processor.get_performance_metrics()
        
        assert metrics['current_batch_size'] == processor.current_batch_size
        assert metrics['current_concurrency'] == processor.current_concurrency
        assert metrics['total_batches_processed'] == 1
        assert metrics['successful_batches'] == 1
        assert metrics['failed_batches'] == 0
        assert 'avg_memory_usage_mb' in metrics
        assert 'peak_memory_mb' in metrics
        assert 'avg_throughput_users_per_second' in metrics
        assert 'avg_success_rate' in metrics
        assert 'current_memory_mb' in metrics
    
    def test_request_shutdown(self, processor):
        """Test requesting shutdown."""
        assert not processor.shutdown_requested
        
        processor.request_shutdown()
        
        assert processor.shutdown_requested


class TestGracefulShutdownHandler:
    """Test graceful shutdown handling."""
    
    @pytest.fixture
    def shutdown_handler(self):
        """Create a test shutdown handler."""
        return GracefulShutdownHandler()
    
    def test_shutdown_handler_initialization(self, shutdown_handler):
        """Test shutdown handler initialization."""
        assert not shutdown_handler.shutdown_event.is_set()
        assert shutdown_handler.active_tasks == []
        assert shutdown_handler.cleanup_callbacks == []
    
    def test_register_task(self, shutdown_handler):
        """Test registering a task."""
        mock_task = Mock()
        
        shutdown_handler.register_task(mock_task)
        
        assert mock_task in shutdown_handler.active_tasks
    
    def test_register_cleanup_callback(self, shutdown_handler):
        """Test registering a cleanup callback."""
        mock_callback = Mock()
        
        shutdown_handler.register_cleanup_callback(mock_callback)
        
        assert mock_callback in shutdown_handler.cleanup_callbacks
    
    @pytest.mark.asyncio
    async def test_shutdown_no_tasks(self, shutdown_handler):
        """Test shutdown with no active tasks."""
        # Should complete quickly with no tasks
        await shutdown_handler.shutdown(timeout_seconds=1)
        
        assert shutdown_handler.shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_tasks(self, shutdown_handler):
        """Test shutdown with active tasks."""
        # Create mock tasks
        task1 = AsyncMock()
        task2 = AsyncMock()
        task1.done.return_value = True
        task2.done.return_value = True
        
        shutdown_handler.register_task(task1)
        shutdown_handler.register_task(task2)
        
        with patch('asyncio.gather', new_callable=AsyncMock) as mock_gather:
            mock_gather.return_value = []
            
            await shutdown_handler.shutdown(timeout_seconds=1)
            
            assert shutdown_handler.shutdown_event.is_set()
            mock_gather.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_cleanup_callbacks(self, shutdown_handler):
        """Test shutdown with cleanup callbacks."""
        sync_callback = Mock()
        async_callback = AsyncMock()
        
        shutdown_handler.register_cleanup_callback(sync_callback)
        shutdown_handler.register_cleanup_callback(async_callback)
        
        await shutdown_handler.shutdown(timeout_seconds=1)
        
        sync_callback.assert_called_once()
        async_callback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_callback_error(self, shutdown_handler):
        """Test shutdown with callback error."""
        def failing_callback():
            raise Exception("Cleanup failed")
        
        shutdown_handler.register_cleanup_callback(failing_callback)
        
        # Should not raise exception even if callback fails
        await shutdown_handler.shutdown(timeout_seconds=1)
        
        assert shutdown_handler.shutdown_event.is_set()
    
    def test_is_shutdown_requested(self, shutdown_handler):
        """Test checking if shutdown is requested."""
        assert not shutdown_handler.is_shutdown_requested()
        
        shutdown_handler.shutdown_event.set()
        
        assert shutdown_handler.is_shutdown_requested()


class TestPerformanceThresholds:
    """Test performance thresholds configuration."""
    
    def test_default_thresholds(self):
        """Test default performance thresholds."""
        thresholds = PerformanceThresholds()
        
        assert thresholds.max_memory_mb == 512
        assert thresholds.max_cpu_percent == 80.0
        assert thresholds.max_concurrent_tasks == 10
        assert thresholds.min_throughput_users_per_second == 0.5
        assert thresholds.memory_warning_threshold_mb == 400
    
    def test_custom_thresholds(self):
        """Test custom performance thresholds."""
        thresholds = PerformanceThresholds(
            max_memory_mb=1024,
            max_cpu_percent=90.0,
            max_concurrent_tasks=20,
            min_throughput_users_per_second=1.0,
            memory_warning_threshold_mb=800
        )
        
        assert thresholds.max_memory_mb == 1024
        assert thresholds.max_cpu_percent == 90.0
        assert thresholds.max_concurrent_tasks == 20
        assert thresholds.min_throughput_users_per_second == 1.0
        assert thresholds.memory_warning_threshold_mb == 800


if __name__ == "__main__":
    pytest.main([__file__])
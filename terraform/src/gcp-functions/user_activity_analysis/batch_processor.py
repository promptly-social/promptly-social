"""
Advanced batch processing and performance optimization for user activity analysis.

This module provides enhanced batch processing strategies, parallel processing
for independent users, memory and execution time monitoring, timeout handling,
and graceful shutdown capabilities.

Requirements implemented:
- 1.3: Efficient user batching strategies and timeout handling
- 8.4: Memory and execution time monitoring
- 10.1, 10.2: Performance optimization and validation
"""

import asyncio
import logging
import time
import gc
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor
import threading

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    # Mock psutil for environments where it's not available
    class MockProcess:
        def memory_info(self):
            return type('MemoryInfo', (), {'rss': 100 * 1024 * 1024})()  # 100MB mock
    
    class MockPsutil:
        def Process(self):
            return MockProcess()
        
        def cpu_percent(self):
            return 50.0  # Mock CPU usage
    
    psutil = MockPsutil()

# Define required types for standalone usage
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class AnalysisStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

@dataclass
class UserAnalysisResult:
    user_id: UUID
    email: str
    status: AnalysisStatus
    analysis_types_performed: List[str]
    processing_time_seconds: float
    error_message: Optional[str] = None
    activity_counts: Optional[dict] = None
    analysis_scope: Optional[dict] = None

logger = logging.getLogger(__name__)


@dataclass
class BatchMetrics:
    """Metrics for batch processing performance."""
    batch_size: int
    processing_time_seconds: float
    memory_usage_mb: float
    peak_memory_mb: float
    cpu_usage_percent: float
    concurrent_tasks: int
    throughput_users_per_second: float
    success_rate: float


@dataclass
class PerformanceThresholds:
    """Performance thresholds for optimization."""
    max_memory_mb: int = 512
    max_cpu_percent: float = 80.0
    max_concurrent_tasks: int = 10
    min_throughput_users_per_second: float = 0.5
    memory_warning_threshold_mb: int = 400


class MemoryMonitor:
    """Monitor memory usage during batch processing."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.peak_memory_mb = 0.0
        self.memory_samples = []
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    def start_monitoring(self):
        """Start continuous memory monitoring."""
        if not self._monitoring:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_memory())
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
    
    async def _monitor_memory(self):
        """Continuously monitor memory usage."""
        try:
            while self._monitoring:
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                self.memory_samples.append({
                    'timestamp': time.time(),
                    'memory_mb': memory_mb
                })
                
                if memory_mb > self.peak_memory_mb:
                    self.peak_memory_mb = memory_mb
                
                # Keep only recent samples (last 60 seconds)
                cutoff_time = time.time() - 60
                self.memory_samples = [
                    sample for sample in self.memory_samples 
                    if sample['timestamp'] > cutoff_time
                ]
                
                await asyncio.sleep(1)  # Sample every second
                
        except asyncio.CancelledError:
            pass
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        memory_info = self.process.memory_info()
        return memory_info.rss / 1024 / 1024
    
    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        return self.peak_memory_mb
    
    def get_average_memory_mb(self) -> float:
        """Get average memory usage over recent samples."""
        if not self.memory_samples:
            return self.get_current_memory_mb()
        
        total_memory = sum(sample['memory_mb'] for sample in self.memory_samples)
        return total_memory / len(self.memory_samples)


class AdaptiveBatchProcessor:
    """
    Advanced batch processor with adaptive sizing and performance optimization.
    
    This processor dynamically adjusts batch sizes and concurrency based on
    system performance, memory usage, and processing throughput.
    
    Requirements implemented:
    - 1.3: Efficient user batching strategies
    - 8.4: Memory and execution time monitoring
    - 10.1, 10.2: Performance optimization
    """
    
    def __init__(
        self,
        initial_batch_size: int = 50,
        max_batch_size: int = 200,
        min_batch_size: int = 10,
        initial_concurrency: int = 5,
        max_concurrency: int = 15,
        performance_thresholds: Optional[PerformanceThresholds] = None
    ):
        """
        Initialize the adaptive batch processor.
        
        Args:
            initial_batch_size: Starting batch size
            max_batch_size: Maximum allowed batch size
            min_batch_size: Minimum allowed batch size
            initial_concurrency: Starting concurrency level
            max_concurrency: Maximum allowed concurrency
            performance_thresholds: Performance thresholds for optimization
        """
        self.current_batch_size = initial_batch_size
        self.max_batch_size = max_batch_size
        self.min_batch_size = min_batch_size
        self.current_concurrency = initial_concurrency
        self.max_concurrency = max_concurrency
        self.thresholds = performance_thresholds or PerformanceThresholds()
        
        self.memory_monitor = MemoryMonitor()
        self.batch_history: List[BatchMetrics] = []
        self.shutdown_requested = False
        
        # Performance tracking
        self.total_users_processed = 0
        self.total_processing_time = 0.0
        self.successful_batches = 0
        self.failed_batches = 0
    
    async def process_users_adaptively(
        self,
        users: List[Dict[str, Any]],
        process_function: Callable[[List[Dict[str, Any]]], List[UserAnalysisResult]],
        timeout_seconds: int = 900  # 15 minutes
    ) -> List[UserAnalysisResult]:
        """
        Process users with adaptive batching and performance optimization.
        
        Args:
            users: List of users to process
            process_function: Function to process each batch
            timeout_seconds: Maximum processing time
            
        Returns:
            List of UserAnalysisResult objects
            
        Requirements: 1.3, 8.4, 10.1, 10.2
        """
        if not users:
            return []
        
        logger.info(f"Starting adaptive batch processing for {len(users)} users")
        
        # Start monitoring
        self.memory_monitor.start_monitoring()
        start_time = time.time()
        all_results = []
        
        try:
            # Create batches
            batches = self._create_adaptive_batches(users)
            logger.info(f"Created {len(batches)} batches with sizes: {[len(batch) for batch in batches]}")
            
            # Process batches with timeout
            batch_tasks = []
            semaphore = asyncio.Semaphore(self.current_concurrency)
            
            for i, batch in enumerate(batches):
                task = asyncio.create_task(
                    self._process_single_batch_with_monitoring(
                        batch, process_function, semaphore, i
                    )
                )
                batch_tasks.append(task)
            
            # Wait for all batches with timeout
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*batch_tasks, return_exceptions=True),
                    timeout=timeout_seconds
                )
                
                # Collect results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error: {result}")
                        self.failed_batches += 1
                    elif isinstance(result, list):
                        all_results.extend(result)
                        self.successful_batches += 1
                
            except asyncio.TimeoutError:
                logger.error(f"Batch processing timed out after {timeout_seconds} seconds")
                self.shutdown_requested = True
                
                # Cancel remaining tasks
                for task in batch_tasks:
                    if not task.done():
                        task.cancel()
                
                # Wait a bit for cancellation to complete
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*batch_tasks, return_exceptions=True),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    pass  # Some tasks may not cancel cleanly
                
                # Create timeout results for all users if no results yet
                if not all_results:
                    for user in users:
                        timeout_result = UserAnalysisResult(
                            user_id=user['user_id'],
                            email=user['email'],
                            status=AnalysisStatus.TIMEOUT,
                            analysis_types_performed=[],
                            processing_time_seconds=timeout_seconds,
                            error_message="Batch processing timed out"
                        )
                        all_results.append(timeout_result)
                else:
                    # Create timeout results for unprocessed users
                    processed_user_ids = {result.user_id for result in all_results}
                    for user in users:
                        if user['user_id'] not in processed_user_ids:
                            timeout_result = UserAnalysisResult(
                                user_id=user['user_id'],
                                email=user['email'],
                                status=AnalysisStatus.TIMEOUT,
                                analysis_types_performed=[],
                                processing_time_seconds=timeout_seconds,
                                error_message="Batch processing timed out"
                            )
                            all_results.append(timeout_result)
            
            # Log final performance summary
            total_time = time.time() - start_time
            self._log_performance_summary(len(users), len(all_results), total_time)
            
            return all_results
            
        finally:
            self.memory_monitor.stop_monitoring()
    
    def _create_adaptive_batches(self, users: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Create batches with adaptive sizing based on performance history.
        
        Args:
            users: List of users to batch
            
        Returns:
            List of user batches
        """
        # Adjust batch size based on recent performance
        self._adjust_batch_size()
        
        batches = []
        current_batch = []
        
        for user in users:
            current_batch.append(user)
            
            if len(current_batch) >= self.current_batch_size:
                batches.append(current_batch)
                current_batch = []
        
        # Add remaining users as final batch
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _adjust_batch_size(self):
        """Adjust batch size based on performance history."""
        if len(self.batch_history) < 2:
            return
        
        # Get recent performance metrics
        recent_metrics = self.batch_history[-3:]  # Last 3 batches
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        avg_throughput = sum(m.throughput_users_per_second for m in recent_metrics) / len(recent_metrics)
        avg_success_rate = sum(m.success_rate for m in recent_metrics) / len(recent_metrics)
        
        # Adjust based on memory usage
        if avg_memory > self.thresholds.memory_warning_threshold_mb:
            self.current_batch_size = max(
                self.min_batch_size,
                int(self.current_batch_size * 0.8)
            )
            logger.info(f"Reduced batch size to {self.current_batch_size} due to high memory usage")
        
        # Adjust based on throughput and success rate
        elif avg_throughput > self.thresholds.min_throughput_users_per_second and avg_success_rate > 0.9:
            self.current_batch_size = min(
                self.max_batch_size,
                int(self.current_batch_size * 1.2)
            )
            logger.info(f"Increased batch size to {self.current_batch_size} due to good performance")
        
        # Adjust concurrency
        self._adjust_concurrency(avg_memory, avg_throughput)
    
    def _adjust_concurrency(self, avg_memory: float, avg_throughput: float):
        """Adjust concurrency level based on performance."""
        if avg_memory > self.thresholds.memory_warning_threshold_mb:
            self.current_concurrency = max(1, self.current_concurrency - 1)
            logger.info(f"Reduced concurrency to {self.current_concurrency} due to high memory usage")
        elif avg_throughput > self.thresholds.min_throughput_users_per_second and avg_memory < self.thresholds.max_memory_mb * 0.7:
            self.current_concurrency = min(self.max_concurrency, self.current_concurrency + 1)
            logger.info(f"Increased concurrency to {self.current_concurrency} due to good performance")
    
    async def _process_single_batch_with_monitoring(
        self,
        batch: List[Dict[str, Any]],
        process_function: Callable,
        semaphore: asyncio.Semaphore,
        batch_index: int
    ) -> List[UserAnalysisResult]:
        """
        Process a single batch with performance monitoring.
        
        Args:
            batch: Batch of users to process
            process_function: Function to process the batch
            semaphore: Concurrency control semaphore
            batch_index: Index of this batch
            
        Returns:
            List of UserAnalysisResult objects
        """
        async with semaphore:
            if self.shutdown_requested:
                logger.info(f"Skipping batch {batch_index} due to shutdown request")
                return []
            
            batch_start_time = time.time()
            start_memory = self.memory_monitor.get_current_memory_mb()
            
            logger.info(f"Processing batch {batch_index} with {len(batch)} users")
            
            try:
                # Force garbage collection before processing
                gc.collect()
                
                # Process the batch
                results = await process_function(batch)
                
                # Calculate metrics
                processing_time = time.time() - batch_start_time
                end_memory = self.memory_monitor.get_current_memory_mb()
                peak_memory = self.memory_monitor.get_peak_memory_mb()
                
                # Calculate success rate
                successful_results = sum(1 for r in results if r.status == AnalysisStatus.SUCCESS)
                success_rate = successful_results / len(batch) if batch else 0.0
                
                # Create batch metrics
                metrics = BatchMetrics(
                    batch_size=len(batch),
                    processing_time_seconds=processing_time,
                    memory_usage_mb=end_memory,
                    peak_memory_mb=peak_memory,
                    cpu_usage_percent=psutil.cpu_percent(),
                    concurrent_tasks=self.current_concurrency,
                    throughput_users_per_second=len(batch) / processing_time if processing_time > 0 else 0,
                    success_rate=success_rate
                )
                
                self.batch_history.append(metrics)
                
                # Log batch completion
                logger.info(
                    f"Batch {batch_index} completed: {len(results)} results, "
                    f"{processing_time:.2f}s, {end_memory:.1f}MB memory, "
                    f"{metrics.throughput_users_per_second:.2f} users/sec"
                )
                
                # Check for performance warnings
                self._check_performance_warnings(metrics, batch_index)
                
                return results
                
            except Exception as e:
                processing_time = time.time() - batch_start_time
                logger.error(f"Error processing batch {batch_index}: {e}", exc_info=True)
                
                # Create failed results for all users in batch
                failed_results = []
                for user in batch:
                    failed_result = UserAnalysisResult(
                        user_id=user['user_id'],
                        email=user['email'],
                        status=AnalysisStatus.FAILED,
                        analysis_types_performed=[],
                        processing_time_seconds=processing_time,
                        error_message=f"Batch processing error: {str(e)}"
                    )
                    failed_results.append(failed_result)
                
                return failed_results
    
    def _check_performance_warnings(self, metrics: BatchMetrics, batch_index: int):
        """Check for performance warnings and log them."""
        warnings = []
        
        if metrics.memory_usage_mb > self.thresholds.memory_warning_threshold_mb:
            warnings.append(f"High memory usage: {metrics.memory_usage_mb:.1f}MB")
        
        if metrics.cpu_usage_percent > self.thresholds.max_cpu_percent:
            warnings.append(f"High CPU usage: {metrics.cpu_usage_percent:.1f}%")
        
        if metrics.throughput_users_per_second < self.thresholds.min_throughput_users_per_second:
            warnings.append(f"Low throughput: {metrics.throughput_users_per_second:.2f} users/sec")
        
        if metrics.success_rate < 0.8:
            warnings.append(f"Low success rate: {metrics.success_rate:.1%}")
        
        if warnings:
            logger.warning(f"Performance warnings for batch {batch_index}: {'; '.join(warnings)}")
    
    def _log_performance_summary(self, total_users: int, results_count: int, total_time: float):
        """Log comprehensive performance summary."""
        if not self.batch_history:
            return
        
        # Calculate aggregate metrics
        avg_memory = sum(m.memory_usage_mb for m in self.batch_history) / len(self.batch_history)
        peak_memory = max(m.peak_memory_mb for m in self.batch_history)
        avg_throughput = sum(m.throughput_users_per_second for m in self.batch_history) / len(self.batch_history)
        overall_success_rate = results_count / total_users if total_users > 0 else 0.0
        
        logger.info(
            f"Adaptive batch processing completed: "
            f"{results_count}/{total_users} users processed in {total_time:.2f}s. "
            f"Avg memory: {avg_memory:.1f}MB, Peak: {peak_memory:.1f}MB, "
            f"Avg throughput: {avg_throughput:.2f} users/sec, "
            f"Success rate: {overall_success_rate:.1%}, "
            f"Batches: {self.successful_batches} successful, {self.failed_batches} failed"
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if not self.batch_history:
            return {}
        
        recent_metrics = self.batch_history[-5:]  # Last 5 batches
        
        return {
            'current_batch_size': self.current_batch_size,
            'current_concurrency': self.current_concurrency,
            'total_batches_processed': len(self.batch_history),
            'successful_batches': self.successful_batches,
            'failed_batches': self.failed_batches,
            'avg_memory_usage_mb': sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics),
            'peak_memory_mb': max(m.peak_memory_mb for m in recent_metrics),
            'avg_throughput_users_per_second': sum(m.throughput_users_per_second for m in recent_metrics) / len(recent_metrics),
            'avg_success_rate': sum(m.success_rate for m in recent_metrics) / len(recent_metrics),
            'current_memory_mb': self.memory_monitor.get_current_memory_mb()
        }
    
    def request_shutdown(self):
        """Request graceful shutdown of batch processing."""
        self.shutdown_requested = True
        logger.info("Graceful shutdown requested for batch processor")


class GracefulShutdownHandler:
    """
    Handle graceful shutdown of batch processing operations.
    
    This handler ensures that ongoing operations complete properly
    and resources are cleaned up during shutdown.
    """
    
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.active_tasks: List[asyncio.Task] = []
        self.cleanup_callbacks: List[Callable] = []
    
    def register_task(self, task: asyncio.Task):
        """Register a task for graceful shutdown."""
        self.active_tasks.append(task)
    
    def register_cleanup_callback(self, callback: Callable):
        """Register a cleanup callback."""
        self.cleanup_callbacks.append(callback)
    
    async def shutdown(self, timeout_seconds: int = 30):
        """
        Perform graceful shutdown.
        
        Args:
            timeout_seconds: Maximum time to wait for tasks to complete
        """
        logger.info("Starting graceful shutdown...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Wait for active tasks to complete
        if self.active_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_tasks, return_exceptions=True),
                    timeout=timeout_seconds
                )
                logger.info("All tasks completed successfully")
            except asyncio.TimeoutError:
                logger.warning(f"Some tasks did not complete within {timeout_seconds}s, cancelling...")
                for task in self.active_tasks:
                    if not task.done():
                        task.cancel()
        
        # Run cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in cleanup callback: {e}")
        
        logger.info("Graceful shutdown completed")
    
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        return self.shutdown_event.is_set()
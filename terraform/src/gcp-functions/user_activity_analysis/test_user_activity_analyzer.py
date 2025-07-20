"""
Integration tests for UserActivityAnalyzer orchestrator class.

Tests the complete analysis workflow coordination, user batch processing,
error isolation, logging, and result aggregation.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from .user_activity_analyzer import (
    UserActivityAnalyzer,
    AnalysisStatus,
    UserAnalysisResult,
    BatchAnalysisResult
)
from .activity_threshold_checker import ActivityThresholdChecker
from .analysis_state_manager import AnalysisStateManager
from .ai_service_factory import AIAnalysisService


class TestUserActivityAnalyzer:
    """Test cases for UserActivityAnalyzer orchestrator."""

    @pytest.fixture
    def mock_db_client(self):
        """Mock database client."""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI analysis service."""
        mock_service = AsyncMock(spec=AIAnalysisService)
        return mock_service

    @pytest.fixture
    def analyzer(self, mock_db_client, mock_ai_service):
        """Create UserActivityAnalyzer instance with mocked dependencies."""
        return UserActivityAnalyzer(
            db_client=mock_db_client,
            ai_service=mock_ai_service,
            post_threshold=5,
            message_threshold=10,
            batch_timeout_minutes=15
        )

    @pytest.fixture
    def sample_users_data(self):
        """Sample user data for testing."""
        return [
            {
                'user_id': uuid4(),
                'email': 'user1@example.com',
                'last_analysis_at': None,
                'post_count': 6,
                'message_count': 3,
                'needs_analysis': True
            },
            {
                'user_id': uuid4(),
                'email': 'user2@example.com',
                'last_analysis_at': datetime.now(timezone.utc) - timedelta(days=1),
                'post_count': 2,
                'message_count': 12,
                'needs_analysis': True
            },
            {
                'user_id': uuid4(),
                'email': 'user3@example.com',
                'last_analysis_at': datetime.now(timezone.utc) - timedelta(hours=2),
                'post_count': 8,
                'message_count': 15,
                'needs_analysis': True
            }
        ]

    @pytest.mark.asyncio
    async def test_analyze_user_activity_success(self, analyzer, sample_users_data):
        """Test successful complete analysis workflow."""
        # Mock the get_users_for_analysis method
        with patch.object(analyzer, 'get_users_for_analysis', return_value=sample_users_data):
            # Mock successful user analysis
            successful_results = []
            for user_data in sample_users_data:
                result = UserAnalysisResult(
                    user_id=user_data['user_id'],
                    email=user_data['email'],
                    status=AnalysisStatus.SUCCESS,
                    analysis_types_performed=['writing_style', 'topics_of_interest'],
                    processing_time_seconds=2.5,
                    activity_counts={'posts': user_data['post_count'], 'messages': user_data['message_count']}
                )
                successful_results.append(result)
            
            with patch.object(analyzer, 'process_user_batch', return_value=successful_results):
                result = await analyzer.analyze_user_activity()
                
                # Verify batch result structure
                assert isinstance(result, BatchAnalysisResult)
                assert result.total_users_processed == 3
                assert result.successful_analyses == 3
                assert result.failed_analyses == 0
                assert result.skipped_analyses == 0
                assert len(result.user_results) == 3
                
                # Verify timing information
                assert result.start_time is not None
                assert result.end_time is not None
                assert result.total_processing_time_seconds > 0
                
                # Verify error summary is empty for successful run
                assert result.error_summary == {}

    @pytest.mark.asyncio
    async def test_analyze_user_activity_no_users(self, analyzer):
        """Test analysis when no users need analysis."""
        with patch.object(analyzer, 'get_users_for_analysis', return_value=[]):
            result = await analyzer.analyze_user_activity()
            
            assert result.total_users_processed == 0
            assert result.successful_analyses == 0
            assert result.failed_analyses == 0
            assert result.skipped_analyses == 0
            assert len(result.user_results) == 0

    @pytest.mark.asyncio
    async def test_analyze_user_activity_with_failures(self, analyzer, sample_users_data):
        """Test analysis workflow with some user failures."""
        with patch.object(analyzer, 'get_users_for_analysis', return_value=sample_users_data):
            # Mock mixed results - some success, some failure
            mixed_results = [
                UserAnalysisResult(
                    user_id=sample_users_data[0]['user_id'],
                    email=sample_users_data[0]['email'],
                    status=AnalysisStatus.SUCCESS,
                    analysis_types_performed=['writing_style'],
                    processing_time_seconds=2.0
                ),
                UserAnalysisResult(
                    user_id=sample_users_data[1]['user_id'],
                    email=sample_users_data[1]['email'],
                    status=AnalysisStatus.FAILED,
                    analysis_types_performed=[],
                    processing_time_seconds=1.0,
                    error_message="AI service error"
                ),
                UserAnalysisResult(
                    user_id=sample_users_data[2]['user_id'],
                    email=sample_users_data[2]['email'],
                    status=AnalysisStatus.SUCCESS,
                    analysis_types_performed=['topics_of_interest', 'bio_update'],
                    processing_time_seconds=3.5
                )
            ]
            
            with patch.object(analyzer, 'process_user_batch', return_value=mixed_results):
                result = await analyzer.analyze_user_activity()
                
                assert result.total_users_processed == 3
                assert result.successful_analyses == 2
                assert result.failed_analyses == 1
                assert result.skipped_analyses == 0
                
                # Verify error summary
                assert 'ai_service_error' in result.error_summary
                assert result.error_summary['ai_service_error'] == 1

    @pytest.mark.asyncio
    async def test_get_users_for_analysis(self, analyzer):
        """Test getting users for analysis."""
        # Mock state manager response
        mock_users = [
            {
                'user_id': uuid4(),
                'email': 'test@example.com',
                'last_analysis_at': None,
                'post_count': 6,
                'message_count': 8,
                'needs_analysis': True
            }
        ]
        
        analyzer.state_manager.get_users_needing_analysis = AsyncMock(return_value=mock_users)
        
        result = await analyzer.get_users_for_analysis()
        
        assert len(result) == 1
        assert result[0]['email'] == 'test@example.com'
        
        # Verify state manager was called with correct thresholds
        analyzer.state_manager.get_users_needing_analysis.assert_called_once_with(5, 10)

    @pytest.mark.asyncio
    async def test_process_user_batch_error_isolation(self, analyzer, sample_users_data):
        """Test that user batch processing isolates errors properly."""
        # Mock analyze_single_user to return different results
        async def mock_analyze_single_user(user_data):
            if user_data['email'] == 'user2@example.com':
                # Simulate failure for second user
                return UserAnalysisResult(
                    user_id=user_data['user_id'],
                    email=user_data['email'],
                    status=AnalysisStatus.FAILED,
                    analysis_types_performed=[],
                    processing_time_seconds=1.0,
                    error_message="Database connection error"
                )
            else:
                # Success for other users
                return UserAnalysisResult(
                    user_id=user_data['user_id'],
                    email=user_data['email'],
                    status=AnalysisStatus.SUCCESS,
                    analysis_types_performed=['writing_style'],
                    processing_time_seconds=2.0
                )
        
        analyzer.analyze_single_user = mock_analyze_single_user
        
        results = await analyzer.process_user_batch(sample_users_data)
        
        # Verify all users were processed despite one failure
        assert len(results) == 3
        
        # Verify error isolation - other users succeeded
        successful_results = [r for r in results if r.status == AnalysisStatus.SUCCESS]
        failed_results = [r for r in results if r.status == AnalysisStatus.FAILED]
        
        assert len(successful_results) == 2
        assert len(failed_results) == 1
        assert failed_results[0].error_message == "Database connection error"

    @pytest.mark.asyncio
    async def test_process_with_timeout(self, analyzer, sample_users_data):
        """Test batch processing with timeout protection."""
        # Set a very short timeout for testing
        analyzer.batch_timeout_seconds = 0.1
        
        # Mock a slow process_user_batch
        async def slow_process_user_batch(users):
            await asyncio.sleep(0.2)  # Longer than timeout
            return []
        
        analyzer.process_user_batch = slow_process_user_batch
        
        results = await analyzer._process_with_timeout(sample_users_data)
        
        # Should return timeout results for all users
        assert len(results) == 3
        for result in results:
            assert result.status == AnalysisStatus.TIMEOUT
            assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_update_analysis_tracking(self, analyzer):
        """Test updating analysis tracking after successful analysis."""
        user_id = uuid4()
        analysis_data = {
            'analysis_scope': {
                'posts_analyzed': {'scheduled_count': 3, 'dismissed_count': 1},
                'messages_analyzed': {'total_count': 5},
                'analysis_types_performed': ['writing_style', 'topics_of_interest']
            },
            'last_post_id': uuid4(),
            'last_message_id': uuid4()
        }
        
        # Mock state manager
        analyzer.state_manager.record_analysis_completion = AsyncMock()
        
        await analyzer.update_analysis_tracking(user_id, analysis_data)
        
        # Verify state manager was called correctly
        analyzer.state_manager.record_analysis_completion.assert_called_once()
        call_args = analyzer.state_manager.record_analysis_completion.call_args
        
        assert call_args.kwargs['user_id'] == user_id
        assert call_args.kwargs['analysis_scope'] == analysis_data['analysis_scope']
        assert call_args.kwargs['last_post_id'] == analysis_data['last_post_id']
        assert call_args.kwargs['last_message_id'] == analysis_data['last_message_id']

    @pytest.mark.asyncio
    async def test_get_analysis_status_summary(self, analyzer):
        """Test getting analysis status summary."""
        # Mock state manager and threshold checker responses
        mock_progress = {
            'total_users': 100,
            'users_analyzed': 85,
            'users_never_analyzed': 15,
            'avg_hours_since_analysis': 12.5
        }
        
        mock_threshold_summary = {
            'total_users_needing_analysis': 25,
            'users_triggered_by_posts': 15,
            'users_triggered_by_messages': 18,
            'users_triggered_by_both': 8
        }
        
        analyzer.state_manager.get_analysis_progress_summary = AsyncMock(return_value=mock_progress)
        analyzer.threshold_checker.get_batch_analysis_summary = AsyncMock(return_value=mock_threshold_summary)
        
        summary = await analyzer.get_analysis_status_summary()
        
        assert 'analysis_progress' in summary
        assert 'threshold_analysis' in summary
        assert 'current_thresholds' in summary
        assert 'last_check_time' in summary
        
        assert summary['analysis_progress'] == mock_progress
        assert summary['threshold_analysis'] == mock_threshold_summary
        assert summary['current_thresholds']['post_threshold'] == 5
        assert summary['current_thresholds']['message_threshold'] == 10

    def test_generate_error_summary(self, analyzer):
        """Test error summary generation from batch results."""
        results = [
            UserAnalysisResult(
                user_id=uuid4(),
                email='user1@example.com',
                status=AnalysisStatus.SUCCESS,
                analysis_types_performed=['writing_style'],
                processing_time_seconds=2.0
            ),
            UserAnalysisResult(
                user_id=uuid4(),
                email='user2@example.com',
                status=AnalysisStatus.FAILED,
                analysis_types_performed=[],
                processing_time_seconds=1.0,
                error_message="AI service timeout error"
            ),
            UserAnalysisResult(
                user_id=uuid4(),
                email='user3@example.com',
                status=AnalysisStatus.FAILED,
                analysis_types_performed=[],
                processing_time_seconds=0.5,
                error_message="Database connection failed"
            ),
            UserAnalysisResult(
                user_id=uuid4(),
                email='user4@example.com',
                status=AnalysisStatus.FAILED,
                analysis_types_performed=[],
                processing_time_seconds=15.0,
                error_message="Processing timeout exceeded"
            )
        ]
        
        error_summary = analyzer._generate_error_summary(results)
        
        assert error_summary['ai_service_error'] == 1
        assert error_summary['database_error'] == 1
        assert error_summary['timeout_error'] == 1

    def test_get_batch_result_summary(self, analyzer):
        """Test batch result summary generation."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=30)
        
        user_results = [
            UserAnalysisResult(
                user_id=uuid4(),
                email='user1@example.com',
                status=AnalysisStatus.SUCCESS,
                analysis_types_performed=['writing_style', 'topics_of_interest'],
                processing_time_seconds=2.0
            ),
            UserAnalysisResult(
                user_id=uuid4(),
                email='user2@example.com',
                status=AnalysisStatus.SUCCESS,
                analysis_types_performed=['bio_update'],
                processing_time_seconds=1.5
            )
        ]
        
        batch_result = BatchAnalysisResult(
            total_users_processed=2,
            successful_analyses=2,
            failed_analyses=0,
            skipped_analyses=0,
            total_processing_time_seconds=30.0,
            start_time=start_time,
            end_time=end_time,
            user_results=user_results,
            error_summary={}
        )
        
        summary = analyzer.get_batch_result_summary(batch_result)
        
        assert summary['summary']['total_users_processed'] == 2
        assert summary['summary']['successful_analyses'] == 2
        assert summary['summary']['success_rate_percent'] == 100.0
        assert summary['summary']['average_processing_time_seconds'] == 15.0
        
        assert summary['timing']['duration_seconds'] == 30.0
        assert summary['errors'] == {}
        
        # Check analysis type summary
        assert summary['analysis_types_performed']['writing_style'] == 1
        assert summary['analysis_types_performed']['topics_of_interest'] == 1
        assert summary['analysis_types_performed']['bio_update'] == 1

    @pytest.mark.asyncio
    async def test_critical_error_handling(self, analyzer):
        """Test handling of critical errors in main workflow."""
        # Mock get_users_for_analysis to raise an exception
        with patch.object(analyzer, 'get_users_for_analysis', side_effect=Exception("Critical database error")):
            result = await analyzer.analyze_user_activity()
            
            # Should return partial results with error information
            assert result.total_users_processed == 0
            assert result.successful_analyses == 0
            assert result.failed_analyses == 0
            assert result.skipped_analyses == 0

    def test_threshold_configuration(self, mock_db_client, mock_ai_service):
        """Test threshold configuration in analyzer."""
        analyzer = UserActivityAnalyzer(
            db_client=mock_db_client,
            ai_service=mock_ai_service,
            post_threshold=8,
            message_threshold=15,
            batch_timeout_minutes=20
        )
        
        assert analyzer.post_threshold == 8
        assert analyzer.message_threshold == 15
        assert analyzer.batch_timeout_seconds == 1200  # 20 minutes
        
        # Verify thresholds were set on threshold checker
        thresholds = analyzer.threshold_checker.get_current_thresholds()
        assert thresholds['post_threshold'] == 8
        assert thresholds['message_threshold'] == 15

    @pytest.mark.asyncio
    async def test_concurrent_user_processing(self, analyzer, sample_users_data):
        """Test that users are processed concurrently with proper semaphore control."""
        processing_times = []
        
        async def mock_analyze_single_user(user_data):
            start_time = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # Simulate processing time
            end_time = asyncio.get_event_loop().time()
            processing_times.append((start_time, end_time))
            
            return UserAnalysisResult(
                user_id=user_data['user_id'],
                email=user_data['email'],
                status=AnalysisStatus.SUCCESS,
                analysis_types_performed=['writing_style'],
                processing_time_seconds=0.1
            )
        
        analyzer.analyze_single_user = mock_analyze_single_user
        
        start_time = asyncio.get_event_loop().time()
        results = await analyzer.process_user_batch(sample_users_data)
        total_time = asyncio.get_event_loop().time() - start_time
        
        # Verify all users were processed
        assert len(results) == 3
        
        # Verify concurrent processing (should be faster than sequential)
        # Sequential would take 0.3+ seconds, concurrent should be closer to 0.1
        assert total_time < 0.25  # Allow some overhead
        
        # Verify overlapping processing times (concurrent execution)
        assert len(processing_times) == 3
        overlapping_pairs = 0
        for i, (start1, end1) in enumerate(processing_times):
            for j, (start2, end2) in enumerate(processing_times[i+1:], i+1):
                if start1 < end2 and start2 < end1:  # Overlapping intervals
                    overlapping_pairs += 1
        
        assert overlapping_pairs > 0  # At least some processing should overlap


class TestUserAnalysisResult:
    """Test cases for UserAnalysisResult dataclass."""

    def test_user_analysis_result_creation(self):
        """Test creating UserAnalysisResult with all fields."""
        user_id = uuid4()
        result = UserAnalysisResult(
            user_id=user_id,
            email='test@example.com',
            status=AnalysisStatus.SUCCESS,
            analysis_types_performed=['writing_style', 'topics_of_interest'],
            processing_time_seconds=2.5,
            error_message=None,
            activity_counts={'posts': 5, 'messages': 10},
            analysis_scope={'posts_analyzed': {'scheduled_count': 3}}
        )
        
        assert result.user_id == user_id
        assert result.email == 'test@example.com'
        assert result.status == AnalysisStatus.SUCCESS
        assert len(result.analysis_types_performed) == 2
        assert result.processing_time_seconds == 2.5
        assert result.error_message is None
        assert result.activity_counts['posts'] == 5

    def test_user_analysis_result_failed(self):
        """Test creating failed UserAnalysisResult."""
        result = UserAnalysisResult(
            user_id=uuid4(),
            email='failed@example.com',
            status=AnalysisStatus.FAILED,
            analysis_types_performed=[],
            processing_time_seconds=1.0,
            error_message="AI service unavailable"
        )
        
        assert result.status == AnalysisStatus.FAILED
        assert result.error_message == "AI service unavailable"
        assert len(result.analysis_types_performed) == 0


class TestBatchAnalysisResult:
    """Test cases for BatchAnalysisResult dataclass."""

    def test_batch_analysis_result_creation(self):
        """Test creating BatchAnalysisResult with complete data."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=45)
        
        user_results = [
            UserAnalysisResult(
                user_id=uuid4(),
                email='user1@example.com',
                status=AnalysisStatus.SUCCESS,
                analysis_types_performed=['writing_style'],
                processing_time_seconds=2.0
            )
        ]
        
        result = BatchAnalysisResult(
            total_users_processed=1,
            successful_analyses=1,
            failed_analyses=0,
            skipped_analyses=0,
            total_processing_time_seconds=45.0,
            start_time=start_time,
            end_time=end_time,
            user_results=user_results,
            error_summary={}
        )
        
        assert result.total_users_processed == 1
        assert result.successful_analyses == 1
        assert result.total_processing_time_seconds == 45.0
        assert len(result.user_results) == 1
        assert result.error_summary == {}

    def test_batch_analysis_result_with_errors(self):
        """Test BatchAnalysisResult with error summary."""
        result = BatchAnalysisResult(
            total_users_processed=3,
            successful_analyses=1,
            failed_analyses=2,
            skipped_analyses=0,
            total_processing_time_seconds=30.0,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            user_results=[],
            error_summary={'ai_service_error': 1, 'database_error': 1}
        )
        
        assert result.failed_analyses == 2
        assert result.error_summary['ai_service_error'] == 1
        assert result.error_summary['database_error'] == 1


class TestIndividualUserAnalysis:
    """Test cases for individual user analysis processing (subtask 6.2)."""

    @pytest.fixture
    def mock_db_client(self):
        """Mock database client."""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI analysis service."""
        mock_service = AsyncMock(spec=AIAnalysisService)
        # Set up default mock responses
        mock_service.analyze_writing_style = AsyncMock(return_value="Updated writing style analysis")
        mock_service.analyze_topics_of_interest = AsyncMock(return_value=[
            {"topic": "technology", "confidence": 0.8},
            {"topic": "business", "confidence": 0.6}
        ])
        mock_service.update_user_bio = AsyncMock(return_value="Enhanced bio with new insights")
        mock_service.analyze_negative_patterns = AsyncMock(return_value="Negative patterns analysis")
        return mock_service

    @pytest.fixture
    def analyzer(self, mock_db_client, mock_ai_service):
        """Create UserActivityAnalyzer instance with mocked dependencies."""
        return UserActivityAnalyzer(
            db_client=mock_db_client,
            ai_service=mock_ai_service,
            post_threshold=5,
            message_threshold=10
        )

    @pytest.fixture
    def sample_user_data(self):
        """Sample user data for testing."""
        return {
            'user_id': uuid4(),
            'email': 'test@example.com',
            'last_analysis_at': None,
            'post_count': 6,
            'message_count': 8,
            'needs_analysis': True
        }

    @pytest.fixture
    def sample_content_data(self):
        """Sample content data for testing."""
        return {
            'posts': [
                {
                    'id': uuid4(),
                    'content': 'This is a scheduled post about technology',
                    'status': 'scheduled',
                    'created_at': datetime.now(timezone.utc) - timedelta(hours=1)
                },
                {
                    'id': uuid4(),
                    'content': 'This is a dismissed post',
                    'status': 'dismissed',
                    'created_at': datetime.now(timezone.utc) - timedelta(hours=2)
                }
            ],
            'messages': [
                {
                    'id': uuid4(),
                    'content': 'User message about business strategy',
                    'created_at': datetime.now(timezone.utc) - timedelta(minutes=30)
                }
            ],
            'scheduled_posts': [
                {
                    'id': uuid4(),
                    'content': 'This is a scheduled post about technology',
                    'status': 'scheduled',
                    'created_at': datetime.now(timezone.utc) - timedelta(hours=1)
                }
            ],
            'dismissed_posts': [
                {
                    'id': uuid4(),
                    'content': 'This is a dismissed post',
                    'status': 'dismissed',
                    'created_at': datetime.now(timezone.utc) - timedelta(hours=2)
                }
            ],
            'user_profile': {
                'user_id': uuid4(),
                'email': 'test@example.com',
                'bio': 'Current user bio',
                'writing_style_analysis': 'Existing writing style',
                'negative_analysis': None
            },
            'last_post_id': uuid4(),
            'last_message_id': uuid4(),
            'content_counts': {
                'total_posts': 2,
                'scheduled_posts': 1,
                'dismissed_posts': 1,
                'messages': 1
            }
        }

    @pytest.mark.asyncio
    async def test_analyze_single_user_success(self, analyzer, sample_user_data):
        """Test successful single user analysis."""
        # Mock the state manager
        analyzer.state_manager.record_analysis_start = AsyncMock()
        
        # Mock the content retrieval and analysis methods
        with patch.object(analyzer, '_retrieve_user_content') as mock_retrieve, \
             patch.object(analyzer, '_has_sufficient_content', return_value=True), \
             patch.object(analyzer, '_orchestrate_ai_analysis') as mock_orchestrate, \
             patch.object(analyzer, '_store_analysis_results') as mock_store, \
             patch.object(analyzer, 'update_analysis_tracking') as mock_update_tracking:
            
            # Set up mock returns
            mock_content_data = {
                'posts': [{'id': uuid4(), 'content': 'test post', 'status': 'scheduled', 'created_at': datetime.now(timezone.utc)}],
                'messages': [],
                'scheduled_posts': [{'id': uuid4(), 'content': 'test post', 'status': 'scheduled', 'created_at': datetime.now(timezone.utc)}],
                'dismissed_posts': [],
                'user_profile': {'bio': 'Test bio', 'writing_style_analysis': 'Existing'},
                'content_counts': {'total_posts': 1, 'scheduled_posts': 1, 'dismissed_posts': 0, 'messages': 0}
            }
            mock_retrieve.return_value = mock_content_data
            
            mock_analysis_results = {
                'writing_style': 'Updated writing style',
                'topics_of_interest': [{'topic': 'tech', 'confidence': 0.8}]
            }
            mock_orchestrate.return_value = mock_analysis_results
            
            # Execute analysis
            result = await analyzer.analyze_single_user(sample_user_data)
            
            # Verify result
            assert result.status == AnalysisStatus.SUCCESS
            assert result.user_id == sample_user_data['user_id']
            assert result.email == sample_user_data['email']
            assert 'writing_style' in result.analysis_types_performed
            assert 'topics_of_interest' in result.analysis_types_performed
            assert result.processing_time_seconds > 0
            
            # Verify method calls
            mock_retrieve.assert_called_once_with(sample_user_data['user_id'])
            mock_orchestrate.assert_called_once()
            mock_store.assert_called_once()
            mock_update_tracking.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_single_user_insufficient_content(self, analyzer, sample_user_data):
        """Test analysis with insufficient content."""
        with patch.object(analyzer, '_retrieve_user_content') as mock_retrieve, \
             patch.object(analyzer, '_has_sufficient_content', return_value=False):
            
            mock_retrieve.return_value = {'content_counts': {'total_posts': 1, 'messages': 2}}
            
            result = await analyzer.analyze_single_user(sample_user_data)
            
            assert result.status == AnalysisStatus.SKIPPED
            assert result.error_message == "Insufficient content for analysis"
            assert len(result.analysis_types_performed) == 0

    @pytest.mark.asyncio
    async def test_analyze_single_user_failure(self, analyzer, sample_user_data):
        """Test analysis failure handling."""
        with patch.object(analyzer, '_retrieve_user_content', side_effect=Exception("Database error")):
            
            result = await analyzer.analyze_single_user(sample_user_data)
            
            assert result.status == AnalysisStatus.FAILED
            assert "Database error" in result.error_message
            assert len(result.analysis_types_performed) == 0

    @pytest.mark.asyncio
    async def test_retrieve_user_content(self, analyzer):
        """Test user content retrieval."""
        user_id = uuid4()
        
        # Mock state manager and profile data
        mock_content = {
            'posts': [
                {
                    'id': uuid4(),
                    'content': 'Scheduled post',
                    'status': 'scheduled',
                    'created_at': datetime.now(timezone.utc)
                },
                {
                    'id': uuid4(),
                    'content': 'Dismissed post',
                    'status': 'dismissed',
                    'created_at': datetime.now(timezone.utc)
                }
            ],
            'messages': [
                {
                    'id': uuid4(),
                    'content': 'User message',
                    'created_at': datetime.now(timezone.utc)
                }
            ]
        }
        
        mock_profile = {
            'user_id': user_id,
            'email': 'test@example.com',
            'bio': 'Test bio',
            'writing_style_analysis': 'Existing analysis'
        }
        
        analyzer.state_manager.get_new_content_since_analysis = AsyncMock(return_value=mock_content)
        
        with patch.object(analyzer, '_get_user_profile_data', return_value=mock_profile):
            result = await analyzer._retrieve_user_content(user_id)
            
            assert 'posts' in result
            assert 'messages' in result
            assert 'scheduled_posts' in result
            assert 'dismissed_posts' in result
            assert 'user_profile' in result
            assert 'content_counts' in result
            
            assert len(result['scheduled_posts']) == 1
            assert len(result['dismissed_posts']) == 1
            assert result['content_counts']['total_posts'] == 2
            assert result['content_counts']['messages'] == 1

    @pytest.mark.asyncio
    async def test_get_user_profile_data(self, analyzer):
        """Test user profile data retrieval."""
        user_id = uuid4()
        
        # Mock database responses
        user_data = {
            'id': str(user_id),
            'email': 'test@example.com',
            'bio': 'Test bio',
            'created_at': datetime.now(timezone.utc)
        }
        
        preferences_data = {
            'writing_style_analysis': 'Existing analysis',
            'negative_analysis': None
        }
        
        analyzer.db_client.execute_query_async = AsyncMock()
        analyzer.db_client.execute_query_async.side_effect = [
            [user_data],  # User query result
            [preferences_data]  # Preferences query result
        ]
        
        result = await analyzer._get_user_profile_data(user_id)
        
        assert result['user_id'] == user_id
        assert result['email'] == 'test@example.com'
        assert result['bio'] == 'Test bio'
        assert result['writing_style_analysis'] == 'Existing analysis'
        assert result['negative_analysis'] is None

    def test_has_sufficient_content(self, analyzer):
        """Test content sufficiency checking."""
        # Sufficient content case
        sufficient_content = {
            'content_counts': {
                'total_posts': 6,
                'scheduled_posts': 3,
                'dismissed_posts': 1,
                'messages': 5
            }
        }
        
        assert analyzer._has_sufficient_content(sufficient_content) is True
        
        # Insufficient content case
        insufficient_content = {
            'content_counts': {
                'total_posts': 1,
                'scheduled_posts': 0,
                'dismissed_posts': 0,
                'messages': 2
            }
        }
        
        assert analyzer._has_sufficient_content(insufficient_content) is False

    @pytest.mark.asyncio
    async def test_orchestrate_ai_analysis(self, analyzer, sample_content_data):
        """Test AI analysis orchestration."""
        user_id = uuid4()
        
        result = await analyzer._orchestrate_ai_analysis(user_id, sample_content_data)
        
        # Verify analysis types were performed based on content
        # Note: writing_style requires 2+ scheduled posts, but sample_content_data only has 1
        # So writing_style should NOT be in result
        assert 'writing_style' not in result  # Only 1 scheduled post, needs 2+
        assert 'topics_of_interest' in result  # 1+ scheduled posts
        assert 'bio_update' in result  # 1+ scheduled posts + bio exists
        assert 'negative_analysis' in result  # 1+ dismissed posts
        
        # Verify AI service calls based on actual logic
        analyzer.ai_service.analyze_writing_style.assert_not_called()  # Only 1 scheduled post, needs 2+
        analyzer.ai_service.analyze_topics_of_interest.assert_called_once()  # 1+ scheduled posts
        analyzer.ai_service.update_user_bio.assert_called_once()  # 1+ scheduled posts + bio exists
        analyzer.ai_service.analyze_negative_patterns.assert_called_once()  # 1+ dismissed posts

    @pytest.mark.asyncio
    async def test_orchestrate_ai_analysis_selective(self, analyzer):
        """Test AI analysis orchestration with selective analysis types."""
        user_id = uuid4()
        
        # Content with only scheduled posts (no dismissed posts)
        content_data = {
            'scheduled_posts': [
                {'content': 'Scheduled post 1'},
                {'content': 'Scheduled post 2'}
            ],
            'dismissed_posts': [],  # No dismissed posts
            'user_profile': {
                'bio': 'Current bio',
                'writing_style_analysis': 'Existing analysis'
            }
        }
        
        result = await analyzer._orchestrate_ai_analysis(user_id, content_data)
        
        # Should have writing style, topics, and bio update, but not negative analysis
        assert 'writing_style' in result
        assert 'topics_of_interest' in result
        assert 'bio_update' in result
        assert 'negative_analysis' not in result
        
        # Verify negative analysis was not called
        analyzer.ai_service.analyze_negative_patterns.assert_not_called()

    @pytest.mark.asyncio
    async def test_store_analysis_results(self, analyzer):
        """Test storing analysis results."""
        user_id = uuid4()
        analysis_results = {
            'writing_style': 'Updated writing style',
            'topics_of_interest': [{'topic': 'tech', 'confidence': 0.8}],
            'bio_update': 'Enhanced bio',
            'negative_analysis': 'Negative patterns'
        }
        
        # Mock the individual update methods
        with patch.object(analyzer, '_update_writing_style_analysis') as mock_writing, \
             patch.object(analyzer, '_update_topics_of_interest') as mock_topics, \
             patch.object(analyzer, '_update_user_bio') as mock_bio, \
             patch.object(analyzer, '_update_negative_analysis') as mock_negative:
            
            await analyzer._store_analysis_results(user_id, analysis_results)
            
            # Verify all update methods were called
            mock_writing.assert_called_once_with(user_id, 'Updated writing style')
            mock_topics.assert_called_once_with(user_id, [{'topic': 'tech', 'confidence': 0.8}])
            mock_bio.assert_called_once_with(user_id, 'Enhanced bio')
            mock_negative.assert_called_once_with(user_id, 'Negative patterns')

    @pytest.mark.asyncio
    async def test_update_writing_style_analysis(self, analyzer):
        """Test writing style analysis update."""
        user_id = uuid4()
        writing_style = "Updated writing style analysis"
        
        await analyzer._update_writing_style_analysis(user_id, writing_style)
        
        # Verify database update was called
        analyzer.db_client.execute_update_async.assert_called_once()
        call_args = analyzer.db_client.execute_update_async.call_args
        
        assert str(user_id) in call_args[0][1]['user_id']
        assert writing_style in call_args[0][1]['writing_style_analysis']

    @pytest.mark.asyncio
    async def test_update_user_bio(self, analyzer):
        """Test user bio update."""
        user_id = uuid4()
        bio = "Enhanced bio with new insights"
        
        await analyzer._update_user_bio(user_id, bio)
        
        # Verify database update was called
        analyzer.db_client.execute_update_async.assert_called_once()
        call_args = analyzer.db_client.execute_update_async.call_args
        
        assert str(user_id) in call_args[0][1]['user_id']
        assert bio in call_args[0][1]['bio']

    @pytest.mark.asyncio
    async def test_update_negative_analysis(self, analyzer):
        """Test negative analysis update."""
        user_id = uuid4()
        negative_analysis = "Negative patterns analysis"
        
        await analyzer._update_negative_analysis(user_id, negative_analysis)
        
        # Verify database update was called
        analyzer.db_client.execute_update_async.assert_called_once()
        call_args = analyzer.db_client.execute_update_async.call_args
        
        assert str(user_id) in call_args[0][1]['user_id']
        assert negative_analysis in call_args[0][1]['negative_analysis']

    def test_create_analysis_scope(self, analyzer, sample_content_data):
        """Test analysis scope creation."""
        analysis_results = {
            'writing_style': 'Updated style',
            'topics_of_interest': [{'topic': 'tech'}]
        }
        
        scope = analyzer._create_analysis_scope(sample_content_data, analysis_results)
        
        assert 'posts_analyzed' in scope
        assert 'messages_analyzed' in scope
        assert 'analysis_types_performed' in scope
        assert 'analysis_timestamp' in scope
        
        assert scope['posts_analyzed']['total_count'] == 2
        assert scope['posts_analyzed']['scheduled_count'] == 1
        assert scope['posts_analyzed']['dismissed_count'] == 1
        assert scope['messages_analyzed']['total_count'] == 1
        
        assert 'writing_style' in scope['analysis_types_performed']
        assert 'topics_of_interest' in scope['analysis_types_performed']

    @pytest.mark.asyncio
    async def test_analyze_single_user_with_state_cleanup(self, analyzer, sample_user_data):
        """Test that failed analysis properly cleans up state."""
        # Mock the state manager cleanup method
        analyzer.state_manager.cleanup_failed_analysis = AsyncMock()
        
        # Mock failure in orchestration
        with patch.object(analyzer, '_retrieve_user_content') as mock_retrieve, \
             patch.object(analyzer, '_has_sufficient_content', return_value=True), \
             patch.object(analyzer, '_orchestrate_ai_analysis', side_effect=Exception("AI service error")):
            
            mock_retrieve.return_value = {'content_counts': {'total_posts': 5}}
            
            result = await analyzer.analyze_single_user(sample_user_data)
            
            assert result.status == AnalysisStatus.FAILED
            assert "AI service error" in result.error_message
            
            # Verify cleanup was called
            analyzer.state_manager.cleanup_failed_analysis.assert_called_once_with(sample_user_data['user_id'])


if __name__ == '__main__':
    pytest.main([__file__])
"""
Comprehensive tests for AnalysisStateManager class.

Tests cover:
- Analysis timestamp tracking
- Analysis scope recording and retrieval
- New content detection since last analysis
- State validation and consistency checking
- Recovery mechanisms for failed analysis

Requirements tested:
- 7.1: Analysis start/completion timestamp recording
- 7.2: Analysis scope tracking for incremental processing
- 7.3: New content detection based on timestamps
- 7.4: State validation and consistency checking
- 7.5: Recovery mechanisms for failed analysis
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
import json

from analysis_state_manager import AnalysisStateManager


class TestAnalysisStateManager:
    """Test suite for AnalysisStateManager class."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mock database client."""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def state_manager(self, mock_db_client):
        """Create an AnalysisStateManager instance with mock database client."""
        return AnalysisStateManager(mock_db_client)

    @pytest.fixture
    def sample_user_id(self):
        """Generate a sample user ID."""
        return uuid4()

    @pytest.fixture
    def sample_analysis_scope(self):
        """Create a sample analysis scope dictionary."""
        return {
            "posts_analyzed": {
                "scheduled_count": 5,
                "dismissed_count": 3,
                "post_ids": ["uuid1", "uuid2", "uuid3"],
                "date_range": {
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2024-01-02T00:00:00Z"
                }
            },
            "messages_analyzed": {
                "total_count": 12,
                "conversation_ids": ["uuid4", "uuid5"],
                "excluded_first_messages": 2
            },
            "analysis_types_performed": [
                "writing_style",
                "topics_of_interest",
                "bio_update",
                "negative_analysis"
            ]
        }

    # Test get_last_analysis_timestamp - Requirement 7.1, 7.3
    @pytest.mark.asyncio
    async def test_get_last_analysis_timestamp_exists(self, state_manager, mock_db_client, sample_user_id):
        """Test getting last analysis timestamp when record exists."""
        expected_timestamp = datetime.now(timezone.utc)
        mock_db_client.execute_query_async.return_value = [{
            'last_analysis_at': expected_timestamp
        }]

        result = await state_manager.get_last_analysis_timestamp(sample_user_id)

        assert result == expected_timestamp
        mock_db_client.execute_query_async.assert_called_once()
        call_args = mock_db_client.execute_query_async.call_args
        assert str(sample_user_id) in call_args[0][1].values()

    @pytest.mark.asyncio
    async def test_get_last_analysis_timestamp_none(self, state_manager, mock_db_client, sample_user_id):
        """Test getting last analysis timestamp when no record exists."""
        mock_db_client.execute_query_async.return_value = []

        result = await state_manager.get_last_analysis_timestamp(sample_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_analysis_timestamp_null_value(self, state_manager, mock_db_client, sample_user_id):
        """Test getting last analysis timestamp when record exists but timestamp is null."""
        mock_db_client.execute_query_async.return_value = [{
            'last_analysis_at': None
        }]

        result = await state_manager.get_last_analysis_timestamp(sample_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_last_analysis_timestamp_timezone_handling(self, state_manager, mock_db_client, sample_user_id):
        """Test timezone handling for timestamps without timezone info."""
        naive_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_client.execute_query_async.return_value = [{
            'last_analysis_at': naive_timestamp
        }]

        result = await state_manager.get_last_analysis_timestamp(sample_user_id)

        assert result.tzinfo == timezone.utc
        assert result.replace(tzinfo=None) == naive_timestamp

    @pytest.mark.asyncio
    async def test_get_last_analysis_timestamp_database_error(self, state_manager, mock_db_client, sample_user_id):
        """Test error handling when database query fails."""
        mock_db_client.execute_query_async.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await state_manager.get_last_analysis_timestamp(sample_user_id)

    # Test record_analysis_start - Requirement 7.1, 7.5
    @pytest.mark.asyncio
    async def test_record_analysis_start_success(self, state_manager, mock_db_client, sample_user_id):
        """Test successful recording of analysis start."""
        mock_db_client.execute_update_async.return_value = 1

        await state_manager.record_analysis_start(sample_user_id)

        mock_db_client.execute_update_async.assert_called_once()
        call_args = mock_db_client.execute_update_async.call_args
        assert "INSERT INTO user_analysis_tracking" in call_args[0][0]
        assert "ON CONFLICT (user_id)" in call_args[0][0]
        assert str(sample_user_id) in call_args[0][1].values()

    @pytest.mark.asyncio
    async def test_record_analysis_start_database_error(self, state_manager, mock_db_client, sample_user_id):
        """Test error handling when recording analysis start fails."""
        mock_db_client.execute_update_async.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await state_manager.record_analysis_start(sample_user_id)

    # Test record_analysis_completion - Requirement 7.1, 7.2, 7.3
    @pytest.mark.asyncio
    async def test_record_analysis_completion_success(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test successful recording of analysis completion."""
        analysis_timestamp = datetime.now(timezone.utc)
        last_post_id = uuid4()
        last_message_id = uuid4()
        
        mock_db_client.execute_update.return_value = 1

        await state_manager.record_analysis_completion(
            sample_user_id,
            analysis_timestamp,
            sample_analysis_scope,
            last_post_id,
            last_message_id
        )

        mock_db_client.execute_update.assert_called_once()
        call_args = mock_db_client.execute_update.call_args
        
        # Verify query structure
        query = call_args[0][0]
        assert "INSERT INTO user_analysis_tracking" in query
        assert "ON CONFLICT (user_id)" in query
        assert "last_analysis_at" in query
        assert "analysis_scope" in query
        
        # Verify parameters
        params = call_args[0][1]
        assert str(sample_user_id) in params
        assert analysis_timestamp in params
        assert str(last_post_id) in params
        assert str(last_message_id) in params

    @pytest.mark.asyncio
    async def test_record_analysis_completion_timezone_handling(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test timezone handling when recording analysis completion."""
        naive_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        mock_db_client.execute_update.return_value = 1

        await state_manager.record_analysis_completion(
            sample_user_id,
            naive_timestamp,
            sample_analysis_scope
        )

        call_args = mock_db_client.execute_update.call_args
        params = call_args[0][1]
        
        # Find the timestamp parameter (should be timezone-aware)
        timestamp_param = params[1]  # Second parameter is the timestamp
        assert timestamp_param.tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_record_analysis_completion_invalid_scope(self, state_manager, mock_db_client, sample_user_id):
        """Test error handling with invalid analysis scope."""
        analysis_timestamp = datetime.now(timezone.utc)
        invalid_scope = {"invalid": "scope"}

        with pytest.raises(Exception):
            await state_manager.record_analysis_completion(
                sample_user_id,
                analysis_timestamp,
                invalid_scope
            )

    @pytest.mark.asyncio
    async def test_record_analysis_completion_optional_ids(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test recording analysis completion without optional post/message IDs."""
        analysis_timestamp = datetime.now(timezone.utc)
        mock_db_client.execute_update.return_value = 1

        await state_manager.record_analysis_completion(
            sample_user_id,
            analysis_timestamp,
            sample_analysis_scope
        )

        call_args = mock_db_client.execute_update.call_args
        params = call_args[0][1]
        
        # Verify None values for optional IDs
        assert params[2] is None  # last_analyzed_post_id
        assert params[3] is None  # last_analyzed_message_id

    # Test get_analysis_scope - Requirement 7.2, 7.3
    @pytest.mark.asyncio
    async def test_get_analysis_scope_exists(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test getting analysis scope when record exists."""
        mock_db_client.fetch_one.return_value = {
            'analysis_scope': sample_analysis_scope
        }

        result = await state_manager.get_analysis_scope(sample_user_id)

        assert result == sample_analysis_scope
        mock_db_client.fetch_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_analysis_scope_none(self, state_manager, mock_db_client, sample_user_id):
        """Test getting analysis scope when no record exists."""
        mock_db_client.fetch_one.return_value = None

        result = await state_manager.get_analysis_scope(sample_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_analysis_scope_null_value(self, state_manager, mock_db_client, sample_user_id):
        """Test getting analysis scope when record exists but scope is null."""
        mock_db_client.fetch_one.return_value = {
            'analysis_scope': None
        }

        result = await state_manager.get_analysis_scope(sample_user_id)

        assert result is None

    # Test get_new_content_since_analysis - Requirement 7.3, 1.2, 2.1, 2.2
    @pytest.mark.asyncio
    async def test_get_new_content_since_analysis_with_timestamp(self, state_manager, mock_db_client, sample_user_id):
        """Test getting new content when last analysis timestamp exists."""
        last_analysis = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Mock the timestamp query
        mock_db_client.fetch_one.side_effect = [
            {'last_analysis_at': last_analysis},  # First call for timestamp
            # Subsequent calls will be handled by fetch_all
        ]
        
        # Mock posts and messages queries
        sample_posts = [
            {
                'id': str(uuid4()),
                'content': 'Test post content',
                'status': 'scheduled',
                'user_feedback': None,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]
        
        sample_messages = [
            {
                'id': str(uuid4()),
                'content': 'Test message content',
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        mock_db_client.fetch_all.side_effect = [sample_posts, sample_messages]

        result = await state_manager.get_new_content_since_analysis(sample_user_id)

        assert 'posts' in result
        assert 'messages' in result
        assert len(result['posts']) == 1
        assert len(result['messages']) == 1
        assert isinstance(result['posts'][0]['id'], UUID)
        assert isinstance(result['messages'][0]['id'], UUID)

    @pytest.mark.asyncio
    async def test_get_new_content_since_analysis_no_timestamp(self, state_manager, mock_db_client, sample_user_id):
        """Test getting new content when no last analysis timestamp exists."""
        # Mock the timestamp query to return None
        mock_db_client.fetch_one.return_value = None
        
        # Mock empty results for posts and messages
        mock_db_client.fetch_all.side_effect = [[], []]

        result = await state_manager.get_new_content_since_analysis(sample_user_id)

        assert result == {'posts': [], 'messages': []}
        
        # Verify queries don't include timestamp conditions
        call_args_list = mock_db_client.fetch_all.call_args_list
        for call_args in call_args_list:
            query = call_args[0][0]
            params = call_args[0][1]
            # Should only have user_id parameter, no timestamp
            assert len(params) == 1
            assert str(sample_user_id) in params

    @pytest.mark.asyncio
    async def test_get_new_content_since_analysis_empty_results(self, state_manager, mock_db_client, sample_user_id):
        """Test getting new content when no new content exists."""
        last_analysis = datetime.now(timezone.utc) - timedelta(hours=1)
        
        mock_db_client.fetch_one.return_value = {'last_analysis_at': last_analysis}
        mock_db_client.fetch_all.side_effect = [[], []]  # Empty posts and messages

        result = await state_manager.get_new_content_since_analysis(sample_user_id)

        assert result == {'posts': [], 'messages': []}

    # Test validate_analysis_state - Requirement 7.4
    @pytest.mark.asyncio
    async def test_validate_analysis_state_valid(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test validation of valid analysis state."""
        now = datetime.now(timezone.utc)
        
        # Mock tracking record
        mock_db_client.fetch_one.side_effect = [
            {
                'last_analysis_at': now,
                'last_analyzed_post_id': str(uuid4()),
                'last_analyzed_message_id': str(uuid4()),
                'analysis_scope': sample_analysis_scope,
                'created_at': now - timedelta(hours=1),
                'updated_at': now
            },
            {'exists': True},  # Post exists
            {'exists': True}   # Message exists
        ]

        result = await state_manager.validate_analysis_state(sample_user_id)

        assert result['is_valid'] is True
        assert len(result['issues']) == 0
        assert result['user_id'] == str(sample_user_id)

    @pytest.mark.asyncio
    async def test_validate_analysis_state_no_record(self, state_manager, mock_db_client, sample_user_id):
        """Test validation when no tracking record exists."""
        mock_db_client.fetch_one.return_value = None

        result = await state_manager.validate_analysis_state(sample_user_id)

        assert result['is_valid'] is True
        assert len(result['warnings']) == 1
        assert "No tracking record found" in result['warnings'][0]

    @pytest.mark.asyncio
    async def test_validate_analysis_state_timestamp_issues(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test validation with timestamp consistency issues."""
        now = datetime.now(timezone.utc)
        
        # Mock tracking record with invalid timestamps
        mock_db_client.fetch_one.return_value = {
            'last_analysis_at': now - timedelta(hours=2),  # Before created_at
            'last_analyzed_post_id': None,
            'last_analyzed_message_id': None,
            'analysis_scope': sample_analysis_scope,
            'created_at': now - timedelta(hours=1),
            'updated_at': now - timedelta(hours=2)  # Before created_at
        }

        result = await state_manager.validate_analysis_state(sample_user_id)

        assert result['is_valid'] is False
        assert len(result['issues']) >= 1
        assert any("Updated timestamp is before created timestamp" in issue for issue in result['issues'])

    @pytest.mark.asyncio
    async def test_validate_analysis_state_invalid_scope(self, state_manager, mock_db_client, sample_user_id):
        """Test validation with invalid analysis scope."""
        now = datetime.now(timezone.utc)
        invalid_scope = {"invalid": "scope"}
        
        mock_db_client.fetch_one.return_value = {
            'last_analysis_at': now,
            'last_analyzed_post_id': None,
            'last_analyzed_message_id': None,
            'analysis_scope': invalid_scope,
            'created_at': now - timedelta(hours=1),
            'updated_at': now
        }

        result = await state_manager.validate_analysis_state(sample_user_id)

        assert result['is_valid'] is False
        assert len(result['issues']) >= 1

    # Test cleanup_failed_analysis - Requirement 7.5, 1.4
    @pytest.mark.asyncio
    async def test_cleanup_failed_analysis_success(self, state_manager, mock_db_client, sample_user_id):
        """Test successful cleanup of failed analysis."""
        mock_db_client.execute_update.return_value = 1

        await state_manager.cleanup_failed_analysis(sample_user_id)

        mock_db_client.execute_update.assert_called_once()
        call_args = mock_db_client.execute_update.call_args
        
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE user_analysis_tracking" in query
        assert "SET updated_at = NOW()" in query
        assert "last_analysis_at" not in query  # Should NOT update this
        assert str(sample_user_id) in params

    @pytest.mark.asyncio
    async def test_cleanup_failed_analysis_no_record(self, state_manager, mock_db_client, sample_user_id):
        """Test cleanup when no tracking record exists."""
        mock_db_client.execute_update.return_value = 0

        # Should not raise an exception, just log a warning
        await state_manager.cleanup_failed_analysis(sample_user_id)

        mock_db_client.execute_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_failed_analysis_database_error(self, state_manager, mock_db_client, sample_user_id):
        """Test error handling during cleanup."""
        mock_db_client.execute_update.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await state_manager.cleanup_failed_analysis(sample_user_id)

    # Test get_users_needing_analysis - Requirement 2.1, 2.2, 2.3, 2.4
    @pytest.mark.asyncio
    async def test_get_users_needing_analysis_success(self, state_manager, mock_db_client):
        """Test getting users who need analysis based on thresholds."""
        sample_users = [
            {
                'user_id': str(uuid4()),
                'email': 'user1@example.com',
                'last_analysis_at': None,
                'post_count': 6,
                'message_count': 4
            },
            {
                'user_id': str(uuid4()),
                'email': 'user2@example.com',
                'last_analysis_at': datetime.now(timezone.utc) - timedelta(hours=2),
                'post_count': 3,
                'message_count': 12
            }
        ]
        
        mock_db_client.fetch_all.return_value = sample_users

        result = await state_manager.get_users_needing_analysis(post_threshold=5, message_threshold=10)

        assert len(result) == 2
        assert all(user['needs_analysis'] for user in result)
        assert all(isinstance(user['user_id'], UUID) for user in result)
        
        # Verify query includes thresholds
        call_args = mock_db_client.fetch_all.call_args
        params = call_args[0][1]
        assert 5 in params  # post_threshold
        assert 10 in params  # message_threshold

    @pytest.mark.asyncio
    async def test_get_users_needing_analysis_empty(self, state_manager, mock_db_client):
        """Test getting users when no users need analysis."""
        mock_db_client.fetch_all.return_value = []

        result = await state_manager.get_users_needing_analysis()

        assert result == []

    # Test get_analysis_progress_summary - Requirement 8.1, 8.2
    @pytest.mark.asyncio
    async def test_get_analysis_progress_summary_success(self, state_manager, mock_db_client):
        """Test getting analysis progress summary."""
        mock_db_client.fetch_one.return_value = {
            'total_users': 100,
            'users_with_tracking': 80,
            'users_analyzed': 75,
            'users_never_analyzed': 5,
            'avg_hours_since_analysis': 24.5,
            'oldest_analysis': datetime.now(timezone.utc) - timedelta(days=7),
            'newest_analysis': datetime.now(timezone.utc)
        }

        result = await state_manager.get_analysis_progress_summary()

        assert result['total_users'] == 100
        assert result['users_with_tracking'] == 80
        assert result['users_analyzed'] == 75
        assert result['users_never_analyzed'] == 5
        assert result['avg_hours_since_analysis'] == 24.5

    @pytest.mark.asyncio
    async def test_get_analysis_progress_summary_empty(self, state_manager, mock_db_client):
        """Test getting analysis progress summary when no data exists."""
        mock_db_client.fetch_one.return_value = None

        result = await state_manager.get_analysis_progress_summary()

        assert result['total_users'] == 0
        assert result['users_with_tracking'] == 0
        assert result['users_analyzed'] == 0

    # Test _validate_analysis_scope - Requirement 7.4
    def test_validate_analysis_scope_valid(self, state_manager, sample_analysis_scope):
        """Test validation of valid analysis scope."""
        result = state_manager._validate_analysis_scope(sample_analysis_scope)

        assert result['is_valid'] is True
        assert len(result['issues']) == 0

    def test_validate_analysis_scope_missing_keys(self, state_manager):
        """Test validation with missing required keys."""
        invalid_scope = {"posts_analyzed": {}}

        result = state_manager._validate_analysis_scope(invalid_scope)

        assert result['is_valid'] is False
        assert len(result['issues']) >= 2  # Missing messages_analyzed and analysis_types_performed

    def test_validate_analysis_scope_invalid_posts_structure(self, state_manager):
        """Test validation with invalid posts_analyzed structure."""
        invalid_scope = {
            "posts_analyzed": "not_a_dict",
            "messages_analyzed": {"total_count": 5},
            "analysis_types_performed": ["writing_style"]
        }

        result = state_manager._validate_analysis_scope(invalid_scope)

        assert result['is_valid'] is False
        assert any("posts_analyzed must be a dictionary" in issue for issue in result['issues'])

    def test_validate_analysis_scope_invalid_counts(self, state_manager):
        """Test validation with invalid count values."""
        invalid_scope = {
            "posts_analyzed": {
                "scheduled_count": -1,  # Invalid negative count
                "dismissed_count": "not_a_number"  # Invalid type
            },
            "messages_analyzed": {"total_count": 5},
            "analysis_types_performed": ["writing_style"]
        }

        result = state_manager._validate_analysis_scope(invalid_scope)

        assert result['is_valid'] is False
        assert len(result['issues']) >= 2

    def test_validate_analysis_scope_invalid_analysis_types(self, state_manager):
        """Test validation with invalid analysis types."""
        invalid_scope = {
            "posts_analyzed": {"scheduled_count": 1, "dismissed_count": 1},
            "messages_analyzed": {"total_count": 5},
            "analysis_types_performed": ["invalid_type", "writing_style"]
        }

        result = state_manager._validate_analysis_scope(invalid_scope)

        assert result['is_valid'] is True  # Should still be valid, just with warnings
        assert any("Unknown analysis type: invalid_type" in issue for issue in result['issues'])

    # Test _validate_content_counts - Requirement 7.4
    @pytest.mark.asyncio
    async def test_validate_content_counts_success(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test validation of content counts against database."""
        # Mock database queries to return matching counts
        mock_db_client.fetch_one.side_effect = [
            {'scheduled_count': 5, 'dismissed_count': 3},  # Posts query
            {'total_count': 12}  # Messages query
        ]

        validation_result = {'warnings': []}
        
        await state_manager._validate_content_counts(sample_user_id, sample_analysis_scope, validation_result)

        assert len(validation_result['warnings']) == 0

    @pytest.mark.asyncio
    async def test_validate_content_counts_mismatch(self, state_manager, mock_db_client, sample_user_id, sample_analysis_scope):
        """Test validation when content counts don't match database."""
        # Mock database queries to return lower counts than recorded
        mock_db_client.fetch_one.side_effect = [
            {'scheduled_count': 3, 'dismissed_count': 1},  # Lower than recorded
            {'total_count': 8}  # Lower than recorded
        ]

        validation_result = {'warnings': []}
        
        await state_manager._validate_content_counts(sample_user_id, sample_analysis_scope, validation_result)

        assert len(validation_result['warnings']) >= 2
        assert any("scheduled posts" in warning for warning in validation_result['warnings'])
        assert any("dismissed posts" in warning for warning in validation_result['warnings'])


# Integration tests
class TestAnalysisStateManagerIntegration:
    """Integration tests for AnalysisStateManager with more realistic scenarios."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a more sophisticated mock database client for integration tests."""
        mock_client = AsyncMock()
        
        # Set up realistic database responses
        mock_client.fetch_one = AsyncMock()
        mock_client.fetch_all = AsyncMock()
        mock_client.execute_update = AsyncMock()
        
        return mock_client

    @pytest.fixture
    def state_manager(self, mock_db_client):
        """Create an AnalysisStateManager instance for integration tests."""
        return AnalysisStateManager(mock_db_client)

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, state_manager, mock_db_client):
        """Test complete workflow from start to completion."""
        user_id = uuid4()
        analysis_timestamp = datetime.now(timezone.utc)
        
        # Mock database responses for the workflow
        mock_db_client.fetch_one.side_effect = [
            None,  # No previous analysis
            {'last_analysis_at': analysis_timestamp}  # After completion
        ]
        mock_db_client.execute_update.return_value = 1
        
        # Step 1: Record analysis start
        await state_manager.record_analysis_start(user_id)
        
        # Step 2: Record analysis completion
        analysis_scope = {
            "posts_analyzed": {"scheduled_count": 3, "dismissed_count": 2},
            "messages_analyzed": {"total_count": 8},
            "analysis_types_performed": ["writing_style", "topics_of_interest"]
        }
        
        await state_manager.record_analysis_completion(
            user_id, analysis_timestamp, analysis_scope
        )
        
        # Step 3: Verify timestamp is recorded
        result_timestamp = await state_manager.get_last_analysis_timestamp(user_id)
        
        # Verify the workflow completed successfully
        assert mock_db_client.execute_update.call_count == 2  # Start + completion
        assert result_timestamp == analysis_timestamp

    @pytest.mark.asyncio
    async def test_failed_analysis_recovery(self, state_manager, mock_db_client):
        """Test recovery from failed analysis."""
        user_id = uuid4()
        
        # Mock database responses
        mock_db_client.execute_update.return_value = 1
        
        # Step 1: Record analysis start
        await state_manager.record_analysis_start(user_id)
        
        # Step 2: Simulate analysis failure and cleanup
        await state_manager.cleanup_failed_analysis(user_id)
        
        # Verify cleanup was called but completion was not
        assert mock_db_client.execute_update.call_count == 2
        
        # Verify cleanup query doesn't update last_analysis_at
        cleanup_call = mock_db_client.execute_update.call_args_list[1]
        cleanup_query = cleanup_call[0][0]
        assert "last_analysis_at" not in cleanup_query
        assert "updated_at = NOW()" in cleanup_query

    @pytest.mark.asyncio
    async def test_incremental_analysis_detection(self, state_manager, mock_db_client):
        """Test detection of new content for incremental analysis."""
        user_id = uuid4()
        last_analysis = datetime.now(timezone.utc) - timedelta(hours=2)
        
        # Mock responses for incremental content detection
        mock_db_client.fetch_one.return_value = {'last_analysis_at': last_analysis}
        
        # Mock new content since last analysis
        new_posts = [
            {
                'id': str(uuid4()),
                'content': 'New post content',
                'status': 'scheduled',
                'user_feedback': None,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc)
            }
        ]
        
        new_messages = [
            {
                'id': str(uuid4()),
                'content': 'New message content',
                'created_at': datetime.now(timezone.utc)
            }
        ]
        
        mock_db_client.fetch_all.side_effect = [new_posts, new_messages]
        
        # Get new content
        result = await state_manager.get_new_content_since_analysis(user_id)
        
        # Verify incremental detection
        assert len(result['posts']) == 1
        assert len(result['messages']) == 1
        
        # Verify queries include timestamp filters
        call_args_list = mock_db_client.fetch_all.call_args_list
        for call_args in call_args_list:
            query = call_args[0][0]
            params = call_args[0][1]
            # Should include timestamp parameter for filtering
            assert len(params) >= 2  # user_id + timestamp(s)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

    # Test progress tracking and recovery methods - Requirement 7.1, 7.2, 7.5

    @pytest.mark.asyncio
    async def test_record_analysis_progress_success(self, state_manager, mock_db_client, sample_user_id):
        """Test successful recording of analysis progress."""
        progress_data = {
            'step': 2,
            'total_steps': 5,
            'current_operation': 'analyzing_writing_style'
        }
        
        mock_db_client.execute_update_async.return_value = 1

        await state_manager.record_analysis_progress(sample_user_id, progress_data)

        mock_db_client.execute_update_async.assert_called_once()
        call_args = mock_db_client.execute_update_async.call_args
        
        query = call_args[0][0]
        params = call_args[0][1]
        
        assert "UPDATE user_analysis_tracking" in query
        assert "analysis_scope" in query
        assert str(sample_user_id) in params.values()

    @pytest.mark.asyncio
    async def test_record_analysis_progress_invalid_data(self, state_manager, mock_db_client, sample_user_id):
        """Test error handling with invalid progress data."""
        invalid_progress = {'step': 1}  # Missing required keys

        with pytest.raises(ValueError, match="Missing required progress key"):
            await state_manager.record_analysis_progress(sample_user_id, invalid_progress)

    @pytest.mark.asyncio
    async def test_get_analysis_progress_exists(self, state_manager, mock_db_client, sample_user_id):
        """Test getting analysis progress when it exists."""
        progress_data = {
            'step': 3,
            'total_steps': 5,
            'current_operation': 'analyzing_topics'
        }
        
        mock_db_client.execute_query_async.return_value = [{
            'analysis_scope': {'progress': progress_data}
        }]

        result = await state_manager.get_analysis_progress(sample_user_id)

        assert result == progress_data

    @pytest.mark.asyncio
    async def test_get_analysis_progress_none(self, state_manager, mock_db_client, sample_user_id):
        """Test getting analysis progress when none exists."""
        mock_db_client.execute_query_async.return_value = []

        result = await state_manager.get_analysis_progress(sample_user_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_detect_interrupted_analysis_success(self, state_manager, mock_db_client):
        """Test detection of interrupted analyses."""
        interrupted_data = [
            {
                'user_id': str(uuid4()),
                'analysis_scope': {
                    'status': 'in_progress',
                    'progress': {'step': 2, 'total_steps': 5, 'current_operation': 'test'}
                },
                'updated_at': datetime.now(timezone.utc) - timedelta(hours=2),
                'last_analysis_at': None
            }
        ]
        
        mock_db_client.execute_query_async.return_value = interrupted_data

        result = await state_manager.detect_interrupted_analysis(timeout_minutes=60)

        assert len(result) == 1
        assert isinstance(result[0]['user_id'], UUID)
        assert result[0]['minutes_since_update'] > 60

    @pytest.mark.asyncio
    async def test_detect_interrupted_analysis_empty(self, state_manager, mock_db_client):
        """Test detection when no interrupted analyses exist."""
        mock_db_client.execute_query_async.return_value = []

        result = await state_manager.detect_interrupted_analysis()

        assert result == []

    @pytest.mark.asyncio
    async def test_recover_interrupted_analysis_success(self, state_manager, mock_db_client, sample_user_id):
        """Test successful recovery of interrupted analysis."""
        # Mock getting current progress
        mock_db_client.execute_query_async.side_effect = [
            [{'analysis_scope': {'progress': {'step': 2, 'total_steps': 5}}}],  # get_analysis_progress
        ]
        
        # Mock recovery update
        mock_db_client.execute_update_async.return_value = 1

        result = await state_manager.recover_interrupted_analysis(sample_user_id)

        assert result['recovered'] is True
        assert result['user_id'] == str(sample_user_id)
        assert result['previous_progress'] is not None

    @pytest.mark.asyncio
    async def test_recover_interrupted_analysis_no_record(self, state_manager, mock_db_client, sample_user_id):
        """Test recovery when no interrupted analysis exists."""
        # Mock getting current progress (none)
        mock_db_client.execute_query_async.return_value = []
        
        # Mock recovery update (no rows affected)
        mock_db_client.execute_update_async.return_value = 0

        result = await state_manager.recover_interrupted_analysis(sample_user_id)

        assert result['recovered'] is False
        assert result['previous_progress'] is None

    @pytest.mark.asyncio
    async def test_cleanup_stale_progress_success(self, state_manager, mock_db_client):
        """Test successful cleanup of stale progress records."""
        mock_db_client.execute_update_async.return_value = 3

        result = await state_manager.cleanup_stale_progress(max_age_hours=24)

        assert result == 3
        mock_db_client.execute_update_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_stale_progress_none(self, state_manager, mock_db_client):
        """Test cleanup when no stale records exist."""
        mock_db_client.execute_update_async.return_value = 0

        result = await state_manager.cleanup_stale_progress()

        assert result == 0

    @pytest.mark.asyncio
    async def test_get_analysis_recovery_summary_success(self, state_manager, mock_db_client):
        """Test getting analysis recovery summary."""
        mock_db_client.execute_query_async.return_value = [{
            'total_tracking_records': 50,
            'in_progress_count': 5,
            'completed_count': 40,
            'potentially_stale_count': 2,
            'avg_minutes_since_update': 30.5
        }]

        result = await state_manager.get_analysis_recovery_summary()

        assert result['total_tracking_records'] == 50
        assert result['in_progress_count'] == 5
        assert result['completed_count'] == 40
        assert result['potentially_stale_count'] == 2
        assert result['avg_minutes_since_update'] == 30.5

    @pytest.mark.asyncio
    async def test_get_analysis_recovery_summary_empty(self, state_manager, mock_db_client):
        """Test getting recovery summary when no data exists."""
        mock_db_client.execute_query_async.return_value = []

        result = await state_manager.get_analysis_recovery_summary()

        assert result['total_tracking_records'] == 0
        assert result['in_progress_count'] == 0

    @pytest.mark.asyncio
    async def test_batch_recover_interrupted_analyses_success(self, state_manager, mock_db_client):
        """Test successful batch recovery of interrupted analyses."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        
        # Mock detect_interrupted_analysis
        interrupted_analyses = [
            {
                'user_id': user_id_1,
                'last_updated': datetime.now(timezone.utc) - timedelta(hours=2),
                'last_analysis_at': None,
                'progress': {'step': 1, 'total_steps': 5},
                'minutes_since_update': 120
            },
            {
                'user_id': user_id_2,
                'last_updated': datetime.now(timezone.utc) - timedelta(hours=1),
                'last_analysis_at': None,
                'progress': {'step': 3, 'total_steps': 5},
                'minutes_since_update': 60
            }
        ]
        
        # Mock the detect method
        state_manager.detect_interrupted_analysis = AsyncMock(return_value=interrupted_analyses)
        
        # Mock recovery for each user
        recovery_results = [
            {'user_id': str(user_id_1), 'recovered': True, 'previous_progress': {'step': 1}},
            {'user_id': str(user_id_2), 'recovered': True, 'previous_progress': {'step': 3}}
        ]
        
        state_manager.recover_interrupted_analysis = AsyncMock(side_effect=recovery_results)

        result = await state_manager.batch_recover_interrupted_analyses()

        assert result['total_detected'] == 2
        assert result['total_recovered'] == 2
        assert result['failed_recoveries'] == 0
        assert len(result['recovery_details']) == 2

    @pytest.mark.asyncio
    async def test_batch_recover_interrupted_analyses_partial_failure(self, state_manager, mock_db_client):
        """Test batch recovery with some failures."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        
        # Mock detect_interrupted_analysis
        interrupted_analyses = [
            {
                'user_id': user_id_1,
                'last_updated': datetime.now(timezone.utc) - timedelta(hours=2),
                'last_analysis_at': None,
                'progress': {'step': 1, 'total_steps': 5},
                'minutes_since_update': 120
            },
            {
                'user_id': user_id_2,
                'last_updated': datetime.now(timezone.utc) - timedelta(hours=1),
                'last_analysis_at': None,
                'progress': {'step': 3, 'total_steps': 5},
                'minutes_since_update': 60
            }
        ]
        
        state_manager.detect_interrupted_analysis = AsyncMock(return_value=interrupted_analyses)
        
        # Mock recovery - first succeeds, second fails
        def mock_recovery(user_id):
            if user_id == user_id_1:
                return {'user_id': str(user_id), 'recovered': True, 'previous_progress': {'step': 1}}
            else:
                raise Exception("Recovery failed")
        
        state_manager.recover_interrupted_analysis = AsyncMock(side_effect=mock_recovery)

        result = await state_manager.batch_recover_interrupted_analyses()

        assert result['total_detected'] == 2
        assert result['total_recovered'] == 1
        assert result['failed_recoveries'] == 1
        assert len(result['recovery_details']) == 2

    @pytest.mark.asyncio
    async def test_batch_recover_interrupted_analyses_max_limit(self, state_manager, mock_db_client):
        """Test batch recovery respects max_recoveries limit."""
        # Create more interrupted analyses than the limit
        interrupted_analyses = []
        for i in range(5):
            interrupted_analyses.append({
                'user_id': uuid4(),
                'last_updated': datetime.now(timezone.utc) - timedelta(hours=2),
                'last_analysis_at': None,
                'progress': {'step': i, 'total_steps': 5},
                'minutes_since_update': 120
            })
        
        state_manager.detect_interrupted_analysis = AsyncMock(return_value=interrupted_analyses)
        state_manager.recover_interrupted_analysis = AsyncMock(
            return_value={'recovered': True, 'previous_progress': {}}
        )

        result = await state_manager.batch_recover_interrupted_analyses(max_recoveries=3)

        assert result['total_detected'] == 5
        assert result['total_recovered'] == 3  # Limited by max_recoveries
        assert len(result['recovery_details']) == 3


# Additional integration tests for progress tracking and recovery
class TestAnalysisStateManagerProgressIntegration:
    """Integration tests for progress tracking and recovery functionality."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mock database client for progress integration tests."""
        mock_client = AsyncMock()
        mock_client.execute_query_async = AsyncMock()
        mock_client.execute_update_async = AsyncMock()
        return mock_client

    @pytest.fixture
    def state_manager(self, mock_db_client):
        """Create an AnalysisStateManager instance for progress integration tests."""
        return AnalysisStateManager(mock_db_client)

    @pytest.mark.asyncio
    async def test_progress_tracking_workflow(self, state_manager, mock_db_client):
        """Test complete progress tracking workflow."""
        user_id = uuid4()
        
        # Mock database responses
        mock_db_client.execute_update_async.return_value = 1
        mock_db_client.execute_query_async.return_value = [{
            'analysis_scope': {
                'progress': {
                    'step': 3,
                    'total_steps': 5,
                    'current_operation': 'analyzing_topics'
                },
                'status': 'in_progress'
            }
        }]
        
        # Step 1: Record progress
        progress_data = {
            'step': 3,
            'total_steps': 5,
            'current_operation': 'analyzing_topics'
        }
        
        await state_manager.record_analysis_progress(user_id, progress_data)
        
        # Step 2: Get progress
        result_progress = await state_manager.get_analysis_progress(user_id)
        
        # Verify workflow
        assert mock_db_client.execute_update_async.call_count == 1
        assert result_progress['step'] == 3
        assert result_progress['current_operation'] == 'analyzing_topics'

    @pytest.mark.asyncio
    async def test_recovery_workflow(self, state_manager, mock_db_client):
        """Test complete recovery workflow."""
        user_id = uuid4()
        
        # Mock interrupted analysis detection
        interrupted_data = [{
            'user_id': str(user_id),
            'analysis_scope': {
                'status': 'in_progress',
                'progress': {'step': 2, 'total_steps': 5, 'current_operation': 'test'}
            },
            'updated_at': datetime.now(timezone.utc) - timedelta(hours=2),
            'last_analysis_at': None
        }]
        
        # Mock database responses for recovery workflow
        mock_db_client.execute_query_async.side_effect = [
            interrupted_data,  # detect_interrupted_analysis
            [{'analysis_scope': {'progress': {'step': 2, 'total_steps': 5}}}],  # get_analysis_progress
        ]
        mock_db_client.execute_update_async.return_value = 1
        
        # Step 1: Detect interrupted analysis
        interrupted_analyses = await state_manager.detect_interrupted_analysis()
        
        # Step 2: Recover the analysis
        recovery_result = await state_manager.recover_interrupted_analysis(user_id)
        
        # Verify recovery workflow
        assert len(interrupted_analyses) == 1
        assert recovery_result['recovered'] is True
        assert recovery_result['previous_progress'] is not None

    @pytest.mark.asyncio
    async def test_stale_cleanup_workflow(self, state_manager, mock_db_client):
        """Test stale progress cleanup workflow."""
        # Mock cleanup operation
        mock_db_client.execute_update_async.return_value = 5
        
        # Mock recovery summary
        mock_db_client.execute_query_async.return_value = [{
            'total_tracking_records': 100,
            'in_progress_count': 10,
            'completed_count': 85,
            'potentially_stale_count': 5,
            'avg_minutes_since_update': 45.2
        }]
        
        # Step 1: Get summary before cleanup
        summary_before = await state_manager.get_analysis_recovery_summary()
        
        # Step 2: Cleanup stale progress
        cleaned_count = await state_manager.cleanup_stale_progress(max_age_hours=24)
        
        # Verify cleanup workflow
        assert summary_before['potentially_stale_count'] == 5
        assert cleaned_count == 5
        assert mock_db_client.execute_update_async.call_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
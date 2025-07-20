"""
Unit tests for ActivityThresholdChecker class.

Tests all counting scenarios, threshold validation, and user qualification logic
as specified in requirements 2.1, 2.2, 2.3, and 2.4.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4, UUID

from activity_threshold_checker import ActivityThresholdChecker


class TestActivityThresholdChecker:
    """Test cases for ActivityThresholdChecker."""

    @pytest.fixture
    def mock_db_client(self):
        """Create a mock database client."""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def threshold_checker(self, mock_db_client):
        """Create ActivityThresholdChecker instance with mock database."""
        return ActivityThresholdChecker(mock_db_client)

    @pytest.fixture
    def sample_user_id(self):
        """Generate a sample user ID."""
        return uuid4()

    @pytest.fixture
    def sample_timestamp(self):
        """Generate a sample timestamp for testing."""
        return datetime.now(timezone.utc) - timedelta(days=7)

    @pytest.mark.asyncio
    async def test_initialization(self, mock_db_client):
        """Test ActivityThresholdChecker initialization."""
        checker = ActivityThresholdChecker(mock_db_client)
        
        assert checker.db_client is mock_db_client
        assert checker.post_threshold == 5
        assert checker.message_threshold == 10

    @pytest.mark.asyncio
    async def test_get_post_counts_no_timestamp(self, threshold_checker, mock_db_client, sample_user_id):
        """Test getting post counts without timestamp filter."""
        # Mock database responses
        mock_db_client.fetch_one.side_effect = [
            {'count': 3},  # scheduled posts
            {'count': 2}   # dismissed posts
        ]
        
        result = await threshold_checker.get_post_counts(sample_user_id)
        
        assert result == {
            'scheduled_count': 3,
            'dismissed_count': 2
        }
        
        # Verify correct queries were made
        assert mock_db_client.fetch_one.call_count == 2

    @pytest.mark.asyncio
    async def test_get_post_counts_with_timestamp(self, threshold_checker, mock_db_client, sample_user_id, sample_timestamp):
        """Test getting post counts with timestamp filter."""
        mock_db_client.fetch_one.side_effect = [
            {'count': 5},  # scheduled posts
            {'count': 3}   # dismissed posts
        ]
        
        result = await threshold_checker.get_post_counts(sample_user_id, sample_timestamp)
        
        assert result == {
            'scheduled_count': 5,
            'dismissed_count': 3
        }

    @pytest.mark.asyncio
    async def test_get_post_counts_no_results(self, threshold_checker, mock_db_client, sample_user_id):
        """Test getting post counts when no results are returned."""
        mock_db_client.fetch_one.side_effect = [None, None]
        
        result = await threshold_checker.get_post_counts(sample_user_id)
        
        assert result == {
            'scheduled_count': 0,
            'dismissed_count': 0
        }

    @pytest.mark.asyncio
    async def test_get_message_counts_no_idea_bank(self, threshold_checker, mock_db_client, sample_user_id):
        """Test message counting for conversations without idea bank."""
        conversation_id = uuid4()
        
        # Mock conversations without idea_bank_id
        mock_db_client.fetch_all.side_effect = [
            [{'id': str(conversation_id), 'idea_bank_id': None, 'created_at': datetime.now(timezone.utc)}],
            [{'id': str(uuid4()), 'created_at': datetime.now(timezone.utc)} for _ in range(5)]  # 5 messages
        ]
        
        result = await threshold_checker.get_message_counts(sample_user_id)
        
        assert result == 5  # All 5 messages counted (no exclusion)

    @pytest.mark.asyncio
    async def test_get_message_counts_with_idea_bank_exclusion(self, threshold_checker, mock_db_client, sample_user_id):
        """Test message counting with idea bank first message exclusion (requirement 2.3)."""
        conversation_id = uuid4()
        idea_bank_id = uuid4()
        
        # Mock conversations with idea_bank_id
        mock_db_client.fetch_all.side_effect = [
            [{'id': str(conversation_id), 'idea_bank_id': str(idea_bank_id), 'created_at': datetime.now(timezone.utc)}],
            [{'id': str(uuid4()), 'created_at': datetime.now(timezone.utc)} for _ in range(5)]  # 5 messages
        ]
        
        result = await threshold_checker.get_message_counts(sample_user_id)
        
        assert result == 4  # 5 messages - 1 (first message excluded from idea bank conversation)

    @pytest.mark.asyncio
    async def test_check_user_activity_meets_post_threshold(self, threshold_checker, mock_db_client, sample_user_id):
        """Test user activity check when post threshold is met (requirement 2.1)."""
        # Mock post counts that meet threshold (>5 total posts)
        mock_db_client.fetch_one.side_effect = [
            {'count': 4},  # scheduled posts
            {'count': 2}   # dismissed posts (total = 6 > 5)
        ]
        
        # Mock message count below threshold
        mock_db_client.fetch_all.side_effect = [
            [],  # No conversations
        ]
        
        result = await threshold_checker.check_user_activity(sample_user_id)
        
        assert result == {
            'scheduled_posts': 4,
            'dismissed_posts': 2,
            'total_posts': 6,
            'messages': 0,
            'meets_threshold': True
        }

    @pytest.mark.asyncio
    async def test_check_user_activity_meets_message_threshold(self, threshold_checker, mock_db_client, sample_user_id):
        """Test user activity check when message threshold is met (requirement 2.2)."""
        # Mock post counts below threshold
        mock_db_client.fetch_one.side_effect = [
            {'count': 2},  # scheduled posts
            {'count': 1}   # dismissed posts (total = 3 < 5)
        ]
        
        # Mock message count that meets threshold (>10 messages)
        conversation_id = uuid4()
        mock_db_client.fetch_all.side_effect = [
            [{'id': str(conversation_id), 'idea_bank_id': None, 'created_at': datetime.now(timezone.utc)}],
            [{'id': str(uuid4()), 'created_at': datetime.now(timezone.utc)} for _ in range(12)]  # 12 messages > 10
        ]
        
        result = await threshold_checker.check_user_activity(sample_user_id)
        
        assert result == {
            'scheduled_posts': 2,
            'dismissed_posts': 1,
            'total_posts': 3,
            'messages': 12,
            'meets_threshold': True
        }

    def test_set_thresholds(self, threshold_checker):
        """Test setting custom thresholds."""
        threshold_checker.set_thresholds(10, 20)
        
        assert threshold_checker.post_threshold == 10
        assert threshold_checker.message_threshold == 20

    def test_set_thresholds_invalid_values(self, threshold_checker):
        """Test setting invalid threshold values."""
        with pytest.raises(ValueError, match="Thresholds must be positive integers"):
            threshold_checker.set_thresholds(0, 10)
        
        with pytest.raises(ValueError, match="Thresholds must be positive integers"):
            threshold_checker.set_thresholds(10, -1)

    def test_get_current_thresholds(self, threshold_checker):
        """Test getting current threshold values."""
        result = threshold_checker.get_current_thresholds()
        
        assert result == {
            'post_threshold': 5,
            'message_threshold': 10
        }
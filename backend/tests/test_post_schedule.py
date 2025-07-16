"""
Integration tests for PostScheduleService.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.post_schedule import (
    PostScheduleService,
    _get_job_name,
    _datetime_to_cron,
)
from app.models.posts import Post


class TestPostScheduleService:
    """Integration tests for PostScheduleService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_db):
        """Create PostScheduleService instance."""
        return PostScheduleService(mock_db)

    @pytest.fixture
    def sample_post(self):
        """Sample post data."""
        return Post(
            id=uuid4(),
            user_id=uuid4(),
            content="Test post content",
            status="suggested",
            platform="linkedin",
        )

    def test_get_job_name(self):
        """Test job name generation."""
        post_id = uuid4()
        job_name = _get_job_name(post_id)

        assert job_name.startswith("share-post-")
        assert str(post_id) in job_name

    def test_datetime_to_cron(self):
        """Test datetime to cron conversion."""
        dt = datetime(2024, 1, 15, 14, 30, 0)
        cron = _datetime_to_cron(dt)

        assert cron == "30 14 15 1 *"

    @pytest.mark.asyncio
    async def test_schedule_post_success(self, service, mock_db, sample_post):
        """Test successful post scheduling."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_post
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock Cloud Scheduler client
        with patch.object(service, "_create_scheduler_job") as mock_create_job:
            mock_create_job.return_value = "test-job-name"

            scheduled_at = datetime.now(timezone.utc)
            result = await service.schedule_post(
                sample_post.user_id, sample_post.id, scheduled_at
            )

            assert result == "test-job-name"
            assert sample_post.status == "scheduled"
            assert sample_post.scheduled_at == scheduled_at
            assert sample_post.scheduler_job_name == "test-job-name"

    @pytest.mark.asyncio
    async def test_schedule_post_not_found(self, service, mock_db):
        """Test scheduling when post not found."""
        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        user_id = uuid4()
        post_id = uuid4()
        scheduled_at = datetime.now(timezone.utc)

        result = await service.schedule_post(user_id, post_id, scheduled_at)

        assert result is None

    @pytest.mark.asyncio
    async def test_schedule_post_scheduler_failure(self, service, mock_db, sample_post):
        """Test scheduling when Cloud Scheduler fails."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_post
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock Cloud Scheduler client failure
        with patch.object(service, "_create_scheduler_job") as mock_create_job:
            mock_create_job.return_value = ""  # Empty string indicates failure

            scheduled_at = datetime.now(timezone.utc)
            result = await service.schedule_post(
                sample_post.user_id, sample_post.id, scheduled_at
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_unschedule_post_success(self, service, mock_db, sample_post):
        """Test successful post unscheduling."""
        # Set up post with existing schedule
        sample_post.scheduler_job_name = "existing-job"
        sample_post.scheduled_at = datetime.now(timezone.utc)
        sample_post.status = "scheduled"

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_post
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock Cloud Scheduler client
        with patch.object(service, "_delete_scheduler_job") as mock_delete_job:
            mock_delete_job.return_value = True

            result = await service.unschedule_post(sample_post.user_id, sample_post.id)

            assert result is True
            assert sample_post.status == "suggested"
            assert sample_post.scheduled_at is None
            assert sample_post.scheduler_job_name is None

    @pytest.mark.asyncio
    async def test_unschedule_post_no_job(self, service, mock_db, sample_post):
        """Test unscheduling when no scheduler job exists."""
        # Set up post without scheduler job
        sample_post.scheduler_job_name = None

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_post
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.unschedule_post(sample_post.user_id, sample_post.id)

        assert result is True  # Should succeed even without job

    @pytest.mark.asyncio
    async def test_reschedule_post_success(self, service, mock_db, sample_post):
        """Test successful post rescheduling."""
        # Set up post with existing schedule
        sample_post.scheduler_job_name = "existing-job"
        sample_post.scheduled_at = datetime.now(timezone.utc)

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_post
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock Cloud Scheduler client
        with patch.object(service, "_update_scheduler_job") as mock_update_job:
            mock_update_job.return_value = True

            new_scheduled_at = datetime.now(timezone.utc)
            result = await service.reschedule_post(
                sample_post.user_id, sample_post.id, new_scheduled_at
            )

            assert result == "existing-job"
            assert sample_post.scheduled_at == new_scheduled_at

    @pytest.mark.asyncio
    async def test_reschedule_post_no_existing_job(self, service, mock_db, sample_post):
        """Test rescheduling when no existing job."""
        # Set up post without scheduler job
        sample_post.scheduler_job_name = None

        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_post
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock schedule_post method
        with patch.object(service, "schedule_post") as mock_schedule:
            mock_schedule.return_value = "new-job-name"

            new_scheduled_at = datetime.now(timezone.utc)
            result = await service.reschedule_post(
                sample_post.user_id, sample_post.id, new_scheduled_at
            )

            assert result == "new-job-name"
            mock_schedule.assert_called_once_with(
                sample_post.user_id, sample_post.id, new_scheduled_at, "UTC"
            )


class TestCloudSchedulerIntegration:
    """Test Cloud Scheduler integration methods."""

    @pytest.fixture
    def service(self):
        """Create PostScheduleService instance."""
        mock_db = Mock(spec=AsyncSession)
        return PostScheduleService(mock_db)

    def test_parent_path(self, service):
        """Test parent path generation."""
        path = service._parent_path()
        assert path == "projects/promptly-social-staging/locations/us-central1"

    @patch("app.services.post_schedule.scheduler_v1.CloudSchedulerClient")
    def test_client_initialization_success(self, mock_scheduler_client, service):
        """Test successful Cloud Scheduler client initialization."""
        mock_client_instance = Mock()
        mock_scheduler_client.return_value = mock_client_instance

        client = service._client()

        assert client == mock_client_instance

    @patch("app.services.post_schedule.scheduler_v1.CloudSchedulerClient")
    def test_client_initialization_failure(self, mock_scheduler_client, service):
        """Test Cloud Scheduler client initialization failure."""
        mock_scheduler_client.side_effect = Exception("Client initialization failed")

        client = service._client()

        assert client is None

    @patch.dict(
        "os.environ",
        {
            "GCP_PROJECT_ID": "test-project",
            "GCP_LOCATION": "us-central1",
            "GCP_SHARE_POST_FUNCTION_URL": "https://test-function-url",
        },
    )
    def test_create_scheduler_job(self, service):
        """Test scheduler job creation."""
        with patch.object(service, "_client") as mock_client_method:
            mock_client = Mock()
            mock_client_method.return_value = mock_client

            user_id = uuid4()
            post_id = uuid4()
            scheduled_at = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

            result = service._create_scheduler_job(post_id, user_id, scheduled_at)

            # Verify job creation was called
            mock_client.create_job.assert_called_once()

            # Verify job configuration
            call_args = mock_client.create_job.call_args
            job = call_args.kwargs["job"]

            assert job["schedule"] == "30 14 15 1 *"
            assert job["time_zone"] == "UTC"
            assert job["http_target"]["http_method"] == "POST"

            # Verify payload contains user_id and post_id
            import json

            payload = json.loads(job["http_target"]["body"].decode("utf-8"))
            assert payload["user_id"] == str(user_id)
            assert payload["post_id"] == str(post_id)

    def test_update_scheduler_job(self, service):
        """Test scheduler job update."""
        with patch.object(service, "_client") as mock_client_method:
            mock_client = Mock()
            mock_client_method.return_value = mock_client

            job_name = "test-job"
            scheduled_at = datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)

            result = service._update_scheduler_job(job_name, scheduled_at)

            # Verify job update was called
            mock_client.update_job.assert_called_once()

            # Verify update configuration
            call_args = mock_client.update_job.call_args
            job = call_args.kwargs["job"]

            assert job["schedule"] == "30 14 15 1 *"
            assert job["time_zone"] == "UTC"

    def test_delete_scheduler_job(self, service):
        """Test scheduler job deletion."""
        with patch.object(service, "_client") as mock_client_method:
            mock_client = Mock()
            mock_client_method.return_value = mock_client

            job_name = "test-job"

            result = service._delete_scheduler_job(job_name)

            # Verify job deletion was called
            mock_client.delete_job.assert_called_once()
            assert result is True

    def test_scheduler_operations_no_client(self, service):
        """Test scheduler operations when client is unavailable."""
        with patch.object(service, "_client") as mock_client_method:
            mock_client_method.return_value = None

            # Test create job
            result = service._create_scheduler_job(uuid4(), uuid4(), datetime.now())
            assert result == ""

            # Test update job
            result = service._update_scheduler_job("test-job", datetime.now())
            assert result is False

            # Test delete job
            result = service._delete_scheduler_job("test-job")
            assert result is False

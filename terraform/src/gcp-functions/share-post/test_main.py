"""
Unit tests for the share-post cloud function.
"""

import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

# Import the main function
from main import (
    share_post,
    get_post_data,
    get_linkedin_connection,
    refresh_token_if_needed,
    share_to_linkedin,
    update_post_status,
    get_post_media,
)


class TestSharePostFunction:
    """Test cases for the main share_post function."""

    def test_share_post_missing_json(self):
        """Test function with missing JSON body."""
        request = Mock()
        request.method = "POST"
        request.get_json.return_value = None
        
        response_data, status_code, headers = share_post(request)
        response = json.loads(response_data)
        
        assert status_code == 400
        assert response["success"] is False
        assert "Invalid JSON" in response["error"]

    def test_share_post_missing_parameters(self):
        """Test function with missing required parameters."""
        request = Mock()
        request.method = "POST"
        request.get_json.return_value = {"user_id": "test-user"}
        
        response_data, status_code, headers = share_post(request)
        response = json.loads(response_data)
        
        assert status_code == 400
        assert response["success"] is False
        assert "user_id and post_id are required" in response["error"]

    def test_share_post_options_request(self):
        """Test CORS preflight request."""
        request = Mock()
        request.method = "OPTIONS"
        
        response_data, status_code, headers = share_post(request)
        
        assert status_code == 204
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert headers["Access-Control-Allow-Methods"] == "POST"

    @patch('main.get_supabase_client')
    @patch('main.asyncio.run')
    def test_share_post_post_not_found(self, mock_asyncio_run, mock_supabase):
        """Test function when post is not found."""
        request = Mock()
        request.method = "POST"
        request.get_json.return_value = {
            "user_id": "test-user",
            "post_id": "test-post"
        }
        
        # Mock asyncio.run to return None for get_post_data
        mock_asyncio_run.return_value = None
        
        response_data, status_code, headers = share_post(request)
        response = json.loads(response_data)
        
        assert status_code == 404
        assert response["success"] is False
        assert "Post not found" in response["error"]


class TestGetPostData:
    """Test cases for get_post_data function."""

    @pytest.mark.asyncio
    async def test_get_post_data_success(self):
        """Test successful post data retrieval."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [{
            "id": "test-post",
            "user_id": "test-user",
            "status": "scheduled",
            "content": "Test post content"
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_post_data(mock_supabase, "test-user", "test-post")
        
        assert result is not None
        assert result["id"] == "test-post"
        assert result["status"] == "scheduled"

    @pytest.mark.asyncio
    async def test_get_post_data_not_found(self):
        """Test post data retrieval when post not found."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_post_data(mock_supabase, "test-user", "test-post")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_post_data_wrong_status(self):
        """Test post data retrieval when post has wrong status."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [{
            "id": "test-post",
            "user_id": "test-user",
            "status": "draft",
            "content": "Test post content"
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_post_data(mock_supabase, "test-user", "test-post")
        
        assert result is None


class TestGetLinkedInConnection:
    """Test cases for get_linkedin_connection function."""

    @pytest.mark.asyncio
    async def test_get_linkedin_connection_success(self):
        """Test successful LinkedIn connection retrieval."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [{
            "id": "connection-id",
            "user_id": "test-user",
            "platform": "linkedin",
            "connection_data": {
                "access_token": "test-token",
                "linkedin_user_id": "linkedin-user-id"
            }
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_linkedin_connection(mock_supabase, "test-user")
        
        assert result is not None
        assert result["platform"] == "linkedin"
        assert result["connection_data"]["access_token"] == "test-token"

    @pytest.mark.asyncio
    async def test_get_linkedin_connection_not_found(self):
        """Test LinkedIn connection retrieval when connection not found."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_linkedin_connection(mock_supabase, "test-user")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_linkedin_connection_no_token(self):
        """Test LinkedIn connection retrieval when no access token."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [{
            "id": "connection-id",
            "user_id": "test-user",
            "platform": "linkedin",
            "connection_data": {}
        }]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_linkedin_connection(mock_supabase, "test-user")
        
        assert result is None


class TestRefreshTokenIfNeeded:
    """Test cases for refresh_token_if_needed function."""

    @pytest.mark.asyncio
    @patch.dict('os.environ', {'LINKEDIN_CLIENT_ID': 'test-id', 'LINKEDIN_CLIENT_SECRET': 'test-secret'})
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        mock_supabase = Mock()
        connection = {
            "id": "connection-id",
            "connection_data": {
                "access_token": "old-token",
                "refresh_token": "refresh-token",
                "expires_at": "2024-01-01T00:00:00Z"
            }
        }
        
        # Mock httpx response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new-token",
                "expires_in": 3600
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await refresh_token_if_needed(mock_supabase, connection)
            
            assert result is not None
            assert result["connection_data"]["access_token"] == "new-token"

    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token(self):
        """Test token refresh when no refresh token available."""
        mock_supabase = Mock()
        connection = {
            "id": "connection-id",
            "connection_data": {
                "access_token": "old-token"
            }
        }
        
        result = await refresh_token_if_needed(mock_supabase, connection)
        
        assert result is None


class TestShareToLinkedIn:
    """Test cases for share_to_linkedin function."""

    @pytest.mark.asyncio
    async def test_share_to_linkedin_success(self):
        """Test successful LinkedIn sharing."""
        post_data = {
            "content": "Test post content",
            "article_url": "https://example.com/article"
        }
        
        connection = {
            "connection_data": {
                "access_token": "test-token",
                "linkedin_user_id": "linkedin-user-id"
            }
        }
        
        # Mock httpx response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                "id": "linkedin-post-id"
            }
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await share_to_linkedin(post_data, connection)
            
            assert result is not None
            assert result["linkedin_post_id"] == "linkedin-post-id"
            assert "shared_at" in result

    @pytest.mark.asyncio
    async def test_share_to_linkedin_missing_credentials(self):
        """Test LinkedIn sharing with missing credentials."""
        post_data = {"content": "Test post content"}
        connection = {"connection_data": {}}
        
        result = await share_to_linkedin(post_data, connection)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_share_to_linkedin_api_error(self):
        """Test LinkedIn sharing with API error."""
        post_data = {"content": "Test post content"}
        connection = {
            "connection_data": {
                "access_token": "test-token",
                "linkedin_user_id": "linkedin-user-id"
            }
        }
        
        # Mock httpx response with error
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await share_to_linkedin(post_data, connection)
            
            assert result is None


class TestUpdatePostStatus:
    """Test cases for update_post_status function."""

    @pytest.mark.asyncio
    async def test_update_post_status_success(self):
        """Test successful post status update."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [{"id": "test-post"}]
        
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await update_post_status(mock_supabase, "test-post", {"status": "posted"})
        
        assert result is True

    @pytest.mark.asyncio
    async def test_update_post_status_failure(self):
        """Test post status update failure."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await update_post_status(mock_supabase, "test-post", {"status": "posted"})
        
        assert result is False


class TestGetPostMedia:
    """Test cases for get_post_media function."""

    @pytest.mark.asyncio
    async def test_get_post_media_success(self):
        """Test successful post media retrieval."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = [
            {
                "id": "media-1",
                "post_id": "test-post",
                "media_type": "image",
                "linkedin_asset_urn": "urn:li:image:123"
            }
        ]
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_post_media(mock_supabase, "test-post")
        
        assert len(result) == 1
        assert result[0]["media_type"] == "image"

    @pytest.mark.asyncio
    async def test_get_post_media_empty(self):
        """Test post media retrieval with no media."""
        mock_supabase = Mock()
        mock_response = Mock()
        mock_response.data = []
        
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response
        
        result = await get_post_media(mock_supabase, "test-post")
        
        assert len(result) == 0
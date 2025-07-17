#!/usr/bin/env python3
"""
Local testing script for the unified post scheduler function.

This script allows you to test the function locally with mock data.
"""

import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Set up environment variables for testing
os.environ.update({
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_SERVICE_KEY": "test_service_key",
    "LINKEDIN_CLIENT_ID": "test_client_id",
    "LINKEDIN_CLIENT_SECRET": "test_client_secret",
    "LINKEDIN_TOKEN_REFRESH_THRESHOLD": "60",
    "MAX_RETRY_ATTEMPTS": "2"
})

from main import (
    process_scheduled_posts,
    get_posts_to_publish,
    process_posts_batch,
    process_single_post,
    get_supabase_client
)


class MockRequest:
    """Mock Flask request object for testing."""
    
    def __init__(self, method="POST", json_data=None):
        self.method = method
        self._json_data = json_data or {}
    
    def get_json(self, silent=True):
        return self._json_data


class MockSupabaseClient:
    """Mock Supabase client for testing."""
    
    def __init__(self):
        self.posts_data = []
        self.connections_data = []
        self.media_data = []
        self.update_calls = []
    
    def table(self, table_name):
        return MockSupabaseTable(self, table_name)


class MockSupabaseTable:
    """Mock Supabase table for testing."""
    
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self._query = {}
    
    def select(self, columns):
        self._query["select"] = columns
        return self
    
    def eq(self, column, value):
        self._query.setdefault("eq", {})[column] = value
        return self
    
    def is_(self, column, value):
        self._query.setdefault("is", {})[column] = value
        return self
    
    def gte(self, column, value):
        self._query.setdefault("gte", {})[column] = value
        return self
    
    def lte(self, column, value):
        self._query.setdefault("lte", {})[column] = value
        return self
    
    def order(self, column, desc=False):
        self._query["order"] = {"column": column, "desc": desc}
        return self
    
    def update(self, data):
        self._query["update"] = data
        return self
    
    def execute(self):
        """Execute the query and return mock data."""
        if self.table_name == "posts":
            if "update" in self._query:
                # Mock update operation
                self.client.update_calls.append({
                    "table": self.table_name,
                    "query": self._query
                })
                return Mock(data=[{"id": "test-post-id"}])
            else:
                # Mock select operation
                return Mock(data=self.client.posts_data)
        
        elif self.table_name == "social_connections":
            return Mock(data=self.client.connections_data)
        
        elif self.table_name == "post_media":
            return Mock(data=self.client.media_data)
        
        return Mock(data=[])


def create_mock_post(post_id="test-post-id", user_id="test-user-id", scheduled_minutes_ago=2):
    """Create a mock post scheduled for publishing."""
    scheduled_at = datetime.now(timezone.utc) - timedelta(minutes=scheduled_minutes_ago)
    
    return {
        "id": post_id,
        "user_id": user_id,
        "content": "Test post content for LinkedIn",
        "status": "scheduled",
        "scheduled_at": scheduled_at.isoformat(),
        "posted_at": None,
        "article_url": "https://example.com/article",
        "platform": "linkedin"
    }


def create_mock_linkedin_connection(user_id="test-user-id"):
    """Create a mock LinkedIn connection."""
    return {
        "id": "connection-id",
        "user_id": user_id,
        "platform": "linkedin",
        "connection_data": {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "linkedin_user_id": "test_linkedin_user",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        }
    }


async def test_get_posts_to_publish():
    """Test the get_posts_to_publish function."""
    print("Testing get_posts_to_publish...")
    
    # Create mock client with test data
    mock_client = MockSupabaseClient()
    mock_client.posts_data = [
        create_mock_post("post-1", "user-1", 2),
        create_mock_post("post-2", "user-1", 4),
        create_mock_post("post-3", "user-2", 1),
    ]
    
    posts = await get_posts_to_publish(mock_client)
    
    print(f"Found {len(posts)} posts to publish")
    for post in posts:
        print(f"  - Post {post['id']} for user {post['user_id']}")
    
    assert len(posts) == 3, f"Expected 3 posts, got {len(posts)}"
    print("✅ get_posts_to_publish test passed")


async def test_process_single_post():
    """Test processing a single post."""
    print("\nTesting process_single_post...")
    
    mock_client = MockSupabaseClient()
    mock_client.connections_data = [create_mock_linkedin_connection()]
    
    test_post = create_mock_post()
    
    # Mock the LinkedIn sharing functions
    with patch('main.refresh_token_if_needed') as mock_refresh, \
         patch('main.get_post_media') as mock_media, \
         patch('main.share_to_linkedin') as mock_share, \
         patch('main.update_post_status') as mock_update:
        
        # Set up mocks
        mock_refresh.return_value = create_mock_linkedin_connection()
        mock_media.return_value = []
        mock_share.return_value = {
            "linkedin_post_id": "linkedin-post-123",
            "shared_at": datetime.now(timezone.utc).isoformat()
        }
        mock_update.return_value = True
        
        result = await process_single_post(mock_client, test_post)
        
        print(f"Process result: {result}")
        
        assert result["success"] == True, "Expected successful processing"
        assert result["linkedin_post_id"] == "linkedin-post-123"
        print("✅ process_single_post test passed")


async def test_full_function():
    """Test the complete function with mock data."""
    print("\nTesting complete function...")
    
    # Mock the get_supabase_client function
    mock_client = MockSupabaseClient()
    mock_client.posts_data = [
        create_mock_post("post-1", "user-1", 2),
        create_mock_post("post-2", "user-1", 3),
    ]
    mock_client.connections_data = [create_mock_linkedin_connection("user-1")]
    
    with patch('main.get_supabase_client') as mock_get_client, \
         patch('main.refresh_token_if_needed') as mock_refresh, \
         patch('main.get_post_media') as mock_media, \
         patch('main.share_to_linkedin') as mock_share, \
         patch('main.update_post_status') as mock_update:
        
        # Set up mocks
        mock_get_client.return_value = mock_client
        mock_refresh.return_value = create_mock_linkedin_connection("user-1")
        mock_media.return_value = []
        mock_share.return_value = {
            "linkedin_post_id": "linkedin-post-123",
            "shared_at": datetime.now(timezone.utc).isoformat()
        }
        mock_update.return_value = True
        
        # Create mock request
        request = MockRequest()
        
        # Call the function
        response_data, status_code, headers = process_scheduled_posts(request)
        response = json.loads(response_data)
        
        print(f"Response: {response}")
        print(f"Status code: {status_code}")
        
        assert status_code == 200, f"Expected status 200, got {status_code}"
        assert response["success"] == True, "Expected successful response"
        assert response["posts_processed"] == 2, f"Expected 2 posts processed, got {response['posts_processed']}"
        print("✅ Full function test passed")


async def test_no_posts_scenario():
    """Test when no posts are found for publishing."""
    print("\nTesting no posts scenario...")
    
    mock_client = MockSupabaseClient()
    mock_client.posts_data = []  # No posts
    
    with patch('main.get_supabase_client') as mock_get_client:
        mock_get_client.return_value = mock_client
        
        request = MockRequest()
        response_data, status_code, headers = process_scheduled_posts(request)
        response = json.loads(response_data)
        
        print(f"Response: {response}")
        
        assert status_code == 200, f"Expected status 200, got {status_code}"
        assert response["success"] == True, "Expected successful response"
        assert response["posts_processed"] == 0, f"Expected 0 posts processed, got {response['posts_processed']}"
        print("✅ No posts scenario test passed")


async def main():
    """Run all tests."""
    print("🧪 Running unified post scheduler tests...\n")
    
    try:
        await test_get_posts_to_publish()
        await test_process_single_post()
        await test_full_function()
        await test_no_posts_scenario()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
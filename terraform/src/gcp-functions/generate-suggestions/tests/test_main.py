import main

import sys
import os
import pytest
from unittest.mock import MagicMock, patch
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock functions_framework before importing main
mock_functions_framework = MagicMock()
mock_functions_framework.http.side_effect = lambda f: f
sys.modules["functions_framework"] = mock_functions_framework


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.get_json.return_value = {"user_id": "test_user"}
    request.method = "POST"
    return request


@pytest.mark.asyncio
@patch("main.SupabaseClient")
@patch("main.ArticleFetcher")
@patch("main.PostsGenerator")
async def test_generate_suggestions_success(
    mock_posts_generator,
    mock_article_fetcher,
    mock_supabase_client_class,
    mock_request,
):
    # Setup mocks
    mock_supabase_instance = MagicMock()
    mock_supabase_client_class.return_value = mock_supabase_instance

    mock_supabase_instance.get_user_preferences_complete.return_value = {
        "topics_of_interest": [],
        "websites": ["http://example.com"],
        "substacks": [],
        "bio": "",
    }
    mock_supabase_instance.get_writing_style.return_value = "formal"
    mock_supabase_instance.get_user_ideas.return_value = []
    mock_supabase_instance.get_latest_articles_from_idea_bank.return_value = []
    mock_supabase_instance.save_candidate_posts_to_idea_banks.side_effect = (
        lambda user_id, posts: posts
    )
    mock_supabase_instance.save_suggested_posts.return_value = [{"post_id": "123"}]

    # Mock ArticleFetcher response
    mock_article_fetcher_instance = mock_article_fetcher.return_value

    async def mock_fetch_candidate_articles(*args, **kwargs):
        return [{"id": "fetched1"}]

    mock_article_fetcher_instance.fetch_candidate_articles.side_effect = (
        mock_fetch_candidate_articles
    )

    # Mock PostsGenerator response
    mock_posts_generator_instance = mock_posts_generator.return_value

    async def mock_filter_articles(*args, **kwargs):
        return [{"id": "filtered1", "content": "content"}]

    mock_posts_generator_instance.filter_articles.side_effect = mock_filter_articles

    async def mock_generate_post(*args, **kwargs):
        mock_generated_post = MagicMock()
        mock_generated_post.model_dump.return_value = {"linkedin_post": "post"}
        return mock_generated_post

    mock_posts_generator_instance.generate_post.side_effect = mock_generate_post

    # Call the function
    response, status_code, _ = await main.generate_suggestions(mock_request)

    # Assertions
    assert status_code == 200
    response_json = json.loads(response)
    assert response_json[0]["post_id"] == "123"

    mock_article_fetcher_instance.fetch_candidate_articles.assert_called()
    mock_posts_generator_instance.filter_articles.assert_called_once()
    mock_posts_generator_instance.generate_post.assert_called_once()
    mock_supabase_instance.save_suggested_posts.assert_called_once()
    mock_supabase_instance.update_daily_suggestions_job_status.assert_called_once()


@pytest.mark.asyncio
async def test_generate_suggestions_no_user_id(mock_request):
    mock_request.get_json.return_value = {"something": "else"}
    response, status_code, _ = await main.generate_suggestions(mock_request)
    assert status_code == 400
    assert "user_id is required" in response


@pytest.mark.asyncio
async def test_generate_suggestions_invalid_json(mock_request):
    mock_request.get_json.return_value = None
    response, status_code, _ = await main.generate_suggestions(mock_request)
    assert status_code == 400
    assert "Invalid JSON" in response


@pytest.mark.asyncio
@patch("main.SupabaseClient")
async def test_generate_suggestions_exception(mock_supabase_client_class, mock_request):
    mock_supabase_instance = MagicMock()
    mock_supabase_client_class.return_value = mock_supabase_instance
    mock_supabase_instance.get_user_preferences_complete.side_effect = Exception(
        "DB Error"
    )

    response, status_code, _ = await main.generate_suggestions(mock_request)
    assert status_code == 500
    assert "DB Error" in response

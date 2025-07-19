import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from posts_generator import PostsGenerator, FilteredArticlesResult, GeneratedPost


@pytest.fixture
def posts_generator():
    """Fixture to initialize PostsGenerator with a mock Supabase client."""
    mock_supabase_client = MagicMock()
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_openrouter_key"}):
        generator = PostsGenerator(supabase_client=mock_supabase_client)
    return generator


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_filter_articles(mock_agent, posts_generator):
    mock_run = MagicMock()
    mock_run.output = FilteredArticlesResult(ids=["1", "3"])

    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    candidate_posts = [
        {"id": "1", "title": "Article 1"},
        {"id": "2", "title": "Article 2"},
        {"id": "3", "title": "Article 3"},
    ]

    filtered = await posts_generator.filter_articles(
        candidate_posts, "bio", "style", ["tech"], 2
    )

    assert len(filtered) == 2
    assert filtered[0]["id"] == "1"
    assert filtered[1]["id"] == "3"
    mock_agent.return_value.run.assert_called_once()


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_filter_articles_no_matches(mock_agent, posts_generator):
    mock_run = MagicMock()
    mock_run.output = FilteredArticlesResult(ids=[])

    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    candidate_posts = [{"id": "1", "title": "Article 1"}]
    filtered = await posts_generator.filter_articles(
        candidate_posts, "bio", "style", ["tech"], 2
    )

    assert len(filtered) == 0


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_generate_post(mock_agent, posts_generator):
    mock_run = MagicMock()
    mock_run.output = GeneratedPost(
        linkedin_post="This is a post.", topics=["tech", "ai"]
    )

    # Since agent.run is an async method, we need to mock it with an awaitable
    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    result = await posts_generator.generate_post(
        "some content", "bio", "style", "strategy"
    )

    assert result.linkedin_post == "This is a post."
    assert result.topics == ["tech", "ai"]
    mock_agent.return_value.run.assert_called_once()

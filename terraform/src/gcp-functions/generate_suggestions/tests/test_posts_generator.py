import sys
import os
import pytest
from unittest.mock import MagicMock, patch
from uuid import UUID

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from posts_generator import PostsGenerator, FilteredArticlesResult, GeneratedPost
from main import remove_duplicate_posts


@pytest.fixture
def posts_generator():
    """Fixture to initialize PostsGenerator."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_openrouter_key"}):
        generator = PostsGenerator()
    return generator


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_filter_articles(mock_agent, posts_generator):
    # Mock the agent to return "YES" for the first two articles
    call_count = 0

    def mock_run_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        mock_run = MagicMock()
        # Return YES for first 2 calls, NO for the rest
        mock_run.output = "YES" if call_count <= 2 else "NO"
        return mock_run

    async def mock_run_async(*args, **kwargs):
        return mock_run_side_effect(*args, **kwargs)

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    candidate_posts = [
        {"id": "1", "title": "Article 1"},
        {"id": "2", "title": "Article 2"},
        {"id": "3", "title": "Article 3"},
    ]

    filtered = await posts_generator.filter_articles(
        candidate_posts, "bio", ["tech"], 2
    )

    assert len(filtered) == 2
    # Since we shuffle, we can't guarantee order, just check we got 2 articles
    assert all(article["id"] in ["1", "2", "3"] for article in filtered)
    # Should have called the agent at least twice (might be more due to shuffling)
    assert mock_agent.return_value.run.call_count >= 2


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_filter_articles_no_matches(mock_agent, posts_generator):
    mock_run = MagicMock()
    mock_run.output = "NO"  # Return NO for all articles

    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    candidate_posts = [{"id": "1", "title": "Article 1"}]
    filtered = await posts_generator.filter_articles(
        candidate_posts, "bio", ["tech"], 2
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


def test_prepare_articles_for_filtering(posts_generator):
    """Test article preparation for filtering."""
    candidate_posts = [
        {
            "id": 123,  # Non-string ID
            "title": "Test Article",
            "subtitle": "Test Subtitle",
            "content": " ".join(["word"] * 500),  # Long content
            "url": "https://example.com"
        }
    ]

    prepared = posts_generator._prepare_articles_for_filtering(candidate_posts)

    assert len(prepared) == 1
    assert prepared[0]["id"] == "123"  # Should be converted to string
    assert "title" in prepared[0]
    assert "subtitle" in prepared[0]
    assert "url" in prepared[0]
    assert "content" in prepared[0]


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_evaluate_single_article(mock_agent, posts_generator):
    """Test individual article evaluation."""
    # Mock the agent response
    mock_run = MagicMock()
    mock_run.output = "YES"

    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    article = {
        "id": "1",
        "title": "Great Article",
        "subtitle": "Interesting subtitle",
        "content": "This is compelling content that would make a great LinkedIn post."
    }

    result = await posts_generator._evaluate_single_article(
        article, "Software engineer", ["tech", "ai"]
    )

    assert result is True
    mock_agent.return_value.run.assert_called_once()


@pytest.mark.asyncio
@patch("posts_generator.Agent")
async def test_filter_articles_individual_processing(mock_agent, posts_generator):
    """Test filtering with individual processing and shuffling."""
    # Mock the agent response to select articles
    mock_run = MagicMock()
    mock_run.output = "YES"

    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    candidate_posts = [
        {"id": "1", "title": "Article 1", "content": "Great content"},
        {"id": "2", "title": "Article 2", "content": "Another content"},
        {"id": "3", "title": "Article 3", "content": "More content"},
    ]

    filtered = await posts_generator.filter_articles(
        candidate_posts, "bio", ["tech"], 2
    )

    # Should return up to 2 articles (since we mock YES for all)
    assert len(filtered) == 2
    # Original content should be preserved
    assert all("content" in article for article in filtered)
    # Agent should be called for evaluation
    assert mock_agent.return_value.run.call_count >= 2


def test_remove_duplicate_posts():
    """Test the remove_duplicate_posts function."""
    # Test with no duplicates
    posts_no_duplicates = [
        {"id": "1", "title": "Article 1"},
        {"id": "2", "title": "Article 2"},
        {"id": "3", "title": "Article 3"},
    ]
    result = remove_duplicate_posts(posts_no_duplicates)
    assert len(result) == 3

    # Test with string duplicates
    posts_with_duplicates = [
        {"id": "1", "title": "Article 1"},
        {"id": "2", "title": "Article 2"},
        {"id": "1", "title": "Article 1 Duplicate"},
        {"id": "3", "title": "Article 3"},
    ]
    result = remove_duplicate_posts(posts_with_duplicates)
    assert len(result) == 3
    # Check that first occurrence is kept
    titles = [post["title"] for post in result]
    assert "Article 1" in titles
    assert "Article 1 Duplicate" not in titles

    # Test with UUID duplicates
    uuid1 = UUID("12345678-1234-5678-9012-123456789012")
    uuid2 = UUID("87654321-4321-8765-2109-876543210987")
    posts_uuid_duplicates = [
        {"id": uuid1, "title": "Article UUID 1"},
        {"id": uuid2, "title": "Article UUID 2"},
        {"id": uuid1, "title": "Article UUID 1 Duplicate"},
    ]
    result = remove_duplicate_posts(posts_uuid_duplicates)
    assert len(result) == 2

    # Test with mixed ID types (string and UUID representing same value)
    uuid_str = "12345678-1234-5678-9012-123456789012"
    uuid_obj = UUID(uuid_str)
    posts_mixed_types = [
        {"id": uuid_str, "title": "Article String ID"},
        {"id": uuid_obj, "title": "Article UUID ID"},
    ]
    result = remove_duplicate_posts(posts_mixed_types)
    assert len(result) == 1  # Should be treated as duplicates

    # Test with empty list
    result = remove_duplicate_posts([])
    assert len(result) == 0

    # Test with posts missing ID
    posts_missing_id = [
        {"id": "1", "title": "Article 1"},
        {"title": "Article No ID"},  # Missing ID
        {"id": "2", "title": "Article 2"},
    ]
    result = remove_duplicate_posts(posts_missing_id)
    assert len(result) == 3  # All should be kept

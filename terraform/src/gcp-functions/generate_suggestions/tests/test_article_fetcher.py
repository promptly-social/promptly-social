import sys
import os
import pytest
import responses
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from article_fetcher import ArticleFetcher, RecommendedArticle


@pytest.fixture
def article_fetcher():
    """Fixture to initialize ArticleFetcher with dummy keys."""
    with patch.dict(
        os.environ,
        {"ZYTE_API_KEY": "test_zyte_key", "OPENROUTER_API_KEY": "test_openrouter_key"},
    ):
        fetcher = ArticleFetcher()
    return fetcher


def test_format_url(article_fetcher):
    assert article_fetcher._format_url("example.com") == "https://example.com"
    assert article_fetcher._format_url("http://example.com") == "https://example.com"
    assert article_fetcher._format_url("https://example.com") == "https://example.com"
    assert (
        article_fetcher._format_url("example.com", is_substack=True)
        == "https://example.com/archive"
    )
    assert (
        article_fetcher._format_url("example.com/", is_substack=True)
        == "https://example.com/archive"
    )
    assert (
        article_fetcher._format_url("example.com/archive", is_substack=True)
        == "https://example.com/archive"
    )


@responses.activate
def test_fetch_article_list_success(article_fetcher):
    responses.add(
        responses.POST,
        article_fetcher.zyte_api_url,
        json={
            "articleList": {
                "articles": [
                    {
                        "headline": "Test Title",
                        "url": "http://example.com/article",
                        "datePublished": datetime.now().isoformat(),
                    }
                ]
            }
        },
        status=200,
    )
    articles = article_fetcher._fetch_article_list("http://example.com")
    assert len(articles) == 1
    assert articles[0]["title"] == "Test Title"


@responses.activate
def test_fetch_article_list_filters_old_articles(article_fetcher):
    four_days_ago = (datetime.now() - timedelta(days=4)).isoformat()
    responses.add(
        responses.POST,
        article_fetcher.zyte_api_url,
        json={
            "articleList": {
                "articles": [
                    {
                        "headline": "Old Title",
                        "url": "http://example.com/old",
                        "datePublished": four_days_ago,
                    }
                ]
            }
        },
        status=200,
    )
    articles = article_fetcher._fetch_article_list("http://example.com")
    assert len(articles) == 0


@responses.activate
def test_fetch_article_list_api_error(article_fetcher):
    responses.add(responses.POST, article_fetcher.zyte_api_url, status=500)
    articles = article_fetcher._fetch_article_list("http://example.com")
    assert articles == []


@responses.activate
def test_scrape_article_content_success(article_fetcher):
    responses.add(
        responses.POST,
        article_fetcher.zyte_api_url,
        json={
            "article": {
                "articleBody": "Full content",
                "datePublished": datetime.now().isoformat(),
            }
        },
        status=200,
    )
    content = article_fetcher._scrape_article_content("http://example.com/article")
    assert content["content"] == "Full content"
    assert content["post_date"] != ""


@responses.activate
def test_scrape_article_content_failure(article_fetcher):
    responses.add(responses.POST, article_fetcher.zyte_api_url, status=500)
    content = article_fetcher._scrape_article_content("http://example.com/article")
    assert content == {"content": "", "post_date": ""}


@pytest.mark.asyncio
@patch("article_fetcher.Agent")
async def test_filter_articles_by_user_preferences(mock_agent, article_fetcher):
    mock_run = MagicMock()
    mock_run.output = [
        RecommendedArticle(
            article_url="http://example.com/article1",
            title="Article 1",
            subtitle="",
            content="",
            post_date="",
        ),
    ]

    async def mock_run_async(*args, **kwargs):
        return mock_run

    mock_agent.return_value.run = MagicMock(side_effect=mock_run_async)

    articles = [{"url": "http://example.com/article1", "title": "Article 1"}]
    user_topics = ["tech"]
    bio = "A tech enthusiast."

    result = await article_fetcher._filter_articles_by_user_preferences(
        articles, user_topics, bio, 1
    )

    assert len(result) == 1
    assert result[0].title == "Article 1"
    mock_agent.return_value.run.assert_called_once()


@pytest.mark.asyncio
async def test_filter_articles_by_user_preferences_empty_input(article_fetcher):
    result = await article_fetcher._filter_articles_by_user_preferences(
        [], ["tech"], "bio", 1
    )
    assert result == []


@pytest.mark.asyncio
@patch.object(ArticleFetcher, "_fetch_article_list")
@patch.object(ArticleFetcher, "_filter_articles_by_user_preferences")
@patch.object(ArticleFetcher, "_scrape_article_content")
async def test_fetch_candidate_articles(
    mock_scrape, mock_filter, mock_fetch_list, article_fetcher
):
    mock_fetch_list.return_value = [
        {"url": "http://example.com/a1", "title": "Title 1"}
    ]

    mock_filtered_article = RecommendedArticle(
        article_url="http://example.com/a1",
        title="Title 1",
        subtitle="Subtitle 1",
        content="",
        post_date="2023-01-01",
    )

    async def mock_filter_async(*args, **kwargs):
        return [mock_filtered_article]

    mock_filter.side_effect = mock_filter_async

    mock_scrape.return_value = {"content": "Full content", "post_date": "2023-01-01"}

    result = await article_fetcher.fetch_candidate_articles(
        ["http://example.com"],
        user_topics_of_interest=["tech"],
        bio="A bio",
        sample_size=1,
    )

    assert len(result) == 1
    assert result[0]["content"] == "Full content"
    mock_fetch_list.assert_called_once()
    mock_filter.assert_called_once_with(
        mock_fetch_list.return_value, ["tech"], "A bio", 1
    )
    mock_scrape.assert_called_once_with("http://example.com/a1")

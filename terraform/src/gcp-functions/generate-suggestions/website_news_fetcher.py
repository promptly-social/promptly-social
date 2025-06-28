import os
import requests
from typing import Dict, Any, List
from datetime import datetime, timezone
import logging
import random

from openai import OpenAI
from helper import extract_json_from_llm_response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebsiteNewsFetcher:
    def __init__(
        self,
        openrouter_api_key: str = None,
        zyte_api_key: str = None,
        max_workers: int = 2,
    ):
        """Initialize the Website News Fetcher with Zyte API."""
        self.max_workers = max_workers
        self.zyte_api_key = zyte_api_key or os.getenv("ZYTE_API_KEY")

        # OpenRouter client for content filtering
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key or os.getenv("OPENROUTER_API_KEY"),
        )

        # Get model configuration from environment variables
        self.model_primary = os.getenv(
            "OPENROUTER_MODEL_PRIMARY", "google/gemini-2.5-flash-preview-05-20"
        )
        models_fallback_str = os.getenv(
            "OPENROUTER_MODELS_FALLBACK", "google/gemini-2.5-flash"
        )
        self.models_fallback = [
            model.strip() for model in models_fallback_str.split(",")
        ]
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.0"))

        # API endpoints
        self.zyte_api_url = "https://api.zyte.com/v1/extract"

        if not self.zyte_api_key:
            logger.warning("ZYTE_API_KEY not found in environment variables")

    def _parse_date_to_utc(self, date_string: str) -> str:
        """
        Parse date string to UTC format.
        Handles various date formats and returns ISO format UTC string.
        """
        if not date_string:
            return ""

        try:
            # Common date formats to try
            date_formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds
                "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format with microseconds and timezone offset
                "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds without Z
                "%Y-%m-%dT%H:%M:%SZ",  # ISO format
                "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone offset
                "%Y-%m-%dT%H:%M:%S",  # ISO format without Z
                "%Y-%m-%d %H:%M:%S",  # Standard datetime
                "%Y-%m-%d",  # Date only
                "%B %d, %Y",  # Month DD, YYYY
                "%d %B %Y",  # DD Month YYYY
            ]

            parsed_date = None
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string.strip(), date_format)
                    break
                except ValueError:
                    continue

            if parsed_date:
                # Convert to UTC ISO format
                if parsed_date.tzinfo is not None:
                    # Convert timezone-aware datetime to UTC
                    utc_date = parsed_date.astimezone(timezone.utc)
                else:
                    # Assume naive datetime is UTC
                    utc_date = parsed_date.replace(tzinfo=timezone.utc)

                return utc_date.isoformat()
            else:
                # If we can't parse it, return the original string
                logger.warning(f"Could not parse date format: {date_string}")
                return date_string

        except Exception as e:
            logger.error(f"Error parsing date '{date_string}': {str(e)}")
            return date_string

    def fetch_news(
        self, website_urls: list[str], user_topics_of_interest: list[str], bio: str
    ) -> list[Dict[str, Any]]:
        """
        Fetch news from the website urls using Zyte API.
        """
        all_articles = []
        if not website_urls:
            return []

        for website_url in website_urls:
            try:
                # Step 1: Get article list from website using Zyte
                articles = self._get_articles_from_website(website_url)

                # Step 2: Filter articles by user preferences
                filtered_articles = self._filter_articles_by_user_preferences(
                    articles, user_topics_of_interest, bio
                )

                all_articles.extend(filtered_articles)

            except Exception as e:
                logger.error(f"Error processing website {website_url}: {str(e)}")
                continue

        return all_articles

    def _get_articles_from_website(self, website_url: str) -> List[Dict[str, Any]]:
        """
        Use Zyte API to get a list of articles from a website.
        """
        if not self.zyte_api_key:
            logger.error("Zyte API key not available")
            return []

        try:
            headers = {"Content-Type": "application/json"}

            payload = {
                "url": website_url,
                "httpResponseBody": True,
                "articleList": True,
                "articleListOptions": {"extractFrom": "httpResponseBody"},
                "followRedirect": True,
            }

            response = requests.post(
                self.zyte_api_url,
                headers=headers,
                json=payload,
                auth=(
                    self.zyte_api_key,
                    "",
                ),
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()

                # Extract article list
                articles_list = data.get("articleList", [])
                articles = articles_list.get("articles", [])

                parsed_articles = []

                for article in articles:
                    # Parse and convert date to UTC
                    raw_date = article.get("datePublished", "")
                    parsed_date = self._parse_date_to_utc(raw_date) if raw_date else ""

                    article_data = {
                        "url": article.get("url", ""),
                        "title": article.get("headline", ""),
                        "subtitle": article.get("description", ""),
                        "content": article.get("articleBody", ""),
                        "post_date": parsed_date,
                        "time_sensitive": False,  # Will be determined during filtering
                    }

                    if article_data["title"] and article_data["url"]:
                        parsed_articles.append(article_data)

                logger.info(f"Found {len(parsed_articles)} articles from {website_url}")

                article_sample = random.sample(parsed_articles, 20)

                logger.info("Randomly selecting up to 20 articles")

                logger.info(
                    f"Scraping article content for {len(article_sample)} articles"
                )
                candidate_articles = []
                for article in article_sample:
                    article_content = self._scrape_article_content(article["url"])
                    article["content"] = article_content["content"]
                    article["post_date"] = article_content["post_date"]
                    if article["content"]:
                        candidate_articles.append(article)

                return candidate_articles

            else:
                logger.warning(
                    f"Zyte API returned status {response.status_code} for {website_url}. Response: {response.text[:200]}..."
                )
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting articles from {website_url}: {str(e)}")
            return []
        except Exception as e:
            logger.error(
                f"Unexpected error getting articles from {website_url}: {str(e)}"
            )
            return []

    def _scrape_article_content(self, article_url: str) -> Dict[str, Any]:
        """
        Optionally scrape full content of a single article using Zyte API.
        This is used when we need the full article content for filtering.
        """
        try:
            headers = {"Content-Type": "application/json"}

            payload = {
                "url": article_url,
                "article": True,
                "httpResponseBody": True,
                "articleOptions": {"extractFrom": "httpResponseBody"},
                "followRedirect": True,
            }

            response = requests.post(
                self.zyte_api_url,
                headers=headers,
                json=payload,
                auth=(self.zyte_api_key, ""),
                timeout=60,
            )

            if response.status_code == 200:
                data = response.json()

                # Extract article content
                article = data.get("article", {})
                article_body = article.get("articleBody", "")
                date_published = article.get("datePublished", "")
                parsed_date = (
                    self._parse_date_to_utc(date_published) if date_published else ""
                )

                if article_body:
                    return {
                        "content": article_body,
                        "post_date": parsed_date,
                    }

            return {
                "content": "",
                "post_date": "",
            }

        except Exception as e:
            logger.error(f"Error scraping content for {article_url}: {str(e)}")
            return ""

    def _filter_articles_by_user_preferences(
        self,
        articles: List[Dict[str, Any]],
        user_topics_of_interest: List[str],
        bio: str,
    ) -> List[Dict[str, Any]]:
        """
        Filter articles by user preferences using OpenRouter.
        Similar to _filter_posts_by_user_preferences but for articles.
        """
        if not user_topics_of_interest or not articles:
            return articles

        matched_articles = []

        for article in articles:
            try:
                today = datetime.now().strftime("%Y-%m-%d")

                article_post_date = article.get("post_date", "Not available")

                prompt = f"""
                Today's date is {today}.
                You are an expert at selecting articles by user topics of interest and bio for the user to create engaging LinkedIn posts.
                You are given an article and a list of user topics of interest and a bio.
                Your task is to determine if the article matches the user topics of interest and bio, and if it would be appropriate for LinkedIn content.
                If the article is a match, determine if the topic is time sensitive or evergreen. 
                If it's time sensitive, for example an article about a new product launch, breaking news, or a recent event, then the time_sensitive field should be true.
                Return a json object with the following format:
                {{"match": true/false, "error": "", "time_sensitive": true/false}}
                
                The article is:
                Title: {article.get("title", "")}
                Subtitle: {article.get("subtitle", "")}
                Content: {article.get("content", "")}...
                URL: {article.get("url", "")}
                Date: {article_post_date}
                
                The user topics of interest are:
                {user_topics_of_interest}
                
                The bio is:
                {bio}
                """

                response = self.openrouter_client.chat.completions.create(
                    model=self.model_primary,
                    extra_body={
                        "models": self.models_fallback,
                    },
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )

                result = extract_json_from_llm_response(
                    response.choices[0].message.content
                )

                if result.get("match", False):
                    # Update article with time_sensitive information
                    article["time_sensitive"] = result.get("time_sensitive", False)
                    article["relevance_score"] = result.get("relevance_score", 5)
                    matched_articles.append(article)

            except Exception as e:
                logger.error(
                    f"Error filtering article {article.get('url', '')}: {str(e)}"
                )
                continue

        # Sort by relevance score (highest first)
        matched_articles.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        logger.info(
            f"Filtered {len(matched_articles)} relevant articles from {len(articles)} total"
        )
        return matched_articles

    def _analyze_website_for_news(
        self, website_url: str, user_topics_of_interest: list[str], bio: str
    ) -> list[Dict[str, Any]]:
        """
        Legacy method - now redirects to the new Zyte-only implementation.
        Kept for backward compatibility.
        """
        return self.fetch_news([website_url], user_topics_of_interest, bio)

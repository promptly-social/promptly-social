import os
import requests
from typing import Dict, Any, List, Optional
import logging
import random
from datetime import datetime, timezone
from helper import parse_date_to_utc
from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai import Agent


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendedArticle(BaseModel):
    """Schema for the recommended article."""

    article_url: str = Field(description="The URL of the recommended article.")
    title: str = Field(description="The title of the recommended article.")
    subtitle: str = Field(description="The subtitle of the recommended article.")
    content: Optional[str] = Field(
        description="The content of the recommended article."
    )
    post_date: Optional[str] = Field(description="The date of the recommended article.")


class ArticleFetcher:
    def __init__(self):
        self.zyte_api_key = os.getenv("ZYTE_API_KEY")
        self.zyte_api_url = "https://api.zyte.com/v1/extract"

        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.zyte_api_key:
            logger.warning("ZYTE_API_KEY not found in environment variables")

        if not self.openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment variables")

        self.openrouter_model_primary = os.getenv(
            "OPENROUTER_MODEL_PRIMARY", "google/gemini-2.5-flash"
        )
        openrouter_models_fallback_str = os.getenv(
            "OPENROUTER_MODELS_FALLBACK", "deepseek/deepseek-chat-v3-0324"
        )
        self.openrouter_models_fallback = [
            model.strip() for model in openrouter_models_fallback_str.split(",")
        ]
        self.openrouter_model_temperature = float(
            os.getenv("OPENROUTER_MODEL_TEMPERATURE", "0.0")
        )

    def _format_url(self, url: str, is_substack: bool = False) -> str:
        """
        Formats a URL to ensure it starts with "https://" and, if it's a
        Substack URL, ends with "/archive".

        Args:
            url: The input URL string.
            is_substack: A boolean flag to indicate if the URL is for Substack.
                        Defaults to False.

        Returns:
            The formatted URL string.
        """
        # 1. Ensure the URL starts with "https://".
        if not url.startswith("https://"):
            # We also check for "http://" to avoid creating "https://http://..."
            if url.startswith("http://"):
                url = url.replace("http://", "https://", 1)
            else:
                url = "https://" + url

        # 2. If it's a Substack URL, ensure it ends with "/archive".
        if is_substack:
            # First, remove any trailing slashes to prevent "//archive".
            url = url.rstrip("/")

            # Then, append "/archive" if it's not already there.
            if not url.endswith("/archive"):
                url += "/archive"

        return url

    async def fetch_candidate_articles(
        self,
        website_urls: list[str],
        user_topics_of_interest: list[str],
        bio: str,
        sample_size: int = 10,
        is_substack: bool = False,
    ) -> list[dict]:
        articles = []

        website_sample_size = 50 if len(website_urls) > 50 else len(website_urls)

        for url in random.sample(website_urls, website_sample_size):
            articles.extend(self._fetch_article_list(url, is_substack))

        # use LLM to filter the articles by user preferences
        sampled_articles = await self._filter_articles_by_user_preferences(
            articles,
            user_topics_of_interest,
            bio,
            sample_size,
        )

        scraped_articles = []
        for article in sampled_articles:
            article_content = self._scrape_article_content(article.article_url)
            if article_content["content"] and article_content["post_date"]:
                article_content["url"] = article.article_url
                article_content["title"] = article.title
                article_content["subtitle"] = article.subtitle
                scraped_articles.append(article_content)

        return scraped_articles

    def _fetch_article_list(
        self,
        url: str,
        is_substack: bool = False,
    ) -> str:
        website_url = self._format_url(url, is_substack)

        try:
            headers = {"Content-Type": "application/json"}

            # if is_substack, we need to use the browserHtml option
            # otherwise, we use the httpResponseBody option by default, since it's cheaper
            payload = (
                {
                    "url": website_url,
                    "browserHtml": True,
                    "articleList": True,
                    "articleListOptions": {"extractFrom": "browserHtml"},
                }
                if is_substack
                else {
                    "url": website_url,
                    "httpResponseBody": True,
                    "articleList": True,
                    "articleListOptions": {"extractFrom": "httpResponseBody"},
                }
            )

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

                # if is_substack, we only need the first article
                if is_substack:
                    articles = articles[:1]

                parsed_articles = []

                for article in articles:
                    # Parse and convert date to UTC
                    raw_date = article.get("datePublished", "")
                    parsed_date = parse_date_to_utc(raw_date) if raw_date else ""

                    # skip the article if it's more than 3 days old
                    if (
                        parsed_date
                        and (
                            datetime.now(timezone.utc)
                            - datetime.fromisoformat(parsed_date.replace("Z", "+00:00"))
                        ).days
                        > 3
                    ):
                        continue

                    article_data = {
                        "url": article.get("url", ""),
                        "title": article.get("headline", ""),
                        "subtitle": article.get("description", ""),
                        "content": article.get("articleBody", ""),
                        "post_date": parsed_date,
                    }

                    if article_data["title"] and article_data["url"]:
                        parsed_articles.append(article_data)

                logger.info(f"Found {len(parsed_articles)} articles from {website_url}")

                return parsed_articles

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
                    parse_date_to_utc(date_published) if date_published else ""
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

    async def _filter_articles_by_user_preferences(
        self,
        articles: list[dict],
        user_topics_of_interest: list[str],
        bio: str,
        number_of_articles_to_select: int = 10,
    ) -> list[RecommendedArticle]:
        """
        Filter articles by user preferences.
        """
        if not articles:
            return []

        try:
            prompt = f"""You are an expert Content Strategist who helps thought leaders find compelling articles to use as inspiration for creating engaging LinkedIn posts. Your goal is to select articles that will spark discussion, showcase expertise, and resonate with a professional audience.

**User Profile:**
- **Bio:** {bio}
- **Topics of Interest:** {user_topics_of_interest}

**Candidate Articles:**
You will be given a list of articles, each with a title, description, and URL.
{articles}

**Your Task:**
From the list of candidate articles, select UP TO {number_of_articles_to_select} that are BEST suited for creating high-engagement LinkedIn posts.

**Selection Criteria (What to look for):**
- **Thought-Provoking Content:** Does the article present a strong opinion, a unique perspective, or deep analysis? Does it challenge common wisdom?
- **Conversation Starter:** Can the user add their own experience or opinion to it easily? Will it encourage comments and debate?
- **Relevance to User's Expertise:** Does it align with the user's bio and topics of interest, positioning them as an expert?
- **Broader Appeal:** Does it discuss a trend, a strategy, or a timeless concept rather than being a niche product update?

**What to AVOID (Very Important):**
- **Software Updates & Product Announcements:** Do not select articles that are just about a new version release, a new feature, or a product launch. These are generally poor for engagement. For example, avoid titles like "Announcing Product X v2.4".
- **Simple News Reports or Press Releases:** Avoid articles that just state facts without providing analysis or opinion. For example, avoid "Company ABC Acquires Company XYZ".
- **Hiring Announcements or Company-specific News:** Avoid articles that are only relevant to one company's internal affairs.

**Instructions:**
1. Carefully analyze each article in the provided list against the criteria above.
2. Select the top {number_of_articles_to_select} articles that best match.
3. Return a list results in the required JSON format.
"""

            model = OpenAIModel(
                self.openrouter_model_primary,
                provider=OpenRouterProvider(
                    api_key=self.openrouter_api_key,
                ),
            )

            agent = Agent(
                model,
                output_type=List[RecommendedArticle],
                model_settings=OpenAIModelSettings(
                    temperature=self.openrouter_model_temperature,
                    extra_body={"models": self.openrouter_models_fallback},
                ),
            )

            result = await agent.run(prompt)

            return result.output

        except Exception as e:
            logger.error(f"Error filtering articles: {str(e)}")
            return []

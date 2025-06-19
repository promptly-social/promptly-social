"""
Substack Content Analysis Module

This module contains the core logic for analyzing Substack content.
It fetches Substack newsletters, parses content, and performs NLP analysis.
"""

import logging
import json
from typing import Dict, List, Any

from openai import OpenAI
from substack_api import User, Newsletter

logger = logging.getLogger(__name__)


class SubstackAnalyzer:
    """Analyzes Substack publications for writing style and content patterns."""

    def __init__(self, max_posts: int = 10, openrouter_api_key: str = None):
        self.max_posts = max_posts
        self.user = None
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

    def analyze_substack(self, platform_username: str) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the full analysis process.

        Args:
            platform_username: The Substack username (e.g., 'username' for username.substack.com)

        Returns:
            Complete analysis results dictionary
        """
        logger.info(f"Starting comprehensive analysis for {platform_username}")

        try:
            # Initialize a user by their username
            self.user = User(platform_username)

            try:
                self.user.get_raw_data()
            except Exception as e:
                logger.error(f"Error getting raw data for {platform_username}: {e}")
                # TODO: surface the error to the user
                return self._create_empty_analysis(platform_username)

            # Step 1: get a list of subscriptions, and persist them to the database
            subscriptions = self.user.get_subscriptions()
            websites = [
                f"https://{subscription['domain']}" for subscription in subscriptions
            ]

            # Step 2: get a list of post URLs from user's subscriptions
            subscription_posts = []
            for website in websites:
                subscription_posts.extend(self._fetch_substack_posts(website))

            # Step 3: get a list of post URLs from user's newsletter
            newsletter_url = f"https://{platform_username}.substack.com"
            newsletter_posts = self._fetch_substack_posts(newsletter_url)

            # Step 4: combine the two lists to generate a list of topics
            posts = subscription_posts + newsletter_posts

            topics = self._analyze_topics(posts)

            # Step 5 Analyze writing style
            writing_style = self._analyze_writing_style(newsletter_posts)

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "writing_content_count": len(newsletter_posts),
                "topics": topics,
                "websites": websites,
            }

            logger.info(f"Substack analysis completed for {platform_username}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing {platform_username}: {e}")
            raise

    def _fetch_substack_posts(self, url: str) -> List[Dict[str, Any]]:
        """Fetch posts from Substack newsletter."""

        try:
            newsletter = Newsletter(url)
            recent_posts = newsletter.get_posts(limit=self.max_posts)

            posts = []
            for post in recent_posts:
                posts.append(post.url)

            return posts

        except Exception as e:
            logger.error(f"Error fetching posts for {url}: {e}")
            return []

    def _analyze_writing_style(self, posts: List[Dict]) -> str:
        """Analyze writing style of posts."""
        if not posts:
            return ""

        urls = "\n".join(posts)
        prompt = f"""
        You are an expert at analyzing writing style of a list of posts of an author.
        You are given a list of URLs to posts.
        Your task is to analyze the writing style of the posts.
        Return the writing style analysis in plain text format. Each sentence should be on a new line.
        URLs: {urls}
        """

        response = self.openrouter_client.chat.completions.create(
            model="google/gemini-2.5-pro",
            extra_body={
                "models": ["openai/gpt-4o"],
            },
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        return response.choices[0].message.content

    def _analyze_topics(self, posts: List[Dict]) -> List[str]:
        """Extract main topics from posts by processing in batches."""
        if not posts:
            return []

        # Split posts into batches of 20
        batch_size = 20
        post_batches = [
            posts[i : i + batch_size] for i in range(0, len(posts), batch_size)
        ]

        all_topics = []

        for i, batch in enumerate(post_batches):
            logger.info(
                f"Processing batch {i + 1}/{len(post_batches)} with {len(batch)} posts"
            )

            try:
                batch_topics = self._analyze_topics_batch(batch)
                all_topics.extend(batch_topics)
            except Exception as e:
                logger.error(f"Error processing batch {i + 1}: {e}")
                continue

        # Merge and deduplicate topics
        unique_topics = list(set(all_topics))
        logger.info(
            f"Extracted {len(unique_topics)} unique topics from {len(posts)} posts"
        )

        return unique_topics

    def _analyze_topics_batch(self, posts: List[str]) -> List[str]:
        """Extract main topics from a batch of posts."""
        urls = "\n".join(posts)
        prompt = f"""
        You are an expert at analyzing topics from a list of posts and websites.
        You are given a list of URLs to posts and websites.
        Your task is to extract the main topics from the posts and websites.
        Return a list of short topics without descriptions, such as AI, startups, technology, etc in a JSON format like this : {{"topics": [], "error": ""}}
        If you cannot extract the topics, return an empty list.
        URLs: {urls}
        """

        response = self.openrouter_client.chat.completions.create(
            model="google/gemini-2.5-pro",
            extra_body={
                "models": ["openai/gpt-4o"],
            },
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        raw_content = response.choices[0].message.content
        print(raw_content)
        content_json = self._extract_json_from_llm_response(raw_content)

        if content_json.get("error"):
            logger.error(
                f"Error extracting topics from batch: {content_json.get('error')}"
            )

        return content_json.get("topics", [])

    def _create_empty_analysis(self, username: str) -> Dict[str, Any]:
        """Create empty analysis result when no posts are found."""
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
            "writing_content_count": 0,
        }

    def _extract_json_from_llm_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            # Remove any markdown formatting
            response = response.replace("```json", "").replace("```", "")
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error extracting JSON from response: {e}")
            return {}

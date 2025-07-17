"""
Substack Content Analysis Module

This module contains the core logic for analyzing Substack content.
It fetches Substack newsletters, parses content, and performs NLP analysis.
"""

import logging
import json
from typing import Dict, List, Any
import random

from llm_client import LLMClient
from prompt_templates import writing_style_substack, topics_substack, bio_substack
from substack_api import User, Newsletter

logger = logging.getLogger(__name__)


class SubstackAnalyzer:
    """Analyzes Substack publications for writing style and content patterns."""

    def __init__(self, max_posts: int = 10, openrouter_api_key: str = None):
        self.max_posts = max_posts
        self.user = None
        # Centralized LLM client (shared config across functions)
        self.llm_client = LLMClient()

    def analyze_substack(
        self,
        platform_username: str,
        current_bio: str,
        content_to_analyze: List[str],
        current_writing_style: str = "",
    ) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the full analysis process.

        Args:
            platform_username: The Substack username (e.g., 'username' for username.substack.com)
            current_bio: The current bio of the user
            content_to_analyze: A list of content to analyze, such as bio, topics, substacks, writing_style, etc.

        Returns:
            Complete analysis results dictionary
        """
        logger.debug(
            f"Starting comprehensive analysis for {platform_username} on {', '.join(content_to_analyze)}"
        )

        try:
            # Initialize a user by their username
            self.user = User(platform_username)

            try:
                self.user.get_raw_data()
            except Exception as e:
                logger.error(f"Error getting raw data for {platform_username}: {e}")
                return self._create_empty_analysis(platform_username)

            topics = []
            substacks = []

            if "interests" in content_to_analyze or "substacks" in content_to_analyze:
                # Step 1: get a list of subscriptions
                subscriptions = self.user.get_subscriptions()
                substacks = [
                    f"https://{subscription['domain']}"
                    for subscription in subscriptions
                ]
                logger.debug(f"Substack subscriptions fetched: {len(substacks)}")

                # Step 2: get a list of post URLs from user's subscriptions
                subscription_posts = []
                for substack in substacks:
                    subscription_posts.extend(self._fetch_substack_posts(substack))

                # randomly sample 100 posts at most from the list of posts to avoid rate limiting and costs
                # this should be enough to get a good analysis of the user's content preferences
                subscription_posts_sample = random.sample(
                    subscription_posts, min(len(subscription_posts), 100)
                )

                topics = (
                    self._analyze_topics(subscription_posts_sample)
                    if "interests" in content_to_analyze
                    else []
                )
                substacks = (
                    substacks  # Return the full list of subscribed substacks
                    if "substacks" in content_to_analyze
                    else []
                )

            bio = current_bio
            if "bio" in content_to_analyze:
                substack_bio = self.user.get_raw_data().get("bio", "")
                newsletter_url = f"https://{platform_username}.substack.com"
                newsletter_posts = self._fetch_substack_posts(newsletter_url)
                logger.debug(
                    f"Substack newsletter URL: {newsletter_url}, posts: {len(newsletter_posts)}"
                )

                bio = self._create_user_bio(newsletter_posts, substack_bio, current_bio)

            writing_style = ""
            if "writing_style" in content_to_analyze:
                newsletter_url = f"https://{platform_username}.substack.com"
                newsletter_posts = self._fetch_substack_posts(newsletter_url)
                logger.debug(
                    f"Substack newsletter URL: {newsletter_url}, posts: {len(newsletter_posts)}"
                )

                # Step 5 analyze writing style (update existing if provided)
                writing_style = self._analyze_writing_style(
                    newsletter_posts, current_writing_style
                )

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "topics": topics,
                "substacks": substacks,
                "bio": bio,
            }

            logger.debug(
                f"Substack analysis completed for {platform_username} on {', '.join(content_to_analyze)}"
            )
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

    def _analyze_writing_style(
        self, posts: List[Dict], current_writing_style: str = ""
    ) -> str:
        """Analyze writing style of posts."""
        if not posts:
            logger.debug("No posts provided for writing style analysis")
            return ""

        prompt = writing_style_substack(posts, current_writing_style)
        try:
            return self.llm_client.run_prompt(prompt)
        except Exception as e:
            logger.error(f"Error analyzing/updating writing style: {e}")
            return current_writing_style

    def _analyze_topics(self, posts: List[Dict]) -> List[str]:
        """Extract main topics from posts by processing in batches."""
        if not posts:
            logger.debug("No posts provided for topics analysis")
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
        if not posts:
            return []

        prompt = topics_substack(posts)

        try:
            raw_response = self.llm_client.run_prompt(prompt)
            content_json = self._extract_json_from_llm_response(raw_response)
            if content_json.get("error"):
                logger.error(
                    "Error extracting topics from batch: %s, raw content: %s",
                    content_json.get("error"),
                    raw_response,
                )
            return content_json.get("topics", [])
        except Exception as e:
            logger.error("LLM error extracting topics: %s", e)
            return []

    def _create_user_bio(
        self,
        posts: List[Dict],
        substack_bio: str,
        current_bio: str,
    ) -> str:
        """Create a user bio from a list of posts and a current bio."""
        if not posts:
            logger.error("No posts provided for user bio creation")
            return substack_bio or current_bio

        prompt = bio_substack(posts, substack_bio, current_bio)

        try:
            return self.llm_client.run_prompt(prompt)
        except Exception as e:
            logger.error(f"Error creating/updating user bio: {e}")
            return substack_bio or current_bio

    def _create_empty_analysis(self, username: str) -> Dict[str, Any]:
        """Create empty analysis result when no posts are found."""
        return {
            "writing_style": "",
            "topics": [],
            "substacks": [],
            "bio": "",
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

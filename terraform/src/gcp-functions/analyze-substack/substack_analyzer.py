"""
Substack Content Analysis Module

This module contains the core logic for analyzing Substack content.
It fetches Substack newsletters, parses content, and performs NLP analysis.
"""

import logging
import json
from typing import Dict, List, Any
import random

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

    def analyze_substack(
        self, platform_username: str, current_bio: str, content_to_analyze: List[str]
    ) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the full analysis process.

        Args:
            platform_username: The Substack username (e.g., 'username' for username.substack.com)
            current_bio: The current bio of the user
            content_to_analyze: A list of content to analyze, such as bio, interests, writing_style, etc.

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
            websites = []

            if "interests" in content_to_analyze:
                # Step 1: get a list of subscriptions, and persist them to the database
                subscriptions = self.user.get_subscriptions()
                websites = [
                    f"https://{subscription['domain']}"
                    for subscription in subscriptions
                ]
                logger.debug(f"Substack subscriptions fetched: {len(websites)}")

                # Step 2: get a list of post URLs from user's subscriptions
                subscription_posts = []
                for website in websites:
                    subscription_posts.extend(self._fetch_substack_posts(website))

                # randomly sample 100 posts at most from the list of posts to avoid rate limiting and costs
                # this should be enough to get a good analysis of the user's content preferences
                subscription_posts_sample = random.sample(
                    subscription_posts, min(len(subscription_posts), 100)
                )

                topics = self._analyze_topics(subscription_posts_sample)

            bio = ""
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

                # Step 5 analyze writing style
                writing_style = self._analyze_writing_style(newsletter_posts)

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "topics": topics,
                "websites": websites,
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

    def _analyze_writing_style(self, posts: List[Dict]) -> str:
        """Analyze writing style of posts."""
        if not posts:
            logger.debug("No posts provided for writing style analysis")
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

        if not response.choices:
            logger.error("API call for writing style analysis returned no choices.")
            return ""

        return response.choices[0].message.content

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

        if not response.choices:
            logger.error("API call for topics batch analysis returned no choices.")
            return []

        raw_content = response.choices[0].message.content
        content_json = self._extract_json_from_llm_response(raw_content)

        if content_json.get("error"):
            logger.error(
                f"Error extracting topics from batch: {content_json.get('error')}, raw content: {raw_content}"
            )

        return content_json.get("topics", [])

    def _create_user_bio(
        self, posts: List[Dict], substack_bio: str, current_bio: str
    ) -> str:
        """Create a user bio from a list of posts and a current bio."""
        if not posts:
            logger.error("No posts provided for user bio creation")
            return substack_bio or current_bio

        urls = "\n".join(posts)
        prompt = f"""
        You are an expert at creating a user bio from a list of posts, their stubstack bio, and a current bio.
        You are given a list of URLs to posts and a current bio.
        Your task is to create a user bio from the posts and the current bio.
        Return the user bio in plain text format. The substack bio and current bio might be empyt or incomplete.
        If the substack bio and/or the current bio are given, update them based on your analysis.
        The user bio should be a short description of the user's interests, what they do, the roles they hold, what they're passionate about.
        This will be used as a persona for LLM to generate content in their style, preferences, and point of view.
        URLs: {urls}
        Substack bio: {substack_bio}
        Current bio: {current_bio}
        """

        response = self.openrouter_client.chat.completions.create(
            model="google/gemini-2.5-pro",
            extra_body={
                "models": ["openai/gpt-4o"],
            },
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )

        if not response.choices:
            logger.error("API call for user bio creation returned no choices.")
            return substack_bio or current_bio

        return response.choices[0].message.content

    def _create_empty_analysis(self, username: str) -> Dict[str, Any]:
        """Create empty analysis result when no posts are found."""
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
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

"""
LinkedIn Content Analysis Module

This module contains the core logic for analyzing LinkedIn content via web scraping.
It fetches LinkedIn posts, parses content, and performs NLP analysis.
"""

import logging
import os
from typing import Dict, List, Any
import httpx
import random

from openai import OpenAI

logger = logging.getLogger(__name__)


class LinkedInAnalyzer:
    """Analyzes LinkedIn publications for writing style and content patterns."""

    def __init__(
        self,
        max_posts: int = 20,
        openrouter_api_key: str = None,
    ):
        self.max_posts = max_posts
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
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

    def analyze_linkedin(
        self, account_id: str, current_bio: str, content_to_analyze: List[str]
    ) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the full LinkedIn analysis process.

        Args:
            account_id: The LinkedIn public profile name for the LinkedIn connection
            current_bio: The current bio of the user
            content_to_analyze: A list of content to analyze, such as bio, writing_style, etc.

        Returns:
            Complete analysis results dictionary
        """
        logger.debug(
            f"Starting comprehensive LinkedIn analysis for account {account_id} on {', '.join(content_to_analyze)}"
        )

        try:
            linkedin_user_id = self._fetch_linkedin_user_id(account_id)
            if not linkedin_user_id:
                logger.error(
                    f"Could not find LinkedIn user ID for account {account_id}"
                )
                return self._create_empty_analysis(account_id)

            # user's own linkedin posts
            user_linkedin_posts = self._fetch_linkedin_posts(
                account_id, linkedin_user_id
            )

            topics = []
            websites = []
            if "interests" in content_to_analyze:
                # Fetch user's comments and reactions for topic analysis
                commented_posts = self._fetch_linkedin_comments(
                    account_id, linkedin_user_id
                )
                reacted_posts = self._fetch_linkedin_reactions(
                    account_id, linkedin_user_id
                )

                # Get post texts from comments and reactions for topic analysis
                interaction_post_texts = self._fetch_interaction_post_texts(
                    account_id, commented_posts, reacted_posts, linkedin_user_id
                )

                # Analyze topics from user's own posts and posts they interacted with
                topics = self._analyze_topics(
                    user_linkedin_posts + interaction_post_texts
                )
                websites = []  # Empty for LinkedIn

            bio = current_bio
            if "bio" in content_to_analyze:
                # Fetch user profile and posts for bio analysis
                user_profile = self._fetch_linkedin_profile(
                    account_id, linkedin_user_id
                )

                bio = self._create_user_bio(
                    user_linkedin_posts, user_profile, current_bio
                )

            writing_style = ""
            if "writing_style" in content_to_analyze:
                logger.debug(
                    f"LinkedIn account: {account_id}, posts: {len(user_linkedin_posts)}"
                )

                # Analyze writing style
                writing_style = self._analyze_writing_style(user_linkedin_posts)

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "topics": topics,
                "websites": websites,
                "bio": bio,
            }

            logger.debug(
                f"LinkedIn analysis completed for account {account_id} on {', '.join(content_to_analyze)}"
            )
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing LinkedIn account {account_id}: {e}")
            raise

    def _fetch_paginated_data(
        self,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        description: str,
    ) -> List[Dict[str, Any]]:
        all_items = []

        try:
            # TODO: Implement Apify solution for this

            return all_items

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching {description}: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching {description}: {e}")
            return []

    def _fetch_linkedin_profile(
        self, account_id: str, linkedin_user_id: str
    ) -> Dict[str, Any]:
        try:
            # TODO: Implement Apify solution for this
            headline = ""
            summary = ""
            positions = []

            return {
                "headline": headline,
                "summary": summary,
                "positions": positions,
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching LinkedIn profile for {account_id}: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile for {account_id}: {e}")
            return None

    def _fetch_linkedin_posts(
        self, account_id: str, linkedin_user_id: str
    ) -> List[str]:
        try:
            # TODO: Implement Apify solution for this
            posts_content = []
            return posts_content

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching LinkedIn posts for {account_id}: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching LinkedIn posts for {account_id}: {e}")
            return []

    def _fetch_linkedin_comments(
        self, account_id: str, linkedin_user_id: str
    ) -> List[Dict[str, Any]]:
        try:
            # TODO: Implement Apify solution for this
            commented_posts = []
            return commented_posts

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching LinkedIn comments for {account_id}: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching LinkedIn comments for {account_id}: {e}")
            return []

    def _fetch_linkedin_reactions(
        self, account_id: str, linkedin_user_id: str
    ) -> List[Dict[str, Any]]:
        try:
            # TODO: Implement Apify solution for this
            reacted_posts = []
            return reacted_posts

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching LinkedIn reactions for {account_id}: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching LinkedIn reactions for {account_id}: {e}")
            return []

    def _fetch_interaction_post_texts(
        self,
        account_id: str,
        comments: List[str],
        reactions: List[str],
        linkedin_user_id: str,
    ) -> List[str]:
        post_texts = []
        post_ids = set()

        post_ids = list(set(comments + reactions))
        # randomly sample 50 posts at most from the list of posts to avoid rate limiting and high costs
        # this should be enough to get a good analysis of the user's content preferences
        post_ids_sample = random.sample(post_ids, min(len(post_ids), 50))

        if not post_ids:
            logger.debug("No post IDs found in comments or reactions")
            return []

        # TODO: Implement Apify solution for this
        for post_id in list(post_ids_sample):
            try:
                # TODO: Implement Apify solution for this
                post_data = {}

                # skip posts that the user didn't write
                if post_data.get("author", {}).get("id") == linkedin_user_id:
                    continue

                text = post_data.get("text", "")
                if text and text.strip():
                    post_texts.append(text)

            except httpx.HTTPStatusError as e:
                logger.warning(
                    f"Could not fetch post {post_id}: {e.response.status_code} - {e.response.text}"
                )
                continue
            except Exception as e:
                logger.warning(f"Error fetching post {post_id}: {e}")
                continue

        logger.debug(
            f"Fetched {len(post_texts)} post texts from {len(post_ids)} interactions for account {account_id}"
        )
        return post_texts

    def _analyze_topics(self, posts: List[str]) -> List[str]:
        """Analyze topics from LinkedIn posts and interactions by processing in batches."""
        if not posts:
            logger.debug("No posts provided for topic analysis")
            return []

        # Split posts into batches of 20
        batch_size = 20
        post_batches = [
            posts[i : i + batch_size] for i in range(0, len(posts), batch_size)
        ]

        all_topics = []

        for i, batch in enumerate(post_batches):
            logger.debug(
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
        logger.debug(
            f"Extracted {len(unique_topics)} unique topics from {len(posts)} posts"
        )

        # Limit to top 10 topics
        return unique_topics[:10]

    def _analyze_topics_batch(self, posts: List[str]) -> List[str]:
        """Analyze topics from a batch of LinkedIn posts."""
        # Combine posts in the batch
        combined_posts = "\n\n---\n\n".join(posts)

        prompt = f"""
        You are an expert at analyzing topics and themes that the user might be interested in from LinkedIn posts and interactions.
        You are given text content from LinkedIn posts that a user has written or interacted with (commented on or reacted to).
        Your task is to identify the main topics and themes that this user is interested in based on their content and interactions.
        Return a list of topics, one per line, focusing on professional interests, industry themes, and subject matters.
        Each topic should be 1-3 words maximum.
        
        LinkedIn Posts and Interactions:
        {combined_posts}
        """

        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model_primary,
                extra_body={
                    "models": self.models_fallback,
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            if not response.choices:
                logger.error("API call for topics batch analysis returned no choices.")
                return []

            topics_text = response.choices[0].message.content
            # Split by lines and clean up
            topics = [
                topic.strip() for topic in topics_text.split("\n") if topic.strip()
            ]
            # Remove any numbering or bullet points
            topics = [topic.lstrip("0123456789.- ") for topic in topics]
            # Filter out empty topics
            topics = [topic for topic in topics if topic]

            return topics

        except Exception as e:
            logger.error(f"Error analyzing topics batch: {e}")
            return []

    def _analyze_writing_style(self, posts: List[str]) -> str:
        """Analyze writing style of LinkedIn posts."""
        if not posts:
            logger.debug("No posts provided for writing style analysis")
            return ""

        # Combine posts with reasonable length limit
        combined_posts = "\n\n---\n\n".join(posts[:10])  # Limit to first 10 posts

        prompt = f"""
        You are an expert at analyzing writing style of LinkedIn posts of an author.
        You are given the text content of several LinkedIn posts.
        Your task is to analyze the writing style, tone, voice, and characteristics of this writing using gender neutral descriptions.
        Consider elements like:
        - Tone (formal, casual, conversational, etc.)
        - Voice (authoritative, friendly, analytical, etc.)
        - Sentence structure and length
        - Use of humor, metaphors, or storytelling
        - Technical vs. accessible language
        - Persuasive techniques
        - Overall personality that comes through in the writing
        
        Return the writing style analysis in plain text format without any markdown. Each observation should be on a new line.
        Be specific and provide actionable insights that could help someone write in a similar style.
        
        LinkedIn Posts:
        {combined_posts}
        """

        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model_primary,
                extra_body={
                    "models": self.models_fallback,
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            if not response.choices:
                logger.error("API call for writing style analysis returned no choices.")
                return ""

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing writing style: {e}")
            return ""

    def _create_user_bio(
        self, posts: List[str], linkedin_profile: Dict[str, Any], current_bio: str
    ) -> str:
        """Create a user bio from LinkedIn posts and profile information."""
        if not posts or not linkedin_profile:
            logger.debug("No posts or LinkedIn profile provided for user bio creation")
            return current_bio

        combined_posts = "\n\n---\n\n".join(posts)
        profile_text = ""
        for position in linkedin_profile.get("positions", []):
            profile_text += f"{position.get('position', '')} at {position.get('company', '')} from {position.get('start', '')} to {position.get('end', 'Present')}\n"
            profile_text += f"{position.get('description', '')}\n\n"

        prompt = f"""
        You are an expert at creating a user bio from LinkedIn posts, their LinkedIn profile, and a current bio.
        You are given LinkedIn post content and profile information.
        Your task is to create a user bio from the posts and the current bio, please use the first person perspective and gender neutral descriptions.
        Return the user bio in plain text format without any markdown. The LinkedIn profile and current bio might be empty or incomplete.
        If the LinkedIn profile and/or the current bio are given, update them based on your analysis.
        The user bio should be a short description of the user's interests, what they do, the roles they hold, what they're passionate about.
        This will be used as a persona for LLM to generate content in their style, preferences, and point of view.
        
        LinkedIn Posts:
        {combined_posts}
        
        LinkedIn Profile: {profile_text}
        Current Bio: {current_bio}
        """

        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model_primary,
                extra_body={
                    "models": self.models_fallback,
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            if not response.choices:
                logger.error("API call for user bio creation returned no choices.")
                return current_bio or linkedin_profile.get("summary", "")

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error creating user bio: {e}")
            return current_bio or linkedin_profile.get("summary", "")

    def _create_empty_analysis(self, account_id: str) -> Dict[str, Any]:
        """Create empty analysis result when no posts are found."""
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
            "bio": "",
        }

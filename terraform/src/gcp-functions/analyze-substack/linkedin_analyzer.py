"""
LinkedIn Content Analysis Module

This module contains the core logic for analyzing LinkedIn content via Unipile.
It fetches LinkedIn posts, parses content, and performs NLP analysis.
"""

import logging
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
        unipile_access_token: str = None,
        unipile_dsn: str = None,
    ):
        self.max_posts = max_posts
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        self.unipile_access_token = unipile_access_token
        self.unipile_dsn = unipile_dsn

    def analyze_linkedin(
        self, account_id: str, current_bio: str, content_to_analyze: List[str]
    ) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the full LinkedIn analysis process.

        Args:
            account_id: The Unipile account ID for the LinkedIn connection
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
        """Helper function to fetch paginated data from Unipile API."""
        all_items = []

        try:
            with httpx.Client() as client:
                logger.debug(f"Fetching {description}")

                response = client.get(url, headers=headers, params=params, timeout=60.0)
                response.raise_for_status()
                response_data = response.json()

                items = response_data.get("items", [])
                all_items.extend(items)

                cursor = response_data.get("cursor", "")
                while cursor:
                    logger.debug(f"Fetching more {description} with cursor {cursor}")
                    params["cursor"] = cursor

                    response = client.get(
                        url, headers=headers, params=params, timeout=60.0
                    )
                    response.raise_for_status()
                    response_data = response.json()

                    cursor = response_data.get("cursor", "")
                    items = response_data.get("items", [])
                    all_items.extend(items)

                logger.debug(f"Fetched {len(all_items)} total {description}")
                return all_items

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching {description}: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"Error fetching {description}: {e}")
            return []

    def _fetch_linkedin_user_id(self, account_id: str) -> Dict[str, Any]:
        """Fetch LinkedIn user ID via Unipile."""
        if not self.unipile_access_token or not self.unipile_dsn:
            logger.error("Unipile access token or DSN not configured")
            return None

        try:
            headers = {
                "X-API-KEY": self.unipile_access_token,
                "Content-Type": "application/json",
            }

            # Get account information first
            with httpx.Client() as client:
                response = client.get(
                    f"https://{self.unipile_dsn}/api/v1/accounts/{account_id}",
                    headers=headers,
                    timeout=30.0,
                )
                response.raise_for_status()
                account_data = response.json()

                # Extract LinkedIn user ID from account data
                connection_params = account_data.get("connection_params", {})
                im_data = connection_params.get("im", {})

                linkedin_candidates = [
                    (im_data.get("id"), "connection_params.im.id"),
                    (im_data.get("premiumId"), "connection_params.im.premiumId"),
                    (
                        im_data.get("publicIdentifier"),
                        "connection_params.im.publicIdentifier",
                    ),
                    (account_data.get("id"), "id"),
                ]

                linkedin_user_id = None
                for candidate_id, field_path in linkedin_candidates:
                    if (
                        candidate_id
                        and isinstance(candidate_id, str)
                        and (
                            candidate_id.startswith("ACo")
                            or candidate_id.startswith("ACw")
                        )
                    ):
                        linkedin_user_id = candidate_id
                        logger.debug(
                            f"Found LinkedIn user ID '{linkedin_user_id}' in field '{field_path}'"
                        )
                        break

                if not linkedin_user_id:
                    logger.error(
                        f"Could not find LinkedIn user ID (pattern ^AC(o|w).+$) in account data for {account_id}. "
                        f"Available fields: {list(account_data.keys())}"
                    )

                return linkedin_user_id

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error fetching LinkedIn profile for {account_id}: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile for {account_id}: {e}")
            return None

    def _fetch_linkedin_profile(
        self, account_id: str, linkedin_user_id: str
    ) -> Dict[str, Any]:
        """Fetch LinkedIn profile information via Unipile."""
        if not self.unipile_access_token or not self.unipile_dsn:
            logger.error("Unipile access token or DSN not configured")
            return None

        try:
            headers = {
                "X-API-KEY": self.unipile_access_token,
                "Content-Type": "application/json",
            }

            params = {"account_id": account_id, "linkedin_sections": "*"}

            with httpx.Client() as client:
                response = client.get(
                    f"https://{self.unipile_dsn}/api/v1/users/{linkedin_user_id}",
                    headers=headers,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                response_data = response.json()
                headline = response_data.get("headline", "")
                summary = response_data.get("summary", "")

                positions = []
                for position in response_data.get("work_experience", []):
                    positions.append(
                        {
                            "position": position.get("position", ""),
                            "company": position.get("company", ""),
                            "start": position.get("start", ""),
                            "end": position.get("end", "Present"),
                            "description": position.get("description", ""),
                        }
                    )

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
        """Fetch LinkedIn posts via Unipile."""
        if not self.unipile_access_token or not self.unipile_dsn:
            logger.error("Unipile access token or DSN not configured")
            return []

        try:
            headers = {
                "X-API-KEY": self.unipile_access_token,
                "Content-Type": "application/json",
            }

            params = {
                "account_id": account_id,
                "limit": self.max_posts
                * 2,  # fetch more posts to get more content since we are going to filter out reposts
            }

            url = f"https://{self.unipile_dsn}/api/v1/users/{linkedin_user_id}/posts"
            posts_data = self._fetch_paginated_data(
                url,
                headers,
                params,
                f"posts for user {linkedin_user_id} with account {account_id}",
            )

            # Extract text content from posts
            posts_content = []
            for post in posts_data:
                # Skip reposts to get original content only
                if post.get("is_repost"):
                    continue

                text = post.get("text", "")
                if text and text.strip():
                    posts_content.append(text)

            posts_content = posts_content[: self.max_posts]

            logger.debug(
                f"Extracted {len(posts_content)} LinkedIn posts using LinkedIn user ID {linkedin_user_id} for account {account_id}"
            )
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
        """Fetch LinkedIn comments via Unipile."""
        if not self.unipile_access_token or not self.unipile_dsn:
            logger.error("Unipile access token or DSN not configured")
            return []

        try:
            headers = {
                "X-API-KEY": self.unipile_access_token,
                "Content-Type": "application/json",
            }

            params = {
                "account_id": account_id,
                "limit": self.max_posts,
            }

            url = f"https://{self.unipile_dsn}/api/v1/users/{linkedin_user_id}/comments"
            comments = self._fetch_paginated_data(
                url,
                headers,
                params,
                f"comments for user {linkedin_user_id} with account {account_id}",
            )

            # filter out the comments made by someone else
            commented_posts = [
                comment.get("post_id")
                for comment in comments
                if (
                    comment.get("author_details", {}).get("id") == linkedin_user_id
                    and comment.get("post_id") is not None
                )
            ]

            logger.debug(
                f"Extracted {len(commented_posts)} LinkedIn comments for user {linkedin_user_id}"
            )
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
        """Fetch LinkedIn reactions via Unipile."""
        if not self.unipile_access_token or not self.unipile_dsn:
            logger.error("Unipile access token or DSN not configured")
            return []

        try:
            headers = {
                "X-API-KEY": self.unipile_access_token,
                "Content-Type": "application/json",
            }

            params = {
                "limit": 100,
                "account_id": account_id,
            }

            url = (
                f"https://{self.unipile_dsn}/api/v1/users/{linkedin_user_id}/reactions"
            )
            reactions = self._fetch_paginated_data(
                url,
                headers,
                params,
                f"reactions for user {linkedin_user_id} with account {account_id}",
            )

            # get the post ids of the reactions
            reacted_posts = [
                reaction.get("post_id")
                for reaction in reactions
                if reaction.get("post_id") is not None
            ]

            logger.debug(
                f"Extracted {len(reacted_posts)} LinkedIn reactions for user {linkedin_user_id}"
            )
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
        """Fetch the text content of posts that the user commented on or reacted to."""
        if not self.unipile_access_token or not self.unipile_dsn:
            logger.error("Unipile access token or DSN not configured")
            return []

        post_texts = []
        post_ids = set()

        post_ids = list(set(comments + reactions))
        # randomly sample 50 posts at most from the list of posts to avoid rate limiting and high costs
        # this should be enough to get a good analysis of the user's content preferences
        post_ids_sample = random.sample(post_ids, min(len(post_ids), 50))

        if not post_ids:
            logger.debug("No post IDs found in comments or reactions")
            return []

        # Fetch post content for each unique post ID
        headers = {
            "X-API-KEY": self.unipile_access_token,
            "Content-Type": "application/json",
        }

        with httpx.Client() as client:
            for post_id in list(post_ids_sample):
                try:
                    params = {
                        "account_id": account_id,
                    }

                    response = client.get(
                        f"https://{self.unipile_dsn}/api/v1/posts/{post_id}",
                        headers=headers,
                        params=params,
                        timeout=30.0,
                    )
                    response.raise_for_status()
                    post_data = response.json()

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
                model="google/gemini-2.5-pro",
                extra_body={
                    "models": ["openai/gpt-4o"],
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
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

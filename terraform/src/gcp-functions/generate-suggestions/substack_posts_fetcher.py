"""
Substack Posts Fetcher Module

This module contains the core logic for fetching latest posts from Substack newsletters.
It handles multiple newsletters in parallel and filters posts by date.
"""

import logging
import concurrent.futures
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from openai import OpenAI
from substack_api import Newsletter
from helper import extract_json_from_llm_response

logger = logging.getLogger(__name__)


class SubstackPostsFetcher:
    """Fetches latest posts from Substack newsletters with date filtering."""

    def __init__(
        self,
        openrouter_api_key: str = None,
        request_delay: float = 0.5,
        max_workers: int = 3,
    ):
        """Initialize the Substack posts fetcher."""
        self.request_delay = (
            request_delay  # Delay between requests to avoid rate limiting
        )
        self.max_workers = max_workers  # Maximum number of concurrent workers
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )

    def get_latest_posts_from_substack(self, substack_url: str) -> List[Dict[str, Any]]:
        """
        Fetch latest posts from a single Substack newsletter.

        Args:
            substack_url: URL of the Substack newsletter

        Returns:
            List of post dictionaries with metadata
        """
        try:
            logger.info(f"Fetching posts from {substack_url}")

            # Add a delay to avoid rate limiting
            time.sleep(self.request_delay)

            # Initialize newsletter
            newsletter = Newsletter(substack_url)

            # Get recent posts (limit to 1 as per user's modification) with retry logic
            recent_posts = self._get_posts_with_retry(newsletter, limit=1)

            # Calculate date threshold (3 days ago)
            three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)

            filtered_posts = []

            for post in recent_posts:
                try:
                    # Get post metadata
                    metadata = post.get_metadata()
                    post_date_str = metadata.get("post_date")

                    if not post_date_str:
                        logger.warning(f"No post_date found for post: {post.url}")
                        continue

                    # Parse post date - handle various formats
                    post_date = self._parse_post_date(post_date_str)
                    if not post_date:
                        continue

                    # Check if post is within last 3 days
                    if post_date >= three_days_ago:
                        post_data = {
                            "url": post.url,
                            "title": metadata.get("title", ""),
                            "subtitle": metadata.get("subtitle", ""),
                            "post_date": post_date.isoformat(),
                            "content": post.get_content(),
                        }
                        filtered_posts.append(post_data)

                except Exception as post_error:
                    logger.warning(
                        f"Error processing post from {substack_url}: {post_error}"
                    )
                    continue

            logger.info(f"Found {len(filtered_posts)} recent posts from {substack_url}")
            return filtered_posts

        except Exception as e:
            logger.error(f"Error fetching posts from {substack_url}: {e}")
            return []

    def fetch_all_substack_posts_parallel(
        self, substack_urls: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch latest posts from multiple Substack newsletters in parallel.

        Args:
            substack_urls: List of Substack URLs

        Returns:
            Combined list of posts from all newsletters
        """
        if not substack_urls:
            logger.info("No Substack URLs provided")
            return []

        logger.info(
            f"Fetching posts from {len(substack_urls)} Substack newsletters in parallel"
        )

        all_posts = []

        # Use ThreadPoolExecutor for parallel requests with reduced workers to avoid rate limiting
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(substack_urls))
        ) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.get_latest_posts_from_substack, url): url
                for url in substack_urls
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    posts = future.result(
                        timeout=30
                    )  # 30 second timeout per newsletter
                    all_posts.extend(posts)
                except Exception as exc:
                    logger.error(f"Error fetching posts from {url}: {exc}")

        # Sort posts by date (newest first)
        all_posts.sort(key=lambda x: x.get("post_date", ""), reverse=True)

        logger.info(f"Total posts fetched: {len(all_posts)}")
        return all_posts

    def _get_posts_with_retry(self, newsletter, limit: int = 1, max_retries: int = 3):
        """
        Get posts with retry logic for rate limiting.

        Args:
            newsletter: Newsletter object
            limit: Number of posts to fetch
            max_retries: Maximum number of retries

        Returns:
            List of posts or empty list if all retries fail
        """
        for attempt in range(max_retries):
            try:
                return newsletter.get_posts(limit=limit)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    # Rate limited, wait longer before retry
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    logger.warning(
                        f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # Either not a rate limit error or final attempt
                    raise e
        return []

    def _parse_post_date(self, post_date_str: str) -> datetime:
        """
        Parse post date string into datetime object.

        Args:
            post_date_str: Date string from post metadata

        Returns:
            Parsed datetime object or None if parsing fails
        """
        try:
            # Try ISO format first
            return datetime.fromisoformat(post_date_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try common formats
                post_date = datetime.strptime(post_date_str, "%Y-%m-%d %H:%M:%S")
                return post_date.replace(tzinfo=timezone.utc)
            except ValueError:
                try:
                    post_date = datetime.strptime(post_date_str, "%Y-%m-%d")
                    return post_date.replace(tzinfo=timezone.utc)
                except ValueError:
                    logger.warning(f"Could not parse date format: {post_date_str}")
                    return None

    def generate_suggestions_for_user(
        self,
        user_id: str,
        substacks: List[str],
        topics_of_interest: List[str],
        bio: str,
    ) -> Dict[str, Any]:
        """
        Complete workflow to generate Substack-based suggestions for a user.

        Args:
            user_id: The user's ID

        Returns:
            Complete response with user preferences and latest posts
        """
        logger.info(f"Generating Substack suggestions for user {user_id}")

        # Get Substack URLs
        substack_urls = substacks

        # Fetch latest posts in parallel
        latest_posts = self.fetch_all_substack_posts_parallel(substack_urls)

        # Filter posts by user preferences
        filtered_posts = self._filter_posts_by_user_preferences(
            latest_posts,
            topics_of_interest,
            bio,
        )

        # Write filtered posts to local JSON file for testing
        with open(
            f"filtered_posts_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "w",
        ) as f:
            json.dump(filtered_posts, f, indent=2, ensure_ascii=False)
        logger.info(f"Filtered posts written to local JSON file for user {user_id}")

        # Prepare complete response
        response_data = {
            "success": True,
            "latest_posts": filtered_posts,
            "total_posts": len(filtered_posts),
        }

        logger.info(f"Successfully generated suggestions for user {user_id}")
        return response_data

    def _filter_posts_by_user_preferences(
        self, posts: List[Dict[str, Any]], user_topics_of_interest: List[str], bio: str
    ) -> List[Dict[str, Any]]:
        """
        Filter posts by user preferences.
        """
        if not user_topics_of_interest:
            return posts

        matched_posts = []
        # use openrouter to filter posts by user topics of interest
        for post in posts:
            prompt = f"""
            You are an expert at selecting posts by user topics of interest and bio for the user to post content on LinkedIn to get engagement.
            You are given a post and a list of user topics of interest and a bio.
            Your task is to select the post by the user topics of interest and bio.
            If the post is a match, determine if the topic is time sensitive or evergreen. If it's time sensitive, then the time_sensitive field should be true.
            Return a json object with the following format:
            {{"match": true/false, "error": "", "time_sensitive": true/false}}
            The post is in the following format:
            {post}
            The user topics of interest are:
            {user_topics_of_interest}
            The bio is:
            {bio}
            """
            response = self.openrouter_client.chat.completions.create(
                model="google/gemini-2.5-pro",
                extra_body={
                    "models": ["openai/gpt-4o"],
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            if extract_json_from_llm_response(response.choices[0].message.content).get(
                "match", False
            ):
                matched_posts.append(post)
        return matched_posts

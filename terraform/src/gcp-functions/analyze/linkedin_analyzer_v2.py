"""
LinkedIn Content Analysis Module V2

This module uses LinkedIn's official Community Management APIs with analytics access tokens
to fetch and analyze LinkedIn content. It replaces web scraping with official API calls.

LinkedIn Community Management APIs used:
- Posts API: Get user's posts and engagement data (/rest/posts)
- Profile API: Get user profile information (/v2/people/{person-id})
- Comments API: Get post comments (/rest/posts/{post-id}/comments)
- Analytics API: Get post and profile analytics (/rest/posts/{post-id}/analytics)

Required LinkedIn Scopes:
- r_member_postAnalytics: For accessing post analytics data
- r_member_profileAnalytics: For accessing profile analytics data

Usage Example:
    analyzer = LinkedInAnalyzerV2(
        analytics_access_token="your_analytics_token",
        max_posts=20,
        openrouter_api_key="your_openrouter_key"
    )

    result = await analyzer.analyze_linkedin(
        person_urn="urn:li:person:123456789",
        current_bio="Current user bio",
        content_to_analyze=["writing_style", "bio", "interests"],
        user_writing_style="Current writing style"
    )
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)


class LinkedInAnalyzerV2:
    """Analyzes LinkedIn content using official LinkedIn Community Management APIs."""

    def __init__(
        self,
        analytics_access_token: str,
        max_posts: int = 20,
        openrouter_api_key: str = None,
    ):
        self.analytics_access_token = analytics_access_token
        self.max_posts = max_posts
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        
        # LinkedIn API base URLs
        self.api_base = "https://api.linkedin.com/v2"
        self.rest_base = "https://api.linkedin.com/rest"
        
        # Get model configuration from environment variables
        import os
        self.model_primary = os.getenv(
            "OPENROUTER_MODEL_PRIMARY", "google/gemini-2.5-flash-preview-05-20"
        )
        models_fallback_str = os.getenv(
            "OPENROUTER_MODELS_FALLBACK", "google/gemini-2.5-flash"
        )
        self.models_fallback = [
            model.strip() for model in models_fallback_str.split(",")
        ]
        self.temperature = float(os.getenv("OPENROUTER_MODEL_TEMPERATURE", "0.0"))

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for LinkedIn API requests."""
        return {
            "Authorization": f"Bearer {self.analytics_access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202405"
        }

    async def analyze_linkedin(
        self,
        person_urn: str,
        current_bio: str,
        content_to_analyze: List[str],
        user_writing_style: str,
    ) -> Dict[str, Any]:
        """
        Main analysis method using LinkedIn Community Management APIs.

        Args:
            person_urn: The LinkedIn person URN (e.g., "urn:li:person:123456")
            current_bio: The current bio of the user
            content_to_analyze: A list of content to analyze, such as bio, writing_style, etc.
            user_writing_style: The current writing style of the user

        Returns:
            Complete analysis results dictionary
        """
        logger.debug(
            f"Starting LinkedIn API analysis for person {person_urn} on {', '.join(content_to_analyze)}"
        )

        try:
            # Fetch user's posts using Community Management API
            user_posts_content, user_posts_data = await self._fetch_user_posts(person_urn)

            topics = []
            websites = []
            if "interests" in content_to_analyze:
                # Analyze topics from user's posts and engagement data
                engagement_data = await self._fetch_post_engagement(user_posts_data)
                topics = await self._analyze_topics(user_posts_content + engagement_data)
                websites = []  # Empty for LinkedIn

            bio = current_bio
            if "bio" in content_to_analyze:
                # Fetch user profile for bio analysis
                user_profile = await self._fetch_user_profile(person_urn)
                bio = await self._create_user_bio(user_posts_content, user_profile, current_bio)

            writing_style = ""
            if "writing_style" in content_to_analyze:
                logger.debug(f"Analyzing writing style from {len(user_posts_content)} posts")
                writing_style = await self._analyze_writing_style(user_posts_content, user_writing_style)

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "topics": topics,
                "websites": websites,
                "bio": bio,
            }

            logger.debug(f"LinkedIn API analysis completed for {person_urn}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing LinkedIn account {person_urn}: {e}")
            raise

    async def _fetch_user_profile(self, person_urn: str) -> Dict[str, Any]:
        """
        Fetch user profile using LinkedIn Profile API.
        
        Uses the /people/{person-id} endpoint to get profile information.
        """
        try:
            # Extract person ID from URN
            person_id = person_urn.split(":")[-1]
            
            url = f"{self.api_base}/people/{person_id}"
            params = {
                "projection": "(id,firstName,lastName,headline,summary,positions,educations,skills)"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                if not response.is_success:
                    self._handle_api_error(response, "profile fetch")
                profile_data = response.json()
                
                return {
                    "headline": profile_data.get("headline", ""),
                    "summary": profile_data.get("summary", ""),
                    "positions": profile_data.get("positions", {}).get("elements", []),
                    "educations": profile_data.get("educations", {}).get("elements", []),
                    "skills": profile_data.get("skills", {}).get("elements", [])
                }
                
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile for {person_urn}: {e}")
            return {}

    async def _fetch_user_posts(self, person_urn: str) -> tuple[List[str], List[Dict]]:
        """
        Fetch user's posts using LinkedIn Community Management API.

        Uses the /posts endpoint with author filter to get user's posts.
        Returns both content strings and full post data.
        """
        try:
            posts_content = []
            posts_data = []

            # Use the Community Management Posts API
            url = f"{self.rest_base}/posts"
            params = {
                "author": person_urn,
                "count": self.max_posts,
                "sortBy": "CREATED_TIME",
                "projection": "(elements*(id,author,commentary,content,createdTime,lastModifiedTime))"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                if not response.is_success:
                    self._handle_api_error(response, "posts fetch")
                response_data = response.json()

                for post in response_data.get("elements", []):
                    posts_data.append(post)

                    # Extract text content using helper method
                    text_content = self._extract_post_text(post)
                    if text_content:
                        posts_content.append(text_content)

                logger.debug(f"Fetched {len(posts_content)} posts for {person_urn}")
                return posts_content, posts_data

        except Exception as e:
            logger.error(f"Error fetching posts for {person_urn}: {e}")
            return [], []

    async def _fetch_post_engagement(self, user_posts_data: List[Dict]) -> List[str]:
        """
        Fetch engagement data for posts to understand user interests.

        Uses the Community Management API to fetch comments and reactions.
        """
        try:
            engagement_content = []

            for post_data in user_posts_data[:10]:  # Limit to first 10 posts for performance
                post_id = post_data.get("id")
                if not post_id:
                    continue

                # Fetch comments for this post
                comments = await self._fetch_post_comments(post_id)
                engagement_content.extend(comments)

                # Note: Reactions API might not provide text content,
                # but we could analyze reaction types for sentiment

            logger.debug(f"Fetched engagement data from {len(engagement_content)} interactions")
            return engagement_content

        except Exception as e:
            logger.error(f"Error fetching engagement data: {e}")
            return []

    async def _fetch_post_comments(self, post_id: str) -> List[str]:
        """
        Fetch comments for a specific post using Community Management API.
        """
        try:
            comments_content = []

            url = f"{self.rest_base}/posts/{post_id}/comments"
            params = {
                "count": 20,  # Limit comments per post
                "projection": "(elements*(id,message,author))"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                comments_data = response.json()

                for comment in comments_data.get("elements", []):
                    message = comment.get("message", "")
                    if message:
                        comments_content.append(message)

                return comments_content

        except Exception as e:
            logger.error(f"Error fetching comments for post {post_id}: {e}")
            return []

    async def _fetch_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Fetch analytics data for a specific post using Analytics API.

        This requires r_member_postAnalytics scope.
        """
        try:
            url = f"{self.rest_base}/posts/{post_id}/analytics"
            params = {
                "projection": "(elements*(impressions,clicks,likes,comments,shares,follows))"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                analytics_data = response.json()

                return analytics_data.get("elements", [{}])[0] if analytics_data.get("elements") else {}

        except Exception as e:
            logger.error(f"Error fetching analytics for post {post_id}: {e}")
            return {}

    async def _fetch_profile_analytics(self, person_urn: str) -> Dict[str, Any]:
        """
        Fetch profile analytics using Analytics API.

        This requires r_member_profileAnalytics scope.
        """
        try:
            # Extract person ID from URN
            person_id = person_urn.split(":")[-1]

            url = f"{self.rest_base}/people/{person_id}/analytics"
            params = {
                "timeRange.start": int((datetime.now() - timedelta(days=30)).timestamp() * 1000),
                "timeRange.end": int(datetime.now().timestamp() * 1000),
                "projection": "(elements*(profileViews,searchAppearances,postImpressions))"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                analytics_data = response.json()

                return analytics_data.get("elements", [{}])[0] if analytics_data.get("elements") else {}

        except Exception as e:
            logger.error(f"Error fetching profile analytics for {person_urn}: {e}")
            return {}

    async def _analyze_topics(self, posts: List[str]) -> List[str]:
        """Analyze topics from LinkedIn posts by processing in batches."""
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
                batch_topics = await self._analyze_topics_batch(batch)
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

    async def _analyze_topics_batch(self, posts: List[str]) -> List[str]:
        """Analyze topics from a batch of LinkedIn posts."""
        # Combine posts in the batch
        combined_posts = "\n\n---\n\n".join(posts)

        prompt = f"""
        You are an expert at analyzing topics and themes that the user might be interested in from LinkedIn posts.
        You are given text content from LinkedIn posts that a user has written.
        Your task is to identify the main topics and themes that this user is interested in based on their content.
        Return a list of topics, one per line, focusing on professional interests, industry themes, and subject matters.
        Each topic should be 1-3 words maximum. DO NOT include any special characters or punctuation.

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

    async def _analyze_writing_style(self, posts: List[str], user_writing_style: str) -> str:
        """Analyze writing style of LinkedIn posts."""
        if not posts:
            logger.debug("No posts provided for writing style analysis")
            return ""

        # Combine posts with reasonable length limit
        combined_posts = "\n\n---\n\n".join(posts)

        if user_writing_style:
            user_writing_style_prompt = f"User's Current Writing Style (if available):\n{user_writing_style}\n\n"
        else:
            user_writing_style_prompt = ""

        prompt = f"""
        You are an expert at analyzing writing style of LinkedIn posts of an author.
        You are given the text content of several LinkedIn posts.
        Your task is to analyze the writing style, tone, voice, and characteristics of this writing using gender neutral descriptions.
        Consider elements like based on different topics and themes:
        - Tone (formal, casual, conversational, etc.)
        - Voice (authoritative, friendly, analytical, etc.)
        - Sentence structure and length
        - Use of humor, metaphors, or storytelling
        - Technical vs. accessible language
        - Persuasive techniques
        - Overall personality that comes through in the writing

        Return the writing style analysis in plain text format without any markdown. Each observation should be on a new line.
        Be specific and provide actionable insights that could help someone write in a similar style.
        If the user's current writing style is provided, incorporate it into the analysis.

        LinkedIn Posts:
        {combined_posts}

        {user_writing_style_prompt}
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

    async def _create_user_bio(
        self,
        posts: List[str],
        linkedin_profile: Dict[str, Any],
        current_bio: str,
    ) -> str:
        """Create a user bio from LinkedIn posts and profile information."""
        if not posts and not linkedin_profile:
            logger.debug("No posts or LinkedIn profile provided for user bio creation")
            return current_bio

        combined_posts = "\n\n---\n\n".join(posts) if posts else ""
        profile_text = ""

        # Format profile information
        if linkedin_profile:
            if linkedin_profile.get("headline"):
                profile_text += f"Headline: {linkedin_profile['headline']}\n"
            if linkedin_profile.get("summary"):
                profile_text += f"Summary: {linkedin_profile['summary']}\n"

            for position in linkedin_profile.get("positions", []):
                title = position.get("title", "")
                company = position.get("companyName", "")
                if title and company:
                    profile_text += f"Position: {title} at {company}\n"
                if position.get("description"):
                    profile_text += f"Description: {position['description']}\n"

        prompt = f"""
        You are an expert at creating a user bio from LinkedIn posts, their LinkedIn profile, and a current bio.
        You are given LinkedIn post content and profile information.
        Your task is to create a user bio from the posts and the current bio, please use the first person perspective and gender neutral descriptions.
        If the LinkedIn profile and/or the current bio are given, update them based on your analysis.
        The user bio should be a short description of the user's interests, what they do, the roles they hold, what they're passionate about.
        If the information is available, also include the user's passions and interests in their personal life.
        If the information is available, also include the user's perspective and opinions on various topics they write about.
        This will be used as a persona for LLM to generate content in their style, preferences, and point of view.

        Return the user bio in plain text format without any markdown. The LinkedIn profile and current bio might be empty or incomplete.

        LinkedIn Posts:
        {combined_posts}

        LinkedIn Profile:
        {profile_text}

        Current Bio:
        {current_bio}
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

    def _extract_post_text(self, post: Dict[str, Any]) -> str:
        """
        Extract text content from a LinkedIn post object.

        Handles different content types: text posts, articles, images with captions, etc.
        """
        text_parts = []

        # Extract commentary (main post text)
        commentary = post.get("commentary", "")
        if commentary:
            text_parts.append(commentary)

        # Extract content based on type
        content = post.get("content", {})

        # Article content
        if content.get("article"):
            article = content["article"]
            if article.get("title"):
                text_parts.append(f"Article: {article['title']}")
            if article.get("description"):
                text_parts.append(article["description"])

        # Media content with descriptions
        if content.get("media"):
            media = content["media"]
            if media.get("title"):
                text_parts.append(f"Media: {media['title']}")
            if media.get("description"):
                text_parts.append(media["description"])

        # Poll content
        if content.get("poll"):
            poll = content["poll"]
            if poll.get("question"):
                text_parts.append(f"Poll: {poll['question']}")
            for option in poll.get("options", []):
                if option.get("text"):
                    text_parts.append(f"Option: {option['text']}")

        return " ".join(text_parts).strip()

    def _handle_api_error(self, response: httpx.Response, context: str) -> None:
        """
        Handle LinkedIn API errors with specific error messages.
        """
        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown API error")
            error_code = error_data.get("status", response.status_code)

            if response.status_code == 401:
                raise Exception(f"Authentication failed for {context}: {error_message}. Check analytics access token.")
            elif response.status_code == 403:
                raise Exception(f"Access forbidden for {context}: {error_message}. Check required scopes (r_member_postAnalytics, r_member_profileAnalytics).")
            elif response.status_code == 429:
                raise Exception(f"Rate limit exceeded for {context}: {error_message}")
            else:
                raise Exception(f"API error for {context} (HTTP {error_code}): {error_message}")

        except ValueError:
            # Response is not JSON
            raise Exception(f"API error for {context} (HTTP {response.status_code}): {response.text}")

    def _create_empty_analysis(self, person_urn: str) -> Dict[str, Any]:
        """Create empty analysis result when no posts are found."""
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
            "bio": "",
        }

    @staticmethod
    def profile_url_to_person_urn(profile_url: str) -> Optional[str]:
        """
        Convert LinkedIn profile URL to person URN.

        Note: This is a simplified conversion. In practice, you would need to use
        LinkedIn's People Search API or have the person URN stored in your database.

        Args:
            profile_url: LinkedIn profile URL (e.g., "https://linkedin.com/in/username")

        Returns:
            Person URN if conversion is possible, None otherwise
        """
        # This is a placeholder implementation
        # In reality, you would need to:
        # 1. Use LinkedIn's People Search API to find the person by profile URL
        # 2. Store the person URN when the user connects their LinkedIn account
        # 3. Use the vanity name to search for the person

        logger.warning("profile_url_to_person_urn is a placeholder. Use stored person URN from database.")
        return None

    @staticmethod
    def get_person_urn_from_vanity_name(vanity_name: str) -> str:
        """
        Create a person URN format from vanity name.

        Note: This creates a URN format but doesn't guarantee it's valid.
        The actual person ID should be obtained during the OAuth flow.

        Args:
            vanity_name: LinkedIn vanity name (username)

        Returns:
            Formatted person URN
        """
        # This is a placeholder - in practice, you need the actual person ID
        # which is obtained during OAuth or through People Search API
        return f"urn:li:person:{vanity_name}"

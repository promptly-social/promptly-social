"""
OpenAI provider implementation for AI analysis services.

This module implements the OpenAI-specific provider for content analysis,
including writing style analysis, topic extraction, bio updates, and
negative pattern analysis.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
import aiohttp
import time

from .ai_service_interface import (
    AIProviderInterface,
    AnalysisType,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceQuotaError,
    AIServiceTimeoutError,
)
from .config import ProviderConfig, AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProviderInterface):
    """OpenAI implementation of the AI analysis provider interface."""

    def __init__(self, config: ProviderConfig):
        """
        Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config.additional_config)

        if config.provider_type != AIProvider.OPENAI:
            raise ValueError(
                f"Invalid provider type for OpenAI: {config.provider_type}"
            )

        self.api_key = config.api_key
        self.model = config.model or "gpt-3.5-turbo"
        self.max_tokens = config.max_tokens or 2000
        self.temperature = config.temperature or 0.7
        self.timeout = config.timeout or 30
        self.rate_limit_rpm = config.rate_limit_requests_per_minute

        # OpenAI specific configuration
        self.organization = config.additional_config.get("organization")
        self.base_url = config.additional_config.get(
            "base_url", "https://api.openai.com/v1"
        )

        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        self._request_times = []

    async def _make_request(
        self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None
    ) -> str:
        """
        Make a request to OpenAI API.

        Args:
            messages: List of messages for the chat completion
            max_tokens: Maximum tokens for response

        Returns:
            Response content from OpenAI

        Raises:
            AIServiceError: For various API errors
        """
        await self._enforce_rate_limit()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self.organization:
            headers["OpenAI-Organization"] = self.organization

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature,
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"].strip()

                    elif response.status == 429:
                        # Rate limit or quota exceeded
                        retry_after = response.headers.get("Retry-After")
                        retry_after_int = int(retry_after) if retry_after else None

                        error_data = await response.json()
                        error_message = error_data.get("error", {}).get(
                            "message", "Rate limit exceeded"
                        )

                        if "quota" in error_message.lower():
                            raise AIServiceQuotaError(
                                f"OpenAI quota exceeded: {error_message}"
                            )
                        else:
                            raise AIServiceRateLimitError(
                                f"OpenAI rate limit: {error_message}", retry_after_int
                            )

                    elif response.status in [400, 401, 403]:
                        error_data = await response.json()
                        error_message = error_data.get("error", {}).get(
                            "message", "API error"
                        )
                        raise AIServiceError(
                            f"OpenAI API error ({response.status}): {error_message}"
                        )

                    else:
                        raise AIServiceError(
                            f"OpenAI API error: HTTP {response.status}"
                        )

        except asyncio.TimeoutError:
            raise AIServiceTimeoutError(
                f"OpenAI request timed out after {self.timeout} seconds"
            )
        except aiohttp.ClientError as e:
            raise AIServiceError(f"OpenAI request failed: {e}")

    async def _enforce_rate_limit(self):
        """Enforce rate limiting if configured."""
        if not self.rate_limit_rpm:
            return

        current_time = time.time()

        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if current_time - t < 60]

        # Check if we're at the rate limit
        if len(self._request_times) >= self.rate_limit_rpm:
            # Wait until the oldest request is more than 1 minute old
            sleep_time = 60 - (current_time - self._request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)

        # Record this request
        self._request_times.append(current_time)

    async def analyze_writing_style(
        self, content_list: List[str], existing_analysis: Optional[str] = None
    ) -> str:
        """
        Analyze writing style from content using OpenAI.

        Args:
            content_list: List of content to analyze
            existing_analysis: Previous analysis to build upon

        Returns:
            Updated writing style analysis
        """
        if not content_list:
            return existing_analysis or "No content available for analysis."

        # Combine content for analysis
        combined_content = "\n\n---\n\n".join(content_list)

        # Create prompt for writing style analysis
        system_prompt = """You are an expert writing analyst. Analyze the provided content to identify writing style patterns, including:

1. Tone and voice characteristics
2. Sentence structure and complexity
3. Vocabulary choices and register
4. Rhetorical devices and techniques
5. Formatting and presentation preferences
6. Audience engagement strategies

Provide a comprehensive analysis that can be used to generate similar content. Focus on actionable insights about the writing style."""

        user_prompt = f"""Analyze the writing style of the following content:

{combined_content}"""

        if existing_analysis:
            user_prompt += f"""

Previous analysis to build upon:
{existing_analysis}

Please update and refine the analysis based on the new content while preserving valuable insights from the previous analysis."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return await self._make_request(messages)

    async def analyze_topics_of_interest(
        self, content_list: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract topics of interest from content using OpenAI.

        Args:
            content_list: List of content to analyze

        Returns:
            List of topics with confidence scores and metadata
        """
        if not content_list:
            return []

        combined_content = "\n\n---\n\n".join(content_list)

        system_prompt = """You are an expert content analyst. Extract and analyze topics of interest from the provided content. 

Return your analysis as a JSON array where each topic has:
- "topic": The main topic or theme
- "confidence": A confidence score from 0.0 to 1.0
- "frequency": How often this topic appears
- "keywords": Related keywords and phrases
- "category": General category (e.g., "technology", "business", "personal development")
- "description": Brief description of why this topic is significant

Focus on identifying recurring themes, professional interests, and areas of expertise."""

        user_prompt = f"""Analyze the following content and extract topics of interest:

{combined_content}

Return the results as a valid JSON array."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self._make_request(messages)

        try:
            # Try to parse JSON response
            topics = json.loads(response)
            if isinstance(topics, list):
                return topics
            else:
                logger.warning("OpenAI returned non-list response for topics analysis")
                return []
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse JSON from OpenAI topics response: {response}"
            )
            # Fallback: try to extract topics from text response
            return self._extract_topics_from_text(response)

    def _extract_topics_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Fallback method to extract topics from text response.

        Args:
            text: Text response from AI

        Returns:
            List of extracted topics
        """
        topics = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    topic_name = parts[0].strip()
                    description = parts[1].strip()

                    topics.append(
                        {
                            "topic": topic_name,
                            "confidence": 0.7,  # Default confidence
                            "frequency": 1,
                            "keywords": [topic_name.lower()],
                            "category": "general",
                            "description": description,
                        }
                    )

        return topics[:10]  # Limit to top 10 topics

    async def update_user_bio(self, current_bio: str, recent_content: List[str]) -> str:
        """
        Update user bio based on recent content using OpenAI.

        Args:
            current_bio: Current user bio
            recent_content: Recent content to incorporate

        Returns:
            Updated bio text
        """
        if not recent_content:
            return current_bio

        combined_content = "\n\n---\n\n".join(recent_content)

        system_prompt = """You are an expert professional bio writer. Update the provided bio based on recent content while:

1. Maintaining the core professional identity and achievements
2. Incorporating new insights, perspectives, or focus areas from recent content
3. Keeping the tone and style consistent with the original bio
4. Ensuring the bio remains professional and concise
5. Highlighting evolving expertise or interests

The updated bio should feel natural and authentic, not forced or overly promotional."""

        user_prompt = f"""Current bio:
{current_bio}

Recent content that may inform bio updates:
{combined_content}

Please update the bio to reflect any new perspectives, expertise, or focus areas evident in the recent content, while maintaining the core professional identity."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return await self._make_request(messages)

    async def analyze_negative_patterns(
        self,
        dismissed_posts: List[Dict[str, Any]],
        feedback_posts: List[Dict[str, Any]],
    ) -> str:
        """
        Analyze negative patterns from dismissed content using OpenAI.

        Args:
            dismissed_posts: Posts that were dismissed
            feedback_posts: Posts with negative feedback

        Returns:
            Analysis of patterns to avoid
        """
        if not dismissed_posts and not feedback_posts:
            return "No negative feedback data available for analysis."

        # Prepare content for analysis
        analysis_content = []

        if dismissed_posts:
            analysis_content.append("DISMISSED POSTS:")
            for i, post in enumerate(dismissed_posts, 1):
                content = post.get("content", "")
                analysis_content.append(f"{i}. {content}")

        if feedback_posts:
            analysis_content.append("\nPOSTS WITH NEGATIVE FEEDBACK:")
            for i, post in enumerate(feedback_posts, 1):
                content = post.get("content", "")
                feedback = post.get("feedback", "")
                analysis_content.append(f"{i}. Content: {content}")
                if feedback:
                    analysis_content.append(f"   Feedback: {feedback}")

        combined_content = "\n".join(analysis_content)

        system_prompt = """You are an expert content analyst specializing in identifying patterns in rejected or negatively received content.

Analyze the provided dismissed posts and negative feedback to identify:

1. Common themes or topics that were rejected
2. Writing styles or tones that didn't resonate
3. Content formats or structures that were dismissed
4. Timing or context issues
5. Audience mismatch indicators
6. Any other patterns that suggest content preferences to avoid

Provide actionable insights that can be used to avoid similar content in the future. Focus on specific, measurable patterns rather than vague generalizations."""

        user_prompt = f"""Analyze the following dismissed and negatively received content to identify patterns to avoid:

{combined_content}

What patterns should be avoided in future content generation?"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return await self._make_request(messages)

    async def make_analysis_request(
        self, prompt: str, content: str, analysis_type: AnalysisType
    ) -> str:
        """
        Make a raw analysis request to OpenAI.

        Args:
            prompt: Analysis prompt
            content: Content to analyze
            analysis_type: Type of analysis being performed

        Returns:
            Raw response from OpenAI
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content},
        ]

        # Adjust max_tokens based on analysis type
        max_tokens = self.max_tokens
        if analysis_type == AnalysisType.TOPICS_OF_INTEREST:
            max_tokens = min(max_tokens, 1500)  # Topics usually need less space
        elif analysis_type == AnalysisType.BIO_UPDATE:
            max_tokens = min(max_tokens, 800)  # Bios should be concise

        return await self._make_request(messages, max_tokens)

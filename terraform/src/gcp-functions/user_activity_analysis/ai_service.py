"""
Pydantic-based AI service for user activity analysis using OpenRouter.

This module provides a simplified AI service implementation using Pydantic AI
and OpenRouter, similar to the chat service pattern used in the main application.
"""

import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)


class AnalysisResult(BaseModel):
    """Base model for analysis results."""

    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class TopicResult(BaseModel):
    """Model for topic analysis results."""

    topic: str
    confidence: float
    keywords: List[str]


class TopicsAnalysisResult(BaseModel):
    """Model for topics of interest analysis."""

    success: bool
    topics: List[TopicResult] = []
    error: Optional[str] = None


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class AIService:
    """
    Simplified AI service using Pydantic AI and OpenRouter.

    This service provides the same interface as the original AI service
    but uses a simpler implementation based on Pydantic AI.
    """

    def __init__(self):
        """Initialize the AI service with OpenRouter configuration."""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_api_key:
            raise AIServiceError("OPENROUTER_API_KEY environment variable is required")

        self.model_primary = os.getenv(
            "OPENROUTER_MODEL_PRIMARY", "google/gemini-2.5-flash"
        )
        models_fallback_str = os.getenv(
            "OPENROUTER_MODELS_FALLBACK", "deepseek/deepseek-r1-0528"
        )
        self.models_fallback = [
            model.strip() for model in models_fallback_str.split(",")
        ]
        self.model_temperature = float(os.getenv("OPENROUTER_MODEL_TEMPERATURE", "0.0"))

        self.model = OpenAIModel(
            self.model_primary,
            provider=OpenRouterProvider(
                api_key=self.openrouter_api_key,
            ),
        )
        self.model_settings = OpenAIModelSettings(
            temperature=self.model_temperature,
            extra_body={"models": self.models_fallback},
        )

    def _create_agent(self, system_prompt: str, output_type: type = str) -> Agent:
        """Create a Pydantic AI agent with proper configuration."""
        return Agent(
            self.model,
            result_type=output_type,
            system_prompt=system_prompt,
            model_settings=OpenAIModelSettings(
                temperature=self.model_temperature,
                extra_body={"models": self.models_fallback},
            ),
            retries=1,  # Built-in retry mechanism
        )

    async def analyze_writing_style(
        self, content_list: List[str], existing_analysis: Optional[str] = None
    ) -> str:
        """
        Analyze writing style from content.

        Args:
            content_list: List of content to analyze
            existing_analysis: Previous analysis to build upon

        Returns:
            Updated writing style analysis as text
        """
        if not content_list:
            return existing_analysis or "No content available for analysis."

        content_text = "\n\n---\n\n".join(content_list)

        system_prompt = f"""You are an expert writing style analyst. Analyze the provided content to identify the author's unique writing characteristics, tone, and patterns.

TASK: Analyze the writing style from the provided content and {'update the existing analysis' if existing_analysis else 'create a comprehensive analysis'}.

{'EXISTING ANALYSIS TO UPDATE:' + existing_analysis if existing_analysis else ''}

CONTENT TO ANALYZE:
{content_text}

Provide a detailed analysis covering:
1. Tone and voice characteristics
2. Sentence structure and length patterns
3. Vocabulary choices and complexity
4. Use of rhetorical devices
5. Emotional expression patterns
6. Professional vs. personal communication style
7. Engagement techniques used

Return only the analysis text in plan text format, no additional formatting or explanations.

VERY IMPORTANT:
- No Markdown
"""

        try:
            agent = self._create_agent(system_prompt)
            result = await agent.run(content_text)
            return result.output
        except Exception as e:
            logger.error(f"Error analyzing writing style: {e}")
            raise AIServiceError(f"Writing style analysis failed: {str(e)}")

    async def analyze_topics_of_interest(
        self, content_list: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract topics of interest from content.

        Args:
            content_list: List of content to analyze

        Returns:
            List of topics with confidence scores and metadata
        """
        if not content_list:
            return []

        content_text = "\n\n---\n\n".join(content_list)

        system_prompt = f"""You are an expert content analyst specializing in topic extraction and categorization.

TASK: Analyze the provided content to identify the main topics of interest, themes, and subject areas that the author engages with.

Each topic should be 1-3 words maximum. DO NOT include any special characters or punctuation.

CONTENT TO ANALYZE:
{content_text}

Extract and analyze topics, providing:
1. Main topic/theme name
2. Confidence level (0.0 to 1.0)
3. Relevant keywords associated with the topic
4. Brief context about how this topic appears in the content

Return the results as a JSON array with this exact structure:
[
  {{
    "topic": "Topic Name",
    "confidence": 0.85,
    "keywords": ["keyword1", "keyword2", "keyword3"],
  }}
]

Focus on the most significant and recurring topics. Limit to maximum 10 topics, ordered by relevance/confidence."""

        try:
            agent = self._create_agent(system_prompt, output_type=TopicsAnalysisResult)
            result = await agent.run(content_text)
            return result.output.topics

        except Exception as e:
            logger.error(f"Error analyzing topics of interest: {e}")
            raise AIServiceError(f"Topics analysis failed: {str(e)}")

    async def update_user_bio(self, current_bio: str, recent_content: List[str]) -> str:
        """
        Update user bio based on recent content.

        Args:
            current_bio: Current user bio
            recent_content: Recent content to incorporate

        Returns:
            Updated bio text
        """
        if not recent_content:
            return current_bio

        content_text = "\n\n---\n\n".join(recent_content)

        system_prompt = f"""You are an expert personal branding consultant specializing in professional bio optimization.

TASK: Update the user's bio based on their recent content activity to better reflect their current interests, expertise, and professional focus.

Your task is to update a user bio from the given information and the current bio, please use the first person perspective and gender neutral descriptions.
If the LinkedIn profile and/or the current bio are given, update them based on your analysis.
The user bio should be a short description of the user's interests, what they do, the roles they hold, what they're passionate about.
If the information is available, also include the user's passions and interests in their personal life.
If the information is available, also include the user's perspective and opinions on various topics they write about.
This will be used as a persona for LLM to generate content in their style, preferences, and point of view.

Return only the updated bio text in plain text format, no additional formatting or explanations.

VERY IMPORTANT:
- No Markdown

CURRENT BIO:
{current_bio}

RECENT CONTENT TO INCORPORATE:
{content_text}
"""

        try:
            agent = self._create_agent(system_prompt)
            result = await agent.run(
                f"Current bio: {current_bio}\n\nRecent content: {content_text}"
            )
            return result.output.strip()
        except Exception as e:
            logger.error(f"Error updating user bio: {e}")
            raise AIServiceError(f"Bio update failed: {str(e)}")

    async def analyze_negative_patterns(
        self,
        dismissed_posts: List[Dict[str, Any]],
        feedback_posts: List[Dict[str, Any]],
        scheduled_posts: List[str],
        current_analysis: str,
    ) -> str:
        """
        Analyze negative patterns from dismissed content.

        Args:
            dismissed_posts: Posts that were dismissed
            feedback_posts: Posts with negative feedback

        Returns:
            Analysis of patterns to avoid
        """
        if not dismissed_posts and not feedback_posts:
            return "No negative feedback data available for analysis."

        # Format dismissed posts
        dismissed_content = []
        for post in dismissed_posts:
            content = post.get("content", "")
            if content:
                dismissed_content.append(f"DISMISSED: {content}")

        # Format feedback posts
        feedback_content = []
        for post in feedback_posts:
            content = post.get("content", "")
            feedback = post.get("feedback", "")
            if content:
                feedback_content.append(f"CONTENT: {content}\nFEEDBACK: {feedback}")

        all_content = dismissed_content + feedback_content
        if not all_content:
            return "No content available for negative pattern analysis."

        approved_content = []
        for post in scheduled_posts:
            if post:
                approved_content.append(f"APPROVED CONTENT: {post}\n")

        content_text = "\n\n---\n\n".join(all_content)
        approved_content_text = "\n\n---\n\n".join(approved_content)

        system_prompt = f"""You are an expert content strategist specializing in analyzing content performance and user preferences.

TASK: Analyze the dismissed posts, negative feedback, and approved content to identify patterns that should be avoided in future content creation.

Analyze and identify:
1. Common themes or topics that received negative responses
2. Writing styles or tones that were poorly received
3. Content formats or structures that were dismissed
4. Timing or context patterns that led to negative feedback
5. Use what the user approved as contrast to identify what works well

Provide actionable insights for content improvement, focusing on:
- What to avoid topics or themse in future content
- Content formats or structures that the user dislike
- Perspectives, angles, or points of view that the user dislike
- Perspectives, angles, or points of view that the user like 

Return a comprehensive analysis that can guide future content creation decisions.
Return the analysis in plan text format.

VERY IMPORTANT:
- No Markdown

Previous analysis to update: 
{current_analysis}

CONTENT AND FEEDBACK DATA:
{content_text}

APPROVED CONTENT DATA:
{approved_content_text}

"""

        try:
            agent = self._create_agent(system_prompt)
            result = await agent.run(content_text)
            return result.output
        except Exception as e:
            logger.error(f"Error analyzing negative patterns: {e}")
            raise AIServiceError(f"Negative pattern analysis failed: {str(e)}")

    async def health_check(self) -> bool:
        """
        Check if the AI service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            agent = self._create_agent(
                "Respond with 'OK' if you can process this request."
            )
            result = await agent.run("Health check test")
            return "OK" in result.output.upper()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


# Global service instance
_ai_service_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    Get or create the global AI service instance.

    Returns:
        AIService instance
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance


def create_ai_service() -> AIService:
    """
    Create a new AI service instance.

    Returns:
        New AIService instance
    """
    return AIService()

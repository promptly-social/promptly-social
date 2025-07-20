"""
Anthropic provider implementation for AI analysis services.

This module implements the Anthropic Claude-specific provider for content analysis,
ensuring feature parity with the OpenAI implementation while leveraging
Claude's specific capabilities and API patterns.
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
    AIServiceTimeoutError
)
from .config import ProviderConfig, AIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProviderInterface):
    """Anthropic Claude implementation of the AI analysis provider interface."""
    
    def __init__(self, config: ProviderConfig):
        """
        Initialize Anthropic provider.
        
        Args:
            config: Provider configuration
        """
        super().__init__(config.additional_config)
        
        if config.provider_type != AIProvider.ANTHROPIC:
            raise ValueError(f"Invalid provider type for Anthropic: {config.provider_type}")
        
        self.api_key = config.api_key
        self.model = config.model or "claude-3-sonnet-20240229"
        self.max_tokens = config.max_tokens or 2000
        self.temperature = config.temperature or 0.7
        self.timeout = config.timeout or 30
        self.rate_limit_rpm = config.rate_limit_requests_per_minute
        
        # Anthropic specific configuration
        self.base_url = config.additional_config.get('base_url', 'https://api.anthropic.com/v1')
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        self._request_times = []
    
    async def _make_request(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> str:
        """
        Make a request to Anthropic API.
        
        Args:
            messages: List of messages for the completion
            max_tokens: Maximum tokens for response
            
        Returns:
            Response content from Anthropic
            
        Raises:
            AIServiceError: For various API errors
        """
        await self._enforce_rate_limit()
        
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        # Convert messages to Anthropic format
        system_message = ""
        user_messages = []
        
        for message in messages:
            if message['role'] == 'system':
                system_message = message['content']
            else:
                user_messages.append(message)
        
        payload = {
            'model': self.model,
            'max_tokens': max_tokens or self.max_tokens,
            'temperature': self.temperature,
            'messages': user_messages
        }
        
        if system_message:
            payload['system'] = system_message
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f'{self.base_url}/messages',
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        # Anthropic returns content in a different format
                        content = data.get('content', [])
                        if content and isinstance(content, list) and len(content) > 0:
                            return content[0].get('text', '').strip()
                        else:
                            return ''
                    
                    elif response.status == 429:
                        # Rate limit or quota exceeded
                        retry_after = response.headers.get('retry-after')
                        retry_after_int = int(retry_after) if retry_after else None
                        
                        try:
                            error_data = await response.json()
                            error_message = error_data.get('error', {}).get('message', 'Rate limit exceeded')
                        except:
                            error_message = 'Rate limit exceeded'
                        
                        if 'quota' in error_message.lower() or 'credit' in error_message.lower():
                            raise AIServiceQuotaError(f"Anthropic quota exceeded: {error_message}")
                        else:
                            raise AIServiceRateLimitError(f"Anthropic rate limit: {error_message}", retry_after_int)
                    
                    elif response.status in [400, 401, 403]:
                        try:
                            error_data = await response.json()
                            error_message = error_data.get('error', {}).get('message', 'API error')
                        except:
                            error_message = f'HTTP {response.status} error'
                        raise AIServiceError(f"Anthropic API error ({response.status}): {error_message}")
                    
                    else:
                        raise AIServiceError(f"Anthropic API error: HTTP {response.status}")
        
        except asyncio.TimeoutError:
            raise AIServiceTimeoutError(f"Anthropic request timed out after {self.timeout} seconds")
        except aiohttp.ClientError as e:
            raise AIServiceError(f"Anthropic request failed: {e}")
    
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
        self, 
        content_list: List[str], 
        existing_analysis: Optional[str] = None
    ) -> str:
        """
        Analyze writing style from content using Anthropic Claude.
        
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
        
        # Create prompt optimized for Claude
        system_prompt = """You are an expert writing analyst with deep expertise in identifying and articulating writing style patterns. Your task is to analyze content and provide comprehensive insights about writing characteristics.

Focus on these key areas:
1. Voice and tone characteristics (formal/informal, authoritative/conversational, etc.)
2. Sentence structure patterns (length, complexity, rhythm)
3. Vocabulary choices and linguistic register
4. Rhetorical techniques and persuasive elements
5. Content organization and flow patterns
6. Audience engagement strategies and techniques

Provide actionable insights that would help generate content with similar stylistic characteristics. Be specific and detailed in your analysis."""
        
        user_prompt = f"""Please analyze the writing style of the following content:

<content>
{combined_content}
</content>"""
        
        if existing_analysis:
            user_prompt += f"""

<previous_analysis>
{existing_analysis}
</previous_analysis>

Please update and refine the analysis based on the new content while preserving valuable insights from the previous analysis. Focus on how the new content confirms, modifies, or extends the previous understanding of the writing style."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages)
    
    async def analyze_topics_of_interest(
        self, 
        content_list: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract topics of interest from content using Anthropic Claude.
        
        Args:
            content_list: List of content to analyze
            
        Returns:
            List of topics with confidence scores and metadata
        """
        if not content_list:
            return []
        
        combined_content = "\n\n---\n\n".join(content_list)
        
        system_prompt = """You are an expert content analyst specializing in topic extraction and thematic analysis. Your task is to identify and analyze topics of interest from the provided content.

Return your analysis as a valid JSON array where each topic object contains:
- "topic": The main topic or theme (string)
- "confidence": Confidence score from 0.0 to 1.0 (number)
- "frequency": How often this topic appears (integer)
- "keywords": Array of related keywords and phrases (array of strings)
- "category": General category like "technology", "business", "personal development" (string)
- "description": Brief explanation of why this topic is significant (string)

Focus on identifying:
- Recurring themes and subjects
- Professional interests and expertise areas
- Industry-specific topics
- Personal interests and perspectives
- Emerging patterns in content focus

Ensure the JSON is properly formatted and valid."""
        
        user_prompt = f"""Analyze the following content and extract topics of interest:

<content>
{combined_content}
</content>

Return the results as a valid JSON array following the specified format."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self._make_request(messages)
        
        try:
            # Try to parse JSON response
            topics = json.loads(response)
            if isinstance(topics, list):
                return topics
            else:
                logger.warning("Anthropic returned non-list response for topics analysis")
                return []
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from Anthropic topics response: {response}")
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
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    topic_name = parts[0].strip()
                    description = parts[1].strip()
                    
                    topics.append({
                        'topic': topic_name,
                        'confidence': 0.7,  # Default confidence
                        'frequency': 1,
                        'keywords': [topic_name.lower()],
                        'category': 'general',
                        'description': description
                    })
        
        return topics[:10]  # Limit to top 10 topics
    
    async def update_user_bio(
        self, 
        current_bio: str, 
        recent_content: List[str]
    ) -> str:
        """
        Update user bio based on recent content using Anthropic Claude.
        
        Args:
            current_bio: Current user bio
            recent_content: Recent content to incorporate
            
        Returns:
            Updated bio text
        """
        if not recent_content:
            return current_bio
        
        combined_content = "\n\n---\n\n".join(recent_content)
        
        system_prompt = """You are an expert professional bio writer with extensive experience in personal branding and professional communication. Your task is to update a professional bio based on recent content while maintaining authenticity and professional standards.

Guidelines for bio updates:
1. Preserve the core professional identity and key achievements
2. Incorporate new insights, perspectives, or evolving focus areas from recent content
3. Maintain consistency with the original tone and professional level
4. Ensure the bio remains concise and impactful
5. Highlight emerging expertise or shifting interests naturally
6. Avoid forced or overly promotional language
7. Keep the bio authentic and genuine to the person's voice

The updated bio should feel like a natural evolution, not a complete rewrite."""
        
        user_prompt = f"""<current_bio>
{current_bio}
</current_bio>

<recent_content>
{combined_content}
</recent_content>

Please update the bio to reflect any new perspectives, expertise, or focus areas evident in the recent content, while maintaining the core professional identity and authentic voice."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages)
    
    async def analyze_negative_patterns(
        self, 
        dismissed_posts: List[Dict[str, Any]], 
        feedback_posts: List[Dict[str, Any]]
    ) -> str:
        """
        Analyze negative patterns from dismissed content using Anthropic Claude.
        
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
            analysis_content.append("<dismissed_posts>")
            for i, post in enumerate(dismissed_posts, 1):
                content = post.get('content', '')
                analysis_content.append(f"{i}. {content}")
            analysis_content.append("</dismissed_posts>")
        
        if feedback_posts:
            analysis_content.append("<posts_with_negative_feedback>")
            for i, post in enumerate(feedback_posts, 1):
                content = post.get('content', '')
                feedback = post.get('feedback', '')
                analysis_content.append(f"{i}. Content: {content}")
                if feedback:
                    analysis_content.append(f"   Feedback: {feedback}")
            analysis_content.append("</posts_with_negative_feedback>")
        
        combined_content = "\n".join(analysis_content)
        
        system_prompt = """You are an expert content analyst specializing in identifying patterns in rejected or negatively received content. Your expertise lies in understanding why certain content doesn't resonate with audiences and extracting actionable insights.

Analyze the provided data to identify specific patterns including:

1. Thematic patterns - topics or subjects that consistently get rejected
2. Stylistic patterns - writing styles, tones, or approaches that don't work
3. Structural patterns - content formats or organization that fail to engage
4. Timing or contextual issues - when content might be inappropriate
5. Audience mismatch indicators - signs that content doesn't fit the intended audience
6. Messaging problems - communication issues or unclear value propositions

Provide specific, actionable insights that can be used to avoid similar content in the future. Focus on concrete patterns rather than vague generalizations. Be thorough but concise."""
        
        user_prompt = f"""Analyze the following dismissed and negatively received content to identify patterns that should be avoided in future content generation:

{combined_content}

What specific patterns, themes, styles, or approaches should be avoided based on this data?"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._make_request(messages)
    
    async def make_analysis_request(
        self, 
        prompt: str, 
        content: str, 
        analysis_type: AnalysisType
    ) -> str:
        """
        Make a raw analysis request to Anthropic.
        
        Args:
            prompt: Analysis prompt
            content: Content to analyze
            analysis_type: Type of analysis being performed
            
        Returns:
            Raw response from Anthropic
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
        
        # Adjust max_tokens based on analysis type
        max_tokens = self.max_tokens
        if analysis_type == AnalysisType.TOPICS_OF_INTEREST:
            max_tokens = min(max_tokens, 1500)  # Topics usually need less space
        elif analysis_type == AnalysisType.BIO_UPDATE:
            max_tokens = min(max_tokens, 800)   # Bios should be concise
        
        return await self._make_request(messages, max_tokens)
"""
Tests for Anthropic provider implementation.

This module contains comprehensive tests for the Anthropic provider,
including mocked API responses and error handling scenarios.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from .anthropic_provider import AnthropicProvider
from .ai_service_interface import (
    AnalysisType,
    AIServiceError,
    AIServiceRateLimitError,
    AIServiceQuotaError,
    AIServiceTimeoutError
)
from .config import ProviderConfig, AIProvider


@pytest.fixture
def anthropic_config():
    """Create test configuration for Anthropic provider."""
    return ProviderConfig(
        provider_type=AIProvider.ANTHROPIC,
        api_key="test-api-key",
        model="claude-3-sonnet-20240229",
        max_tokens=2000,
        temperature=0.7,
        timeout=30,
        rate_limit_requests_per_minute=60,
        additional_config={
            'base_url': 'https://api.anthropic.com/v1'
        }
    )


@pytest.fixture
def anthropic_provider(anthropic_config):
    """Create Anthropic provider instance for testing."""
    return AnthropicProvider(anthropic_config)


class TestAnthropicProvider:
    """Test cases for Anthropic provider."""
    
    def test_initialization(self, anthropic_config):
        """Test Anthropic provider initialization."""
        provider = AnthropicProvider(anthropic_config)
        
        assert provider.api_key == "test-api-key"
        assert provider.model == "claude-3-sonnet-20240229"
        assert provider.max_tokens == 2000
        assert provider.temperature == 0.7
        assert provider.timeout == 30
        assert provider.rate_limit_rpm == 60
        assert provider.base_url == "https://api.anthropic.com/v1"
    
    def test_initialization_with_invalid_provider_type(self):
        """Test initialization with invalid provider type."""
        config = ProviderConfig(
            provider_type=AIProvider.OPENAI,  # Wrong type
            api_key="test-key"
        )
        
        with pytest.raises(ValueError, match="Invalid provider type for Anthropic"):
            AnthropicProvider(config)
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, anthropic_provider):
        """Test successful API request."""
        mock_response_data = {
            'content': [
                {
                    'text': 'Test response content'
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "test message"}]
            result = await anthropic_provider._make_request(messages)
            
            assert result == "Test response content"
            
            # Verify request was made correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://api.anthropic.com/v1/messages"
            
            # Check headers
            headers = call_args[1]['headers']
            assert headers['x-api-key'] == 'test-api-key'
            assert headers['Content-Type'] == 'application/json'
            assert headers['anthropic-version'] == '2023-06-01'
            
            # Check payload
            payload = call_args[1]['json']
            assert payload['model'] == 'claude-3-sonnet-20240229'
            assert payload['messages'] == messages
            assert payload['max_tokens'] == 2000
            assert payload['temperature'] == 0.7
    
    @pytest.mark.asyncio
    async def test_make_request_with_system_message(self, anthropic_provider):
        """Test API request with system message."""
        mock_response_data = {
            'content': [
                {
                    'text': 'Test response'
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "test message"}
            ]
            result = await anthropic_provider._make_request(messages)
            
            assert result == "Test response"
            
            # Check that system message was handled correctly
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert payload['system'] == "You are a helpful assistant"
            assert len(payload['messages']) == 1
            assert payload['messages'][0]['role'] == 'user'
    
    @pytest.mark.asyncio
    async def test_make_request_rate_limit_error(self, anthropic_provider):
        """Test handling of rate limit errors."""
        error_response = {
            'error': {
                'message': 'Rate limit exceeded'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {'retry-after': '60'}
            mock_response.json = AsyncMock(return_value=error_response)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(AIServiceRateLimitError) as exc_info:
                await anthropic_provider._make_request(messages)
            
            assert "Rate limit exceeded" in str(exc_info.value)
            assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    async def test_make_request_quota_error(self, anthropic_provider):
        """Test handling of quota exceeded errors."""
        error_response = {
            'error': {
                'message': 'Credit limit exceeded'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.headers = {}
            mock_response.json = AsyncMock(return_value=error_response)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(AIServiceQuotaError) as exc_info:
                await anthropic_provider._make_request(messages)
            
            assert "quota exceeded" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_make_request_timeout_error(self, anthropic_provider):
        """Test handling of timeout errors."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(AIServiceTimeoutError) as exc_info:
                await anthropic_provider._make_request(messages)
            
            assert "timed out" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_writing_style(self, anthropic_provider):
        """Test writing style analysis."""
        content_list = [
            "This is a professional post about technology trends.",
            "Here's another post with a casual tone and personal insights."
        ]
        
        mock_analysis = "The writing style demonstrates a sophisticated blend of professional expertise and personal authenticity..."
        
        with patch.object(anthropic_provider, '_make_request', return_value=mock_analysis) as mock_request:
            result = await anthropic_provider.analyze_writing_style(content_list)
            
            assert result == mock_analysis
            mock_request.assert_called_once()
            
            # Check that the request included both pieces of content
            call_args = mock_request.call_args[0][0]  # messages parameter
            user_message = call_args[1]['content']
            assert content_list[0] in user_message
            assert content_list[1] in user_message
    
    @pytest.mark.asyncio
    async def test_analyze_writing_style_with_existing_analysis(self, anthropic_provider):
        """Test writing style analysis with existing analysis."""
        content_list = ["New content to analyze"]
        existing_analysis = "Previous analysis results..."
        
        mock_analysis = "Updated analysis incorporating new content insights..."
        
        with patch.object(anthropic_provider, '_make_request', return_value=mock_analysis) as mock_request:
            result = await anthropic_provider.analyze_writing_style(content_list, existing_analysis)
            
            assert result == mock_analysis
            
            # Check that existing analysis was included in the prompt
            call_args = mock_request.call_args[0][0]
            user_message = call_args[1]['content']
            assert existing_analysis in user_message
    
    @pytest.mark.asyncio
    async def test_analyze_writing_style_empty_content(self, anthropic_provider):
        """Test writing style analysis with empty content."""
        result = await anthropic_provider.analyze_writing_style([])
        assert "No content available" in result
        
        existing_analysis = "Previous analysis"
        result = await anthropic_provider.analyze_writing_style([], existing_analysis)
        assert result == existing_analysis
    
    @pytest.mark.asyncio
    async def test_analyze_topics_of_interest(self, anthropic_provider):
        """Test topics of interest analysis."""
        content_list = [
            "Post about artificial intelligence and machine learning",
            "Discussion on software development best practices"
        ]
        
        mock_topics = [
            {
                "topic": "Artificial Intelligence",
                "confidence": 0.9,
                "frequency": 2,
                "keywords": ["AI", "machine learning", "neural networks"],
                "category": "technology",
                "description": "Deep focus on AI and ML technologies and applications"
            },
            {
                "topic": "Software Development",
                "confidence": 0.8,
                "frequency": 1,
                "keywords": ["development", "best practices", "coding"],
                "category": "technology",
                "description": "Software engineering methodologies and practices"
            }
        ]
        
        with patch.object(anthropic_provider, '_make_request', return_value=json.dumps(mock_topics)) as mock_request:
            result = await anthropic_provider.analyze_topics_of_interest(content_list)
            
            assert result == mock_topics
            assert len(result) == 2
            assert result[0]['topic'] == "Artificial Intelligence"
            assert result[1]['topic'] == "Software Development"
    
    @pytest.mark.asyncio
    async def test_analyze_topics_invalid_json(self, anthropic_provider):
        """Test topics analysis with invalid JSON response."""
        content_list = ["Test content"]
        
        # Mock response that's not valid JSON
        invalid_response = "Here are the key topics: AI and Machine Learning, Software Development"
        
        with patch.object(anthropic_provider, '_make_request', return_value=invalid_response):
            result = await anthropic_provider.analyze_topics_of_interest(content_list)
            
            # Should fallback to text extraction
            assert isinstance(result, list)
    
    @pytest.mark.asyncio
    async def test_update_user_bio(self, anthropic_provider):
        """Test user bio update."""
        current_bio = "Software engineer with 5 years of experience in web development."
        recent_content = [
            "Recently started working extensively with AI and machine learning projects",
            "Published research on neural network optimization techniques"
        ]
        
        updated_bio = "Software engineer with 5 years of experience in web development, now specializing in AI and machine learning research with published work in neural network optimization."
        
        with patch.object(anthropic_provider, '_make_request', return_value=updated_bio) as mock_request:
            result = await anthropic_provider.update_user_bio(current_bio, recent_content)
            
            assert result == updated_bio
            
            # Check that both current bio and recent content were included
            call_args = mock_request.call_args[0][0]
            user_message = call_args[1]['content']
            assert current_bio in user_message
            assert recent_content[0] in user_message
            assert recent_content[1] in user_message
    
    @pytest.mark.asyncio
    async def test_update_user_bio_empty_content(self, anthropic_provider):
        """Test bio update with empty recent content."""
        current_bio = "Original bio"
        result = await anthropic_provider.update_user_bio(current_bio, [])
        assert result == current_bio
    
    @pytest.mark.asyncio
    async def test_analyze_negative_patterns(self, anthropic_provider):
        """Test negative patterns analysis."""
        dismissed_posts = [
            {"content": "Post about controversial political topic"},
            {"content": "Another dismissed post with aggressive tone"}
        ]
        
        feedback_posts = [
            {
                "content": "Post with overly promotional content",
                "feedback": "Too sales-focused and pushy"
            }
        ]
        
        mock_analysis = "Key patterns to avoid: controversial political topics, aggressive or confrontational tone, overly promotional content that feels pushy or sales-focused..."
        
        with patch.object(anthropic_provider, '_make_request', return_value=mock_analysis) as mock_request:
            result = await anthropic_provider.analyze_negative_patterns(dismissed_posts, feedback_posts)
            
            assert result == mock_analysis
            
            # Check that both dismissed posts and feedback were included
            call_args = mock_request.call_args[0][0]
            user_message = call_args[1]['content']
            assert "controversial political topic" in user_message
            assert "Too sales-focused" in user_message
    
    @pytest.mark.asyncio
    async def test_analyze_negative_patterns_empty_data(self, anthropic_provider):
        """Test negative patterns analysis with no data."""
        result = await anthropic_provider.analyze_negative_patterns([], [])
        assert "No negative feedback data" in result
    
    @pytest.mark.asyncio
    async def test_make_analysis_request(self, anthropic_provider):
        """Test raw analysis request."""
        prompt = "Analyze this content for key themes"
        content = "Content to analyze"
        analysis_type = AnalysisType.WRITING_STYLE
        
        mock_response = "Analysis result"
        
        with patch.object(anthropic_provider, '_make_request', return_value=mock_response) as mock_request:
            result = await anthropic_provider.make_analysis_request(prompt, content, analysis_type)
            
            assert result == mock_response
            
            # Check that messages were formatted correctly
            call_args = mock_request.call_args[0]
            messages = call_args[0]
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[0]['content'] == prompt
            assert messages[1]['role'] == 'user'
            assert messages[1]['content'] == content
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, anthropic_provider):
        """Test successful health check."""
        with patch.object(anthropic_provider, 'make_analysis_request', return_value="OK") as mock_request:
            result = await anthropic_provider.health_check()
            
            assert result is True
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, anthropic_provider):
        """Test failed health check."""
        with patch.object(anthropic_provider, 'make_analysis_request', side_effect=AIServiceError("API error")):
            result = await anthropic_provider.health_check()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, anthropic_provider):
        """Test rate limiting functionality."""
        # Set a very low rate limit for testing
        anthropic_provider.rate_limit_rpm = 2
        
        # Mock time to control rate limiting
        with patch('time.time') as mock_time:
            mock_time.return_value = 1000.0
            
            # First request should go through
            await anthropic_provider._enforce_rate_limit()
            assert len(anthropic_provider._request_times) == 1
            
            # Second request should go through
            await anthropic_provider._enforce_rate_limit()
            assert len(anthropic_provider._request_times) == 2
            
            # Third request should be rate limited
            with patch('asyncio.sleep') as mock_sleep:
                await anthropic_provider._enforce_rate_limit()
                mock_sleep.assert_called_once()
    
    def test_extract_topics_from_text(self, anthropic_provider):
        """Test fallback topic extraction from text."""
        text_response = """
        Technology: Advanced focus on AI and machine learning applications
        Business Strategy: Entrepreneurship and startup growth methodologies
        Personal Development: Leadership skills and team management
        """
        
        topics = anthropic_provider._extract_topics_from_text(text_response)
        
        assert len(topics) == 3
        assert topics[0]['topic'] == 'Technology'
        assert topics[1]['topic'] == 'Business Strategy'
        assert topics[2]['topic'] == 'Personal Development'
        
        # Check default values
        for topic in topics:
            assert topic['confidence'] == 0.7
            assert topic['frequency'] == 1
            assert isinstance(topic['keywords'], list)
            assert topic['category'] == 'general'
    
    @pytest.mark.asyncio
    async def test_make_request_empty_content_response(self, anthropic_provider):
        """Test handling of empty content in response."""
        mock_response_data = {
            'content': []
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "test message"}]
            result = await anthropic_provider._make_request(messages)
            
            assert result == ""
    
    @pytest.mark.asyncio
    async def test_make_request_malformed_response(self, anthropic_provider):
        """Test handling of malformed response structure."""
        mock_response_data = {
            'content': [
                {
                    'type': 'text'
                    # Missing 'text' field
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            messages = [{"role": "user", "content": "test message"}]
            result = await anthropic_provider._make_request(messages)
            
            assert result == ""


if __name__ == "__main__":
    pytest.main([__file__])
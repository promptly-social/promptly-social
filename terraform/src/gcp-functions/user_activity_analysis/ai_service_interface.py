"""
Abstract base class and interfaces for AI analysis providers.

This module defines the provider-agnostic interface for AI analysis services,
enabling support for multiple AI providers (OpenAI, Anthropic, etc.) with
consistent error handling and retry logic.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import time
from functools import wraps

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    WRITING_STYLE = "writing_style"
    TOPICS_OF_INTEREST = "topics_of_interest"
    BIO_UPDATE = "bio_update"
    NEGATIVE_ANALYSIS = "negative_analysis"


@dataclass
class AnalysisRequest:
    """Request object for AI analysis."""
    analysis_type: AnalysisType
    content: List[str]
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result object from AI analysis."""
    analysis_type: AnalysisType
    result: Union[str, List[Dict[str, Any]], Dict[str, Any]]
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class AIServiceRateLimitError(AIServiceError):
    """Exception for rate limit errors."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AIServiceQuotaError(AIServiceError):
    """Exception for quota exceeded errors."""
    pass


class AIServiceTimeoutError(AIServiceError):
    """Exception for timeout errors."""
    pass


def retry_with_exponential_backoff(max_attempts: int = 3, initial_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for implementing exponential backoff retry logic.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except AIServiceRateLimitError as e:
                    last_exception = e
                    if e.retry_after:
                        delay = min(e.retry_after, max_delay)
                    else:
                        delay = min(initial_delay * (2 ** attempt), max_delay)
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Rate limit hit on attempt {attempt + 1}/{max_attempts}. "
                            f"Retrying in {delay} seconds..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Max retry attempts reached. Last error: {e}")
                        raise
                        
                except (AIServiceTimeoutError, AIServiceError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = min(initial_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"AI service error on attempt {attempt + 1}/{max_attempts}: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Max retry attempts reached. Last error: {e}")
                        raise
                        
                except Exception as e:
                    # Don't retry for unexpected errors
                    logger.error(f"Unexpected error in AI service call: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class AIProviderInterface(ABC):
    """Abstract base class for AI analysis providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace('provider', '')
    
    @abstractmethod
    async def analyze_writing_style(
        self, 
        content_list: List[str], 
        existing_analysis: Optional[str] = None
    ) -> str:
        """
        Analyze writing style from content.
        
        Args:
            content_list: List of content to analyze
            existing_analysis: Previous analysis to build upon
            
        Returns:
            Updated writing style analysis as text
        """
        pass
    
    @abstractmethod
    async def analyze_topics_of_interest(
        self, 
        content_list: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract topics of interest from content.
        
        Args:
            content_list: List of content to analyze
            
        Returns:
            List of topics with confidence scores and metadata
        """
        pass
    
    @abstractmethod
    async def update_user_bio(
        self, 
        current_bio: str, 
        recent_content: List[str]
    ) -> str:
        """
        Update user bio based on recent content.
        
        Args:
            current_bio: Current user bio
            recent_content: Recent content to incorporate
            
        Returns:
            Updated bio text
        """
        pass
    
    @abstractmethod
    async def analyze_negative_patterns(
        self, 
        dismissed_posts: List[Dict[str, Any]], 
        feedback_posts: List[Dict[str, Any]]
    ) -> str:
        """
        Analyze negative patterns from dismissed content.
        
        Args:
            dismissed_posts: Posts that were dismissed
            feedback_posts: Posts with negative feedback
            
        Returns:
            Analysis of patterns to avoid
        """
        pass
    
    @abstractmethod
    async def make_analysis_request(
        self, 
        prompt: str, 
        content: str, 
        analysis_type: AnalysisType
    ) -> str:
        """
        Make a raw analysis request to the AI provider.
        
        Args:
            prompt: Analysis prompt
            content: Content to analyze
            analysis_type: Type of analysis being performed
            
        Returns:
            Raw response from AI provider
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Check if the AI provider is available.
        
        Returns:
            True if provider is healthy, False otherwise
        """
        try:
            # Simple test request
            test_response = await self.make_analysis_request(
                "Respond with 'OK' if you can process this request.",
                "Test content",
                AnalysisType.WRITING_STYLE
            )
            return "OK" in test_response.upper()
        except Exception as e:
            logger.warning(f"Health check failed for {self.provider_name}: {e}")
            return False


class AIAnalysisService:
    """
    Main AI analysis service that coordinates between different providers.
    
    This service provides a unified interface for AI analysis while supporting
    multiple providers with fallback capabilities.
    """
    
    def __init__(self, primary_provider: AIProviderInterface, fallback_providers: Optional[List[AIProviderInterface]] = None):
        """
        Initialize the AI analysis service.
        
        Args:
            primary_provider: Primary AI provider to use
            fallback_providers: Optional list of fallback providers
        """
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or []
        self.all_providers = [primary_provider] + self.fallback_providers
    
    async def _execute_with_fallback(self, operation_name: str, *args, **kwargs):
        """
        Execute an operation with fallback to other providers if primary fails.
        
        Args:
            operation_name: Name of the method to call on providers
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            Result from the first successful provider
        """
        last_exception = None
        
        for i, provider in enumerate(self.all_providers):
            try:
                method = getattr(provider, operation_name)
                result = await method(*args, **kwargs)
                
                if i > 0:  # Used fallback provider
                    logger.info(f"Successfully used fallback provider {provider.provider_name} for {operation_name}")
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Provider {provider.provider_name} failed for {operation_name}: {e}")
                
                if i < len(self.all_providers) - 1:
                    logger.info(f"Trying fallback provider...")
                    continue
        
        # All providers failed
        logger.error(f"All providers failed for {operation_name}. Last error: {last_exception}")
        raise AIServiceError(f"All AI providers failed for {operation_name}: {last_exception}")
    
    @retry_with_exponential_backoff(max_attempts=3)
    async def analyze_writing_style(
        self, 
        content_list: List[str], 
        existing_analysis: Optional[str] = None
    ) -> str:
        """Analyze writing style with fallback support."""
        return await self._execute_with_fallback(
            'analyze_writing_style', 
            content_list, 
            existing_analysis
        )
    
    @retry_with_exponential_backoff(max_attempts=3)
    async def analyze_topics_of_interest(
        self, 
        content_list: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze topics of interest with fallback support."""
        return await self._execute_with_fallback(
            'analyze_topics_of_interest', 
            content_list
        )
    
    @retry_with_exponential_backoff(max_attempts=3)
    async def update_user_bio(
        self, 
        current_bio: str, 
        recent_content: List[str]
    ) -> str:
        """Update user bio with fallback support."""
        return await self._execute_with_fallback(
            'update_user_bio', 
            current_bio, 
            recent_content
        )
    
    @retry_with_exponential_backoff(max_attempts=3)
    async def analyze_negative_patterns(
        self, 
        dismissed_posts: List[Dict[str, Any]], 
        feedback_posts: List[Dict[str, Any]]
    ) -> str:
        """Analyze negative patterns with fallback support."""
        return await self._execute_with_fallback(
            'analyze_negative_patterns', 
            dismissed_posts, 
            feedback_posts
        )
    
    async def get_provider_status(self) -> Dict[str, bool]:
        """
        Get health status of all configured providers.
        
        Returns:
            Dictionary mapping provider names to health status
        """
        status = {}
        for provider in self.all_providers:
            status[provider.provider_name] = await provider.health_check()
        return status
    
    async def analyze_batch(self, requests: List[AnalysisRequest]) -> List[AnalysisResult]:
        """
        Process multiple analysis requests in batch.
        
        Args:
            requests: List of analysis requests
            
        Returns:
            List of analysis results
        """
        results = []
        
        for request in requests:
            start_time = time.time()
            
            try:
                if request.analysis_type == AnalysisType.WRITING_STYLE:
                    result = await self.analyze_writing_style(
                        request.content,
                        request.context.get('existing_analysis') if request.context else None
                    )
                elif request.analysis_type == AnalysisType.TOPICS_OF_INTEREST:
                    result = await self.analyze_topics_of_interest(request.content)
                elif request.analysis_type == AnalysisType.BIO_UPDATE:
                    result = await self.update_user_bio(
                        request.context.get('current_bio', '') if request.context else '',
                        request.content
                    )
                elif request.analysis_type == AnalysisType.NEGATIVE_ANALYSIS:
                    result = await self.analyze_negative_patterns(
                        request.context.get('dismissed_posts', []) if request.context else [],
                        request.context.get('feedback_posts', []) if request.context else []
                    )
                else:
                    raise AIServiceError(f"Unsupported analysis type: {request.analysis_type}")
                
                processing_time = time.time() - start_time
                
                results.append(AnalysisResult(
                    analysis_type=request.analysis_type,
                    result=result,
                    processing_time=processing_time,
                    metadata={'user_id': request.user_id} if request.user_id else None
                ))
                
            except Exception as e:
                logger.error(f"Failed to process analysis request {request.analysis_type}: {e}")
                results.append(AnalysisResult(
                    analysis_type=request.analysis_type,
                    result=None,
                    metadata={'error': str(e), 'user_id': request.user_id} if request.user_id else {'error': str(e)}
                ))
        
        return results
"""
AI Service Factory and Configuration Management.

This module implements the factory pattern for AI provider instantiation,
configuration-based provider selection, fallback mechanisms, and rate limiting.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

from .ai_service_interface import AIAnalysisService, AIProviderInterface, AIServiceError
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .config import AIServiceConfig, ProviderConfig, AIProvider, ConfigManager

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Status of an AI provider."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXCEEDED = "quota_exceeded"
    UNKNOWN = "unknown"


@dataclass
class ProviderHealth:
    """Health information for an AI provider."""
    provider_name: str
    status: ProviderStatus
    last_check: float
    error_count: int = 0
    last_error: Optional[str] = None
    response_time: Optional[float] = None


class RateLimitManager:
    """Manages rate limiting across multiple providers."""
    
    def __init__(self):
        self._provider_limits: Dict[str, Dict[str, Any]] = {}
        self._global_requests: List[float] = []
        self._global_limit_per_minute = 100  # Default global limit
    
    def configure_provider_limit(self, provider_name: str, requests_per_minute: int):
        """Configure rate limit for a specific provider."""
        self._provider_limits[provider_name] = {
            'rpm': requests_per_minute,
            'requests': []
        }
    
    async def check_rate_limit(self, provider_name: str) -> bool:
        """
        Check if a request can be made to the provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            True if request can be made, False if rate limited
        """
        current_time = time.time()
        
        # Check provider-specific rate limit
        if provider_name in self._provider_limits:
            provider_data = self._provider_limits[provider_name]
            # Remove requests older than 1 minute
            provider_data['requests'] = [
                t for t in provider_data['requests'] 
                if current_time - t < 60
            ]
            
            if len(provider_data['requests']) >= provider_data['rpm']:
                return False
        
        # Check global rate limit
        self._global_requests = [
            t for t in self._global_requests 
            if current_time - t < 60
        ]
        
        if len(self._global_requests) >= self._global_limit_per_minute:
            return False
        
        return True
    
    def record_request(self, provider_name: str):
        """Record a request for rate limiting purposes."""
        current_time = time.time()
        
        # Record provider-specific request
        if provider_name in self._provider_limits:
            self._provider_limits[provider_name]['requests'].append(current_time)
        
        # Record global request
        self._global_requests.append(current_time)


class HealthMonitor:
    """Monitors health of AI providers."""
    
    def __init__(self, check_interval: int = 300):
        """
        Initialize health monitor.
        
        Args:
            check_interval: Interval between health checks in seconds
        """
        self.check_interval = check_interval
        self._provider_health: Dict[str, ProviderHealth] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._providers: Dict[str, AIProviderInterface] = {}
    
    def register_provider(self, provider: AIProviderInterface):
        """Register a provider for health monitoring."""
        self._providers[provider.provider_name] = provider
        self._provider_health[provider.provider_name] = ProviderHealth(
            provider_name=provider.provider_name,
            status=ProviderStatus.UNKNOWN,
            last_check=0
        )
    
    async def check_provider_health(self, provider_name: str) -> ProviderHealth:
        """
        Check health of a specific provider.
        
        Args:
            provider_name: Name of the provider to check
            
        Returns:
            ProviderHealth object with current status
        """
        if provider_name not in self._providers:
            return ProviderHealth(
                provider_name=provider_name,
                status=ProviderStatus.UNKNOWN,
                last_check=time.time(),
                error_count=1,
                last_error="Provider not registered"
            )
        
        provider = self._providers[provider_name]
        health = self._provider_health[provider_name]
        
        start_time = time.time()
        try:
            is_healthy = await provider.health_check()
            response_time = time.time() - start_time
            
            if is_healthy:
                health.status = ProviderStatus.HEALTHY
                health.error_count = 0
                health.last_error = None
            else:
                health.status = ProviderStatus.UNHEALTHY
                health.error_count += 1
                health.last_error = "Health check failed"
            
            health.response_time = response_time
            
        except Exception as e:
            health.status = ProviderStatus.UNHEALTHY
            health.error_count += 1
            health.last_error = str(e)
            health.response_time = time.time() - start_time
        
        health.last_check = time.time()
        return health
    
    async def check_all_providers(self) -> Dict[str, ProviderHealth]:
        """Check health of all registered providers."""
        results = {}
        for provider_name in self._providers:
            results[provider_name] = await self.check_provider_health(provider_name)
        return results
    
    def get_provider_health(self, provider_name: str) -> Optional[ProviderHealth]:
        """Get cached health status of a provider."""
        return self._provider_health.get(provider_name)
    
    def get_healthy_providers(self) -> List[str]:
        """Get list of currently healthy providers."""
        healthy = []
        for name, health in self._provider_health.items():
            if health.status == ProviderStatus.HEALTHY:
                healthy.append(name)
        return healthy
    
    async def start_monitoring(self):
        """Start continuous health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            return
        
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop."""
        while True:
            try:
                await self.check_all_providers()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)


class AIServiceFactory:
    """Factory for creating and managing AI analysis services."""
    
    def __init__(self):
        self._rate_limit_manager = RateLimitManager()
        self._health_monitor = HealthMonitor()
        self._providers: Dict[str, AIProviderInterface] = {}
        self._service_cache: Optional[AIAnalysisService] = None
    
    def create_provider(self, config: ProviderConfig) -> AIProviderInterface:
        """
        Create an AI provider instance based on configuration.
        
        Args:
            config: Provider configuration
            
        Returns:
            AIProviderInterface instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        if config.provider_type == AIProvider.OPENAI:
            provider = OpenAIProvider(config)
        elif config.provider_type == AIProvider.ANTHROPIC:
            provider = AnthropicProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")
        
        # Configure rate limiting
        if config.rate_limit_requests_per_minute:
            self._rate_limit_manager.configure_provider_limit(
                provider.provider_name,
                config.rate_limit_requests_per_minute
            )
        
        # Register for health monitoring
        self._health_monitor.register_provider(provider)
        
        # Cache provider
        self._providers[provider.provider_name] = provider
        
        return provider
    
    def create_service(self, config: AIServiceConfig) -> AIAnalysisService:
        """
        Create an AI analysis service with configured providers.
        
        Args:
            config: Service configuration
            
        Returns:
            AIAnalysisService instance
        """
        # Create primary provider
        primary_provider = self.create_provider(config.primary_provider)
        
        # Create fallback providers
        fallback_providers = []
        for fallback_config in config.fallback_providers:
            try:
                fallback_provider = self.create_provider(fallback_config)
                fallback_providers.append(fallback_provider)
            except Exception as e:
                logger.warning(f"Failed to create fallback provider {fallback_config.provider_type}: {e}")
        
        # Create service with enhanced capabilities
        service = EnhancedAIAnalysisService(
            primary_provider=primary_provider,
            fallback_providers=fallback_providers,
            rate_limit_manager=self._rate_limit_manager,
            health_monitor=self._health_monitor
        )
        
        self._service_cache = service
        return service
    
    def create_service_from_environment(self) -> AIAnalysisService:
        """
        Create AI analysis service from environment configuration.
        
        Returns:
            AIAnalysisService instance
        """
        config = ConfigManager.load_from_environment()
        return self.create_service(config)
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all providers.
        
        Returns:
            Dictionary with provider status information
        """
        status = {}
        for name, provider in self._providers.items():
            health = self._health_monitor.get_provider_health(name)
            status[name] = {
                'provider_type': provider.__class__.__name__,
                'health_status': health.status.value if health else 'unknown',
                'last_check': health.last_check if health else 0,
                'error_count': health.error_count if health else 0,
                'last_error': health.last_error if health else None,
                'response_time': health.response_time if health else None
            }
        return status
    
    async def start_monitoring(self):
        """Start health monitoring for all providers."""
        await self._health_monitor.start_monitoring()
    
    async def stop_monitoring(self):
        """Stop health monitoring."""
        await self._health_monitor.stop_monitoring()


class EnhancedAIAnalysisService(AIAnalysisService):
    """Enhanced AI analysis service with rate limiting and health monitoring."""
    
    def __init__(
        self,
        primary_provider: AIProviderInterface,
        fallback_providers: Optional[List[AIProviderInterface]] = None,
        rate_limit_manager: Optional[RateLimitManager] = None,
        health_monitor: Optional[HealthMonitor] = None
    ):
        """
        Initialize enhanced AI analysis service.
        
        Args:
            primary_provider: Primary AI provider
            fallback_providers: List of fallback providers
            rate_limit_manager: Rate limiting manager
            health_monitor: Health monitoring manager
        """
        super().__init__(primary_provider, fallback_providers)
        self._rate_limit_manager = rate_limit_manager
        self._health_monitor = health_monitor
    
    async def _execute_with_fallback(self, operation_name: str, *args, **kwargs):
        """
        Execute operation with enhanced fallback logic including health checks.
        
        Args:
            operation_name: Name of the method to call
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            Result from the first successful provider
        """
        # Get healthy providers in order of preference
        available_providers = []
        
        # Check primary provider health
        if self._health_monitor:
            primary_health = self._health_monitor.get_provider_health(self.primary_provider.provider_name)
            if not primary_health or primary_health.status == ProviderStatus.HEALTHY:
                available_providers.append(self.primary_provider)
        else:
            available_providers.append(self.primary_provider)
        
        # Add healthy fallback providers
        for provider in self.fallback_providers:
            if self._health_monitor:
                health = self._health_monitor.get_provider_health(provider.provider_name)
                if health and health.status == ProviderStatus.HEALTHY:
                    available_providers.append(provider)
            else:
                available_providers.append(provider)
        
        if not available_providers:
            # If no providers are healthy, try all providers anyway
            available_providers = self.all_providers
        
        last_exception = None
        
        for i, provider in enumerate(available_providers):
            # Check rate limits
            if self._rate_limit_manager:
                can_make_request = await self._rate_limit_manager.check_rate_limit(provider.provider_name)
                if not can_make_request:
                    logger.warning(f"Rate limit exceeded for provider {provider.provider_name}, trying next provider")
                    continue
            
            try:
                method = getattr(provider, operation_name)
                result = await method(*args, **kwargs)
                
                # Record successful request
                if self._rate_limit_manager:
                    self._rate_limit_manager.record_request(provider.provider_name)
                
                if i > 0:  # Used fallback provider
                    logger.info(f"Successfully used fallback provider {provider.provider_name} for {operation_name}")
                
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Provider {provider.provider_name} failed for {operation_name}: {e}")
                
                # Update health status if we have a health monitor
                if self._health_monitor:
                    health = self._health_monitor.get_provider_health(provider.provider_name)
                    if health:
                        health.error_count += 1
                        health.last_error = str(e)
                
                if i < len(available_providers) - 1:
                    logger.info(f"Trying next provider...")
                    continue
        
        # All providers failed
        logger.error(f"All available providers failed for {operation_name}. Last error: {last_exception}")
        raise AIServiceError(f"All AI providers failed for {operation_name}: {last_exception}")


# Global factory instance
_factory_instance: Optional[AIServiceFactory] = None


def get_factory() -> AIServiceFactory:
    """Get the global AI service factory instance."""
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = AIServiceFactory()
    return _factory_instance


def create_ai_service(config: Optional[AIServiceConfig] = None) -> AIAnalysisService:
    """
    Create an AI analysis service.
    
    Args:
        config: Optional service configuration. If None, loads from environment.
        
    Returns:
        AIAnalysisService instance
    """
    factory = get_factory()
    
    if config:
        return factory.create_service(config)
    else:
        return factory.create_service_from_environment()


async def initialize_monitoring():
    """Initialize health monitoring for the global factory."""
    factory = get_factory()
    await factory.start_monitoring()


async def shutdown_monitoring():
    """Shutdown health monitoring for the global factory."""
    factory = get_factory()
    await factory.stop_monitoring()
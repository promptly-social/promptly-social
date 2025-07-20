"""
Integration tests for AI service factory and provider switching.

This module contains comprehensive tests for the AI service factory,
including provider switching, rate limiting, and health monitoring.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import time

from .ai_service_factory import (
    AIServiceFactory,
    EnhancedAIAnalysisService,
    RateLimitManager,
    HealthMonitor,
    ProviderStatus,
    ProviderHealth,
    get_factory,
    create_ai_service
)
from .ai_service_interface import AIServiceError, AIServiceRateLimitError
from .config import AIServiceConfig, ProviderConfig, AIProvider


@pytest.fixture
def openai_config():
    """Create OpenAI provider configuration."""
    return ProviderConfig(
        provider_type=AIProvider.OPENAI,
        api_key="test-openai-key",
        model="gpt-3.5-turbo",
        rate_limit_requests_per_minute=60
    )


@pytest.fixture
def anthropic_config():
    """Create Anthropic provider configuration."""
    return ProviderConfig(
        provider_type=AIProvider.ANTHROPIC,
        api_key="test-anthropic-key",
        model="claude-3-sonnet-20240229",
        rate_limit_requests_per_minute=50
    )


@pytest.fixture
def service_config(openai_config, anthropic_config):
    """Create AI service configuration."""
    return AIServiceConfig(
        primary_provider=openai_config,
        fallback_providers=[anthropic_config],
        max_retry_attempts=3,
        initial_retry_delay=1.0,
        max_retry_delay=60.0
    )


@pytest.fixture
def factory():
    """Create AI service factory."""
    return AIServiceFactory()


class TestRateLimitManager:
    """Test cases for rate limit manager."""
    
    def test_configure_provider_limit(self):
        """Test configuring provider rate limits."""
        manager = RateLimitManager()
        manager.configure_provider_limit("openai", 60)
        
        assert "openai" in manager._provider_limits
        assert manager._provider_limits["openai"]["rpm"] == 60
        assert manager._provider_limits["openai"]["requests"] == []
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit check when requests are allowed."""
        manager = RateLimitManager()
        manager.configure_provider_limit("openai", 60)
        
        # Should allow request when no previous requests
        can_request = await manager.check_rate_limit("openai")
        assert can_request is True
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit is exceeded."""
        manager = RateLimitManager()
        manager.configure_provider_limit("openai", 2)  # Very low limit
        
        # Make requests up to the limit
        for _ in range(2):
            manager.record_request("openai")
        
        # Next request should be rate limited
        can_request = await manager.check_rate_limit("openai")
        assert can_request is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_cleanup(self):
        """Test that old requests are cleaned up."""
        manager = RateLimitManager()
        manager.configure_provider_limit("openai", 60)
        
        # Mock time to simulate old requests
        with patch('time.time') as mock_time:
            # Add old request (more than 1 minute ago)
            mock_time.return_value = 1000.0
            manager.record_request("openai")
            
            # Move time forward by more than 1 minute
            mock_time.return_value = 1070.0
            
            # Should allow request as old request is cleaned up
            can_request = await manager.check_rate_limit("openai")
            assert can_request is True
    
    def test_record_request(self):
        """Test recording requests for rate limiting."""
        manager = RateLimitManager()
        manager.configure_provider_limit("openai", 60)
        
        manager.record_request("openai")
        
        assert len(manager._provider_limits["openai"]["requests"]) == 1
        assert len(manager._global_requests) == 1


class TestHealthMonitor:
    """Test cases for health monitor."""
    
    @pytest.fixture
    def health_monitor(self):
        """Create health monitor."""
        return HealthMonitor(check_interval=1)  # Short interval for testing
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock AI provider."""
        provider = MagicMock()
        provider.provider_name = "test_provider"
        provider.health_check = AsyncMock(return_value=True)
        return provider
    
    def test_register_provider(self, health_monitor, mock_provider):
        """Test registering a provider for monitoring."""
        health_monitor.register_provider(mock_provider)
        
        assert "test_provider" in health_monitor._providers
        assert "test_provider" in health_monitor._provider_health
        
        health = health_monitor._provider_health["test_provider"]
        assert health.provider_name == "test_provider"
        assert health.status == ProviderStatus.UNKNOWN
    
    @pytest.mark.asyncio
    async def test_check_provider_health_success(self, health_monitor, mock_provider):
        """Test successful health check."""
        health_monitor.register_provider(mock_provider)
        
        health = await health_monitor.check_provider_health("test_provider")
        
        assert health.status == ProviderStatus.HEALTHY
        assert health.error_count == 0
        assert health.last_error is None
        assert health.response_time is not None
        mock_provider.health_check.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_provider_health_failure(self, health_monitor, mock_provider):
        """Test failed health check."""
        mock_provider.health_check.return_value = False
        health_monitor.register_provider(mock_provider)
        
        health = await health_monitor.check_provider_health("test_provider")
        
        assert health.status == ProviderStatus.UNHEALTHY
        assert health.error_count == 1
        assert health.last_error == "Health check failed"
    
    @pytest.mark.asyncio
    async def test_check_provider_health_exception(self, health_monitor, mock_provider):
        """Test health check with exception."""
        mock_provider.health_check.side_effect = Exception("Connection error")
        health_monitor.register_provider(mock_provider)
        
        health = await health_monitor.check_provider_health("test_provider")
        
        assert health.status == ProviderStatus.UNHEALTHY
        assert health.error_count == 1
        assert "Connection error" in health.last_error
    
    @pytest.mark.asyncio
    async def test_check_all_providers(self, health_monitor):
        """Test checking all registered providers."""
        # Register multiple providers
        provider1 = MagicMock()
        provider1.provider_name = "provider1"
        provider1.health_check = AsyncMock(return_value=True)
        
        provider2 = MagicMock()
        provider2.provider_name = "provider2"
        provider2.health_check = AsyncMock(return_value=False)
        
        health_monitor.register_provider(provider1)
        health_monitor.register_provider(provider2)
        
        results = await health_monitor.check_all_providers()
        
        assert len(results) == 2
        assert results["provider1"].status == ProviderStatus.HEALTHY
        assert results["provider2"].status == ProviderStatus.UNHEALTHY
    
    def test_get_healthy_providers(self, health_monitor):
        """Test getting list of healthy providers."""
        # Manually set provider health
        health_monitor._provider_health["provider1"] = ProviderHealth(
            provider_name="provider1",
            status=ProviderStatus.HEALTHY,
            last_check=time.time()
        )
        health_monitor._provider_health["provider2"] = ProviderHealth(
            provider_name="provider2",
            status=ProviderStatus.UNHEALTHY,
            last_check=time.time()
        )
        
        healthy = health_monitor.get_healthy_providers()
        
        assert healthy == ["provider1"]


class TestAIServiceFactory:
    """Test cases for AI service factory."""
    
    def test_create_openai_provider(self, factory, openai_config):
        """Test creating OpenAI provider."""
        provider = factory.create_provider(openai_config)
        
        assert provider.provider_name == "openai"
        assert provider.api_key == "test-openai-key"
        assert "openai" in factory._providers
    
    def test_create_anthropic_provider(self, factory, anthropic_config):
        """Test creating Anthropic provider."""
        provider = factory.create_provider(anthropic_config)
        
        assert provider.provider_name == "anthropic"
        assert provider.api_key == "test-anthropic-key"
        assert "anthropic" in factory._providers
    
    def test_create_unsupported_provider(self, factory):
        """Test creating unsupported provider type."""
        config = ProviderConfig(
            provider_type="unsupported",  # Invalid type
            api_key="test-key"
        )
        
        with pytest.raises(ValueError, match="Unsupported provider type"):
            factory.create_provider(config)
    
    def test_create_service(self, factory, service_config):
        """Test creating AI analysis service."""
        service = factory.create_service(service_config)
        
        assert isinstance(service, EnhancedAIAnalysisService)
        assert service.primary_provider.provider_name == "openai"
        assert len(service.fallback_providers) == 1
        assert service.fallback_providers[0].provider_name == "anthropic"
    
    @patch.dict('os.environ', {
        'AI_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key',
        'AI_FALLBACK_PROVIDERS': 'anthropic',
        'ANTHROPIC_API_KEY': 'test-anthropic-key'
    })
    def test_create_service_from_environment(self, factory):
        """Test creating service from environment configuration."""
        service = factory.create_service_from_environment()
        
        assert isinstance(service, EnhancedAIAnalysisService)
        assert service.primary_provider.provider_name == "openai"
    
    def test_get_provider_status(self, factory, openai_config):
        """Test getting provider status."""
        provider = factory.create_provider(openai_config)
        
        status = factory.get_provider_status()
        
        assert "openai" in status
        assert status["openai"]["provider_type"] == "OpenAIProvider"
        assert "health_status" in status["openai"]


class TestEnhancedAIAnalysisService:
    """Test cases for enhanced AI analysis service."""
    
    @pytest.fixture
    def mock_primary_provider(self):
        """Create mock primary provider."""
        provider = MagicMock()
        provider.provider_name = "openai"
        provider.analyze_writing_style = AsyncMock(return_value="Primary analysis")
        return provider
    
    @pytest.fixture
    def mock_fallback_provider(self):
        """Create mock fallback provider."""
        provider = MagicMock()
        provider.provider_name = "anthropic"
        provider.analyze_writing_style = AsyncMock(return_value="Fallback analysis")
        return provider
    
    @pytest.fixture
    def enhanced_service(self, mock_primary_provider, mock_fallback_provider):
        """Create enhanced AI analysis service."""
        rate_manager = RateLimitManager()
        health_monitor = HealthMonitor()
        
        return EnhancedAIAnalysisService(
            primary_provider=mock_primary_provider,
            fallback_providers=[mock_fallback_provider],
            rate_limit_manager=rate_manager,
            health_monitor=health_monitor
        )
    
    @pytest.mark.asyncio
    async def test_successful_primary_provider(self, enhanced_service, mock_primary_provider):
        """Test successful execution with primary provider."""
        result = await enhanced_service.analyze_writing_style(["test content"])
        
        assert result == "Primary analysis"
        mock_primary_provider.analyze_writing_style.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_to_secondary_provider(self, enhanced_service, mock_primary_provider, mock_fallback_provider):
        """Test fallback to secondary provider when primary fails."""
        mock_primary_provider.analyze_writing_style.side_effect = AIServiceError("Primary failed")
        
        result = await enhanced_service.analyze_writing_style(["test content"])
        
        assert result == "Fallback analysis"
        mock_primary_provider.analyze_writing_style.assert_called_once()
        mock_fallback_provider.analyze_writing_style.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_all_providers_fail(self, enhanced_service, mock_primary_provider, mock_fallback_provider):
        """Test when all providers fail."""
        mock_primary_provider.analyze_writing_style.side_effect = AIServiceError("Primary failed")
        mock_fallback_provider.analyze_writing_style.side_effect = AIServiceError("Fallback failed")
        
        with pytest.raises(AIServiceError, match="All AI providers failed"):
            await enhanced_service.analyze_writing_style(["test content"])
    
    @pytest.mark.asyncio
    async def test_rate_limiting_skip_provider(self, enhanced_service, mock_primary_provider, mock_fallback_provider):
        """Test skipping rate-limited provider."""
        # Mock rate limit manager to block primary provider
        enhanced_service._rate_limit_manager.check_rate_limit = AsyncMock(side_effect=lambda name: name != "openai")
        
        result = await enhanced_service.analyze_writing_style(["test content"])
        
        assert result == "Fallback analysis"
        mock_primary_provider.analyze_writing_style.assert_not_called()
        mock_fallback_provider.analyze_writing_style.assert_called_once()


class TestGlobalFunctions:
    """Test cases for global factory functions."""
    
    def test_get_factory_singleton(self):
        """Test that get_factory returns singleton instance."""
        factory1 = get_factory()
        factory2 = get_factory()
        
        assert factory1 is factory2
    
    @patch.dict('os.environ', {
        'AI_PROVIDER': 'openai',
        'OPENAI_API_KEY': 'test-key'
    })
    def test_create_ai_service_from_environment(self):
        """Test creating AI service from environment."""
        service = create_ai_service()
        
        assert isinstance(service, EnhancedAIAnalysisService)
    
    def test_create_ai_service_with_config(self, service_config):
        """Test creating AI service with explicit config."""
        service = create_ai_service(service_config)
        
        assert isinstance(service, EnhancedAIAnalysisService)
        assert service.primary_provider.provider_name == "openai"


class TestIntegrationScenarios:
    """Integration test scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, service_config):
        """Test complete analysis workflow with provider switching."""
        factory = AIServiceFactory()
        
        # Mock the providers to simulate different behaviors
        with patch('terraform.src.gcp_functions.user_activity_analysis.openai_provider.OpenAIProvider') as MockOpenAI, \
             patch('terraform.src.gcp_functions.user_activity_analysis.anthropic_provider.AnthropicProvider') as MockAnthropic:
            
            # Configure OpenAI mock to fail
            openai_instance = MockOpenAI.return_value
            openai_instance.provider_name = "openai"
            openai_instance.analyze_writing_style = AsyncMock(side_effect=AIServiceRateLimitError("Rate limited"))
            
            # Configure Anthropic mock to succeed
            anthropic_instance = MockAnthropic.return_value
            anthropic_instance.provider_name = "anthropic"
            anthropic_instance.analyze_writing_style = AsyncMock(return_value="Anthropic analysis result")
            
            service = factory.create_service(service_config)
            
            # Should fallback to Anthropic when OpenAI is rate limited
            result = await service.analyze_writing_style(["test content"])
            
            assert result == "Anthropic analysis result"
            openai_instance.analyze_writing_style.assert_called_once()
            anthropic_instance.analyze_writing_style.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, service_config):
        """Test health monitoring integration."""
        factory = AIServiceFactory()
        
        with patch('terraform.src.gcp_functions.user_activity_analysis.openai_provider.OpenAIProvider') as MockOpenAI:
            openai_instance = MockOpenAI.return_value
            openai_instance.provider_name = "openai"
            openai_instance.health_check = AsyncMock(return_value=True)
            
            service = factory.create_service(service_config)
            
            # Start monitoring
            await factory.start_monitoring()
            
            # Give monitoring a moment to run
            await asyncio.sleep(0.1)
            
            # Check provider status
            status = factory.get_provider_status()
            assert "openai" in status
            
            # Stop monitoring
            await factory.stop_monitoring()


if __name__ == "__main__":
    pytest.main([__file__])
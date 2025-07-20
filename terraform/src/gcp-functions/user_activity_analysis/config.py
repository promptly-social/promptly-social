"""
Configuration management for AI analysis service.

This module handles configuration loading, validation, and provider selection
for the user activity analysis system.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class ProviderConfig:
    """Configuration for a specific AI provider."""
    provider_type: AIProvider
    api_key: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    timeout: Optional[int] = None
    rate_limit_requests_per_minute: Optional[int] = None
    additional_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIServiceConfig:
    """Main configuration for AI analysis service."""
    primary_provider: ProviderConfig
    fallback_providers: List[ProviderConfig] = field(default_factory=list)
    max_retry_attempts: int = 3
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    enable_health_checks: bool = True
    health_check_interval: int = 300  # seconds
    batch_size: int = 10
    analysis_timeout: int = 300  # seconds


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigManager:
    """Manages configuration loading and validation."""
    
    @staticmethod
    def load_from_environment() -> AIServiceConfig:
        """
        Load configuration from environment variables.
        
        Returns:
            AIServiceConfig instance
            
        Raises:
            ConfigurationError: If required configuration is missing or invalid
        """
        try:
            # Primary provider configuration
            primary_provider_type = os.getenv('AI_PROVIDER', 'openai').lower()
            if primary_provider_type not in [p.value for p in AIProvider]:
                raise ConfigurationError(f"Unsupported primary AI provider: {primary_provider_type}")
            
            primary_provider = ConfigManager._load_provider_config(
                AIProvider(primary_provider_type),
                is_primary=True
            )
            
            # Fallback providers configuration
            fallback_providers = []
            fallback_provider_types = os.getenv('AI_FALLBACK_PROVIDERS', '').split(',')
            fallback_provider_types = [p.strip().lower() for p in fallback_provider_types if p.strip()]
            
            for provider_type in fallback_provider_types:
                if provider_type and provider_type in [p.value for p in AIProvider]:
                    try:
                        fallback_config = ConfigManager._load_provider_config(
                            AIProvider(provider_type),
                            is_primary=False
                        )
                        fallback_providers.append(fallback_config)
                    except ConfigurationError as e:
                        logger.warning(f"Failed to load fallback provider {provider_type}: {e}")
            
            # Service configuration
            config = AIServiceConfig(
                primary_provider=primary_provider,
                fallback_providers=fallback_providers,
                max_retry_attempts=int(os.getenv('AI_MAX_RETRY_ATTEMPTS', '3')),
                initial_retry_delay=float(os.getenv('AI_INITIAL_RETRY_DELAY', '1.0')),
                max_retry_delay=float(os.getenv('AI_MAX_RETRY_DELAY', '60.0')),
                enable_health_checks=os.getenv('AI_ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
                health_check_interval=int(os.getenv('AI_HEALTH_CHECK_INTERVAL', '300')),
                batch_size=int(os.getenv('AI_BATCH_SIZE', '10')),
                analysis_timeout=int(os.getenv('AI_ANALYSIS_TIMEOUT', '300'))
            )
            
            ConfigManager._validate_config(config)
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(f"Configuration loading failed: {e}")
    
    @staticmethod
    def _load_provider_config(provider_type: AIProvider, is_primary: bool = True) -> ProviderConfig:
        """
        Load configuration for a specific provider.
        
        Args:
            provider_type: Type of AI provider
            is_primary: Whether this is the primary provider
            
        Returns:
            ProviderConfig instance
            
        Raises:
            ConfigurationError: If required configuration is missing
        """
        provider_name = provider_type.value.upper()
        
        # API key is required
        api_key_env = f'{provider_name}_API_KEY'
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            if is_primary:
                raise ConfigurationError(f"Missing required API key: {api_key_env}")
            else:
                raise ConfigurationError(f"Missing API key for fallback provider: {api_key_env}")
        
        # Provider-specific configuration
        config = ProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            model=os.getenv(f'{provider_name}_MODEL'),
            max_tokens=ConfigManager._get_int_env(f'{provider_name}_MAX_TOKENS'),
            temperature=ConfigManager._get_float_env(f'{provider_name}_TEMPERATURE'),
            timeout=ConfigManager._get_int_env(f'{provider_name}_TIMEOUT', 30),
            rate_limit_requests_per_minute=ConfigManager._get_int_env(f'{provider_name}_RATE_LIMIT_RPM')
        )
        
        # Load additional provider-specific configuration
        if provider_type == AIProvider.OPENAI:
            config.additional_config.update({
                'organization': os.getenv('OPENAI_ORGANIZATION'),
                'base_url': os.getenv('OPENAI_BASE_URL'),
            })
        elif provider_type == AIProvider.ANTHROPIC:
            config.additional_config.update({
                'base_url': os.getenv('ANTHROPIC_BASE_URL'),
            })
        
        return config
    
    @staticmethod
    def _get_int_env(key: str, default: Optional[int] = None) -> Optional[int]:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}")
            return default
    
    @staticmethod
    def _get_float_env(key: str, default: Optional[float] = None) -> Optional[float]:
        """Get float value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Invalid float value for {key}: {value}")
            return default
    
    @staticmethod
    def _validate_config(config: AIServiceConfig) -> None:
        """
        Validate the loaded configuration.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate retry configuration
        if config.max_retry_attempts < 1:
            raise ConfigurationError("max_retry_attempts must be at least 1")
        
        if config.initial_retry_delay <= 0:
            raise ConfigurationError("initial_retry_delay must be positive")
        
        if config.max_retry_delay <= config.initial_retry_delay:
            raise ConfigurationError("max_retry_delay must be greater than initial_retry_delay")
        
        # Validate batch configuration
        if config.batch_size < 1:
            raise ConfigurationError("batch_size must be at least 1")
        
        if config.analysis_timeout < 1:
            raise ConfigurationError("analysis_timeout must be at least 1 second")
        
        # Validate provider configurations
        ConfigManager._validate_provider_config(config.primary_provider)
        
        for fallback_config in config.fallback_providers:
            ConfigManager._validate_provider_config(fallback_config)
    
    @staticmethod
    def _validate_provider_config(config: ProviderConfig) -> None:
        """
        Validate a provider configuration.
        
        Args:
            config: Provider configuration to validate
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not config.api_key:
            raise ConfigurationError(f"API key is required for {config.provider_type.value}")
        
        if config.max_tokens is not None and config.max_tokens < 1:
            raise ConfigurationError(f"max_tokens must be positive for {config.provider_type.value}")
        
        if config.temperature is not None and not (0 <= config.temperature <= 2):
            raise ConfigurationError(f"temperature must be between 0 and 2 for {config.provider_type.value}")
        
        if config.timeout is not None and config.timeout < 1:
            raise ConfigurationError(f"timeout must be at least 1 second for {config.provider_type.value}")
        
        if config.rate_limit_requests_per_minute is not None and config.rate_limit_requests_per_minute < 1:
            raise ConfigurationError(f"rate_limit_requests_per_minute must be positive for {config.provider_type.value}")


def get_default_config() -> AIServiceConfig:
    """
    Get default configuration for development/testing.
    
    Returns:
        AIServiceConfig with default values
    """
    return AIServiceConfig(
        primary_provider=ProviderConfig(
            provider_type=AIProvider.OPENAI,
            api_key="test-key",
            model="gpt-3.5-turbo",
            max_tokens=2000,
            temperature=0.7,
            timeout=30
        ),
        max_retry_attempts=3,
        initial_retry_delay=1.0,
        max_retry_delay=60.0,
        enable_health_checks=True,
        health_check_interval=300,
        batch_size=10,
        analysis_timeout=300
    )


def load_config() -> AIServiceConfig:
    """
    Load configuration from environment or return default.
    
    Returns:
        AIServiceConfig instance
    """
    try:
        return ConfigManager.load_from_environment()
    except ConfigurationError as e:
        logger.warning(f"Failed to load configuration from environment: {e}")
        logger.info("Using default configuration")
        return get_default_config()
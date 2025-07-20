"""
Shared model configuration for PydanticAI agents.
Provides consistent model settings and fallback configurations across all services.
"""

from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from app.core.config import settings


class ModelConfig:
    """Centralized model configuration for consistent setup across services."""

    def __init__(self):
        self.provider = OpenRouterProvider(
            api_key=settings.openrouter_api_key,
        )

        # Parse fallback models
        self.chat_fallback_models = [
            model.strip()
            for model in settings.openrouter_models_fallback.split(",")
            if model.strip()
        ]

        self.large_fallback_models = [
            model.strip()
            for model in settings.openrouter_large_models_fallback.split(",")
            if model.strip()
        ]

    def get_chat_model(self) -> OpenAIModel:
        """Get the primary chat model with OpenRouter provider."""
        return OpenAIModel(
            settings.openrouter_model_primary,
            provider=self.provider,
        )

    def get_large_model(self) -> OpenAIModel:
        """Get the primary large model with OpenRouter provider."""
        return OpenAIModel(
            settings.openrouter_large_model_primary,
            provider=self.provider,
        )

    def get_chat_model_settings(self) -> OpenAIModelSettings:
        """Get model settings for chat operations with fallback configuration."""
        return OpenAIModelSettings(
            temperature=settings.openrouter_model_temperature,
            extra_body={"models": self.chat_fallback_models},
        )

    def get_large_model_settings(self) -> OpenAIModelSettings:
        """Get model settings for large model operations with fallback configuration."""
        return OpenAIModelSettings(
            temperature=settings.openrouter_large_model_temperature,
            extra_body={"models": self.large_fallback_models},
        )


# Singleton instance for reuse across services
model_config = ModelConfig()

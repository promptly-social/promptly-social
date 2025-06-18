"""
Application configuration management using Pydantic Settings.
Follows SOC-II and GDPR compliance standards.
"""

from typing import List, Optional
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    app_name: str = Field(default="Promptly API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="production")

    # Database
    database_url: str = Field(default="sqlite:///./app.db")
    database_url_async: str = Field(default="sqlite+aiosqlite:///./app.db")

    # Supabase
    supabase_url: str = Field(default="https://test.supabase.co")
    supabase_key: str = Field(default="test_key")
    supabase_service_key: str = Field(default="test_service_key")

    # Security
    secret_key: str = Field(default="dev_secret_key")
    jwt_secret_key: str = Field(default="dev_jwt_secret")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    bcrypt_rounds: int = Field(default=12)

    # CORS - Use string instead of List to avoid JSON parsing
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # OAuth
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of: {allowed_envs}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()

    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins:
            return []
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


# Global settings instance
settings = Settings()

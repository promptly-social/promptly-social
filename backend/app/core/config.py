"""
Application configuration management using Pydantic Settings.
Follows SOC-II and GDPR compliance standards.
"""

from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator
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
    backend_url: str = Field(default="http://localhost:8000")
    frontend_url: str = Field(default="http://localhost:8080")

    # GCP
    gcp_project_id: str = Field(default="promptly-social-staging")
    gcp_location: str = Field(default="us-central1")

    # Service account email for Cloud Scheduler OIDC token
    gcp_app_service_account_email: Optional[str] = Field(
        default=None, alias="APP_SERVICE_ACCOUNT_EMAIL"
    )

    # Database
    database_url: str = Field(default="sqlite:///./app.db")
    use_local_db: bool = Field(
        default=False
    )  # Set to True to use local DB instead of Cloud SQL

    # Cloud SQL specific settings
    cloud_sql_instance_connection_name: Optional[str] = Field(default=None)
    cloud_sql_database_name: Optional[str] = Field(default=None)
    cloud_sql_user: Optional[str] = Field(default=None)
    cloud_sql_password: Optional[str] = Field(default=None)

    # Connection pooling settings
    db_pool_size: int = Field(default=10)
    db_max_overflow: int = Field(default=20)
    db_pool_timeout: int = Field(default=30)
    db_pool_recycle: int = Field(default=3600)

    # Migration settings
    auto_apply_migrations: bool = Field(default=True)
    migration_timeout: int = Field(default=300)
    migration_lock_timeout: int = Field(default=60)

    # Supabase
    supabase_url: str = Field(default="https://test.supabase.co")
    supabase_key: str = Field(default="test_key")
    supabase_service_key: str = Field(default="test_service_key")

    # Security
    jwt_secret_key: str = Field(default="dev_jwt_secret")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=1440)
    refresh_token_expire_days: int = Field(default=7)

    # CORS - Use string instead of List to avoid JSON parsing
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # OAuth
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)
    linkedin_client_id: Optional[str] = Field(default=None)
    linkedin_client_secret: Optional[str] = Field(default=None)

    # LinkedIn Analytics OAuth (separate API access for analytics scopes)
    linkedin_analytics_client_id: Optional[str] = Field(default=None)
    linkedin_analytics_client_secret: Optional[str] = Field(default=None)

    # OpenRouter LLM Configuration
    openrouter_api_key: Optional[str] = Field(default="dummy-openrouter-api-key")
    openrouter_model_primary: str = Field(default="google/gemini-2.5-flash")
    openrouter_models_fallback: str = Field(default="deepseek/deepseek-chat-v3-0324")
    openrouter_model_temperature: float = Field(default=0.0)
    openrouter_large_model_primary: str = Field(default="google/gemini-2.5-pro")
    openrouter_large_models_fallback: str = Field(default="anthropic/claude-sonnet-4")
    openrouter_large_model_temperature: float = Field(default=0.0)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)

    # Cloud function URLs
    gcp_analysis_function_url: Optional[str] = Field(default=None)
    gcp_service_account_key_path: Optional[str] = Field(default=None)
    gcp_generate_suggestions_function_url: Optional[str] = Field(default=None)
    post_media_bucket_name: Optional[str] = Field(default=None)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_envs = ["development", "staging", "production", "test"]
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

    def get_cloud_sql_database_url(self) -> str:
        """
        Build Cloud SQL connection string from individual components.

        Returns:
            str: Cloud SQL PostgreSQL connection URL
        """
        if all(
            [
                self.cloud_sql_instance_connection_name,
                self.cloud_sql_database_name,
                self.cloud_sql_user,
                self.cloud_sql_password,
            ]
        ):
            # Build Cloud SQL connection string
            return (
                f"postgresql://{self.cloud_sql_user}:{self.cloud_sql_password}"
                f"@/{self.cloud_sql_database_name}"
                f"?host=/cloudsql/{self.cloud_sql_instance_connection_name}"
            )
        return None

    def get_database_url(self) -> str:
        """
        Get the appropriate database URL based on configuration.

        Returns:
            str: Database URL (respects test environment and local development settings)
        """
        # In test environment, always use the database_url (usually SQLite)
        if self.environment in ["test", "testing"]:
            return self.database_url

        # If use_local_db is True, use local database instead of Cloud SQL
        if self.use_local_db:
            return self.database_url

        # Otherwise, use Cloud SQL if configured
        cloud_sql_url = self.get_cloud_sql_database_url()
        if cloud_sql_url:
            return cloud_sql_url
        return self.database_url

    def get_async_database_url(self) -> str:
        """
        Convert the base database URL to async version.

        Returns:
            str: Async database URL with appropriate driver
        """
        base_url = self.get_database_url()

        if base_url.startswith("postgresql://"):
            async_url = base_url.replace("postgresql://", "postgresql+asyncpg://")
            return async_url
        elif base_url.startswith("postgresql+asyncpg://"):
            # Already async PostgreSQL URL
            return base_url
        elif base_url.startswith("sqlite://"):
            async_url = base_url.replace("sqlite://", "sqlite+aiosqlite://")
            return async_url
        elif base_url.startswith("sqlite:///"):
            async_url = base_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            return async_url
        elif base_url.startswith("sqlite+aiosqlite://"):
            # Already async SQLite URL
            return base_url
        else:
            # For other databases, assume they already have the correct driver
            return base_url


# Global settings instance
settings = Settings()

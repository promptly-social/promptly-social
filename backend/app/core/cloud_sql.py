"""
Google Cloud SQL connection utilities and factory.
Provides connection management for Cloud SQL PostgreSQL instances.
"""

import logging
from typing import Optional

from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.pool import NullPool


from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudSQLConnectionFactory:
    """Factory for creating Cloud SQL database connections."""

    def __init__(self):
        self._connector: Optional[Connector] = None
        self._async_connector: Optional[Connector] = None

    def _get_connector(self) -> Connector:
        """Get or create a Cloud SQL connector instance."""
        if self._connector is None:
            self._connector = Connector(refresh_strategy="LAZY")
        return self._connector

    def _get_async_connector(self) -> Connector:
        """Get or create an async Cloud SQL connector instance."""
        if self._async_connector is None:
            self._async_connector = Connector(refresh_strategy="LAZY")
        return self._async_connector

    def create_engine(self) -> Engine:
        """
        Create a synchronous SQLAlchemy engine for Cloud SQL.

        Returns:
            Engine: Configured SQLAlchemy engine
        """
        try:
            connector = self._get_connector()

            def getconn():
                """Create a database connection using Cloud SQL connector."""
                logger.info(
                    f"Connecting to Cloud SQL instance: {settings.cloud_sql_instance_connection_name}"
                )
                return connector.connect(
                    settings.cloud_sql_instance_connection_name,
                    "pg8000",
                    user=settings.cloud_sql_user,
                    password=settings.cloud_sql_password,
                    db=settings.cloud_sql_database_name,
                    ip_type=IPTypes.PUBLIC,  # Use public IP by default
                )

            # Create engine with connection factory - don't specify a URL, just use the creator
            engine = create_engine(
                "postgresql+pg8000://",  # Minimal URL since we're using creator
                creator=getconn,
                poolclass=NullPool,  # Use NullPool to avoid connection pooling issues
                echo=settings.debug,
                pool_pre_ping=True,
            )

            logger.info("Created Cloud SQL sync engine successfully")
            return engine

        except Exception as e:
            logger.error(f"Failed to create Cloud SQL sync engine: {e}")
            raise

    def create_async_engine(self) -> AsyncEngine:
        """
        Create an asynchronous SQLAlchemy engine for Cloud SQL.

        Returns:
            AsyncEngine: Configured async SQLAlchemy engine
        """
        try:
            connector = self._get_async_connector()

            async def getconn():
                """Create an async database connection using Cloud SQL connector."""
                return await connector.connect_async(
                    settings.cloud_sql_instance_connection_name,
                    "asyncpg",
                    user=settings.cloud_sql_user,
                    password=settings.cloud_sql_password,
                    db=settings.cloud_sql_database_name,
                    ip_type=IPTypes.PUBLIC,  # Use public IP by default
                )

            # Create async engine with connection factory
            engine = create_async_engine(
                "postgresql+asyncpg://",
                async_creator=getconn,
                poolclass=NullPool,  # Use NullPool to avoid connection pooling issues
                echo=settings.debug,
                pool_pre_ping=True,
            )

            logger.info("Created Cloud SQL async engine successfully")
            return engine

        except Exception as e:
            logger.error(f"Failed to create Cloud SQL async engine: {e}")
            raise

    def validate_connection(self) -> bool:
        """
        Validate Cloud SQL connection by attempting to connect.

        Returns:
            bool: True if connection is successful
        """
        try:
            engine = self.create_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Cloud SQL connection validation failed: {e}")
            return False

    def close_connectors(self) -> None:
        """Close all connector instances."""
        if self._connector:
            self._connector.close()
            self._connector = None
        if self._async_connector:
            self._async_connector.close()
            self._async_connector = None


# Global Cloud SQL connection factory instance
cloud_sql_factory = CloudSQLConnectionFactory()

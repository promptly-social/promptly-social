"""
Shared Cloud SQL client for GCP Cloud Functions.
Provides database connection and query utilities using Cloud SQL Python Connector.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
import asyncio

from google.cloud.sql.connector import Connector, IPTypes
from sqlalchemy import create_engine, text, Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class CloudSQLClient:
    """Cloud SQL client for database operations."""

    def __init__(self):
        self.instance_connection_name = os.getenv("CLOUD_SQL_INSTANCE_CONNECTION_NAME")
        self.database_name = os.getenv("CLOUD_SQL_DATABASE_NAME")
        self.user = os.getenv("CLOUD_SQL_USER")
        self.password = os.getenv("CLOUD_SQL_PASSWORD")

        if not all(
            [
                self.instance_connection_name,
                self.database_name,
                self.user,
                self.password,
            ]
        ):
            raise ValueError("Missing required Cloud SQL environment variables")

        self._connector: Optional[Connector] = None
        self._async_connector: Optional[Connector] = None
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None

    def _get_connector(self) -> Connector:
        """Get or create a Cloud SQL connector instance."""
        if self._connector is None:
            self._connector = Connector()
        return self._connector

    def _get_async_connector(self) -> Connector:
        """Get or create an async Cloud SQL connector instance."""
        if self._async_connector is None:
            self._async_connector = Connector()
        return self._async_connector

    def get_engine(self) -> Engine:
        """Get or create a synchronous SQLAlchemy engine."""
        if self._engine is None:
            connector = self._get_connector()

            def getconn():
                return connector.connect(
                    self.instance_connection_name,
                    "pg8000",
                    user=self.user,
                    password=self.password,
                    db=self.database_name,
                    ip_type=IPTypes.PUBLIC,
                )

            self._engine = create_engine(
                "postgresql+pg8000://",
                creator=getconn,
                poolclass=NullPool,
                echo=False,
                pool_pre_ping=True,
            )

        return self._engine

    def get_async_engine(self) -> AsyncEngine:
        """Get or create an asynchronous SQLAlchemy engine."""
        if self._async_engine is None:
            connector = self._get_async_connector()

            async def getconn():
                return await connector.connect_async(
                    self.instance_connection_name,
                    "asyncpg",
                    user=self.user,
                    password=self.password,
                    db=self.database_name,
                    ip_type=IPTypes.PUBLIC,
                )

            self._async_engine = create_async_engine(
                "postgresql+asyncpg://",
                async_creator=getconn,
                poolclass=NullPool,
                echo=False,
                pool_pre_ping=True,
            )

        return self._async_engine

    def execute_query(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries."""
        engine = self.get_engine()

        with engine.connect() as conn:
            # Use transaction for INSERT/UPDATE/DELETE operations that return data
            query_upper = query.strip().upper()
            if query_upper.startswith(("INSERT", "UPDATE", "DELETE")):
                with conn.begin():
                    result = conn.execute(text(query), params or {})
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result.fetchall()]
            else:
                # Regular SELECT queries don't need transactions
                result = conn.execute(text(query), params or {})
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]

    async def execute_query_async(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query asynchronously and return results as list of dictionaries."""
        engine = self.get_async_engine()

        async with engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]

    def execute_update(self, query: str, params: Dict[str, Any] = None) -> int:
        """Execute an update/insert/delete query and return affected rows count."""
        engine = self.get_engine()

        with engine.connect() as conn:
            with conn.begin():
                result = conn.execute(text(query), params or {})
                return result.rowcount

    async def execute_update_async(
        self, query: str, params: Dict[str, Any] = None
    ) -> int:
        """Execute an update/insert/delete query asynchronously and return affected rows count."""
        engine = self.get_async_engine()

        async with engine.connect() as conn:
            async with conn.begin():
                result = await conn.execute(text(query), params or {})
                return result.rowcount

    @asynccontextmanager
    async def get_async_session(self):
        """Get an async database session."""
        engine = self.get_async_engine()
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    def close(self):
        """Close all connections and connectors."""
        if self._connector:
            self._connector.close()
            self._connector = None
        if self._async_connector:
            self._async_connector.close()
            self._async_connector = None
        if self._engine:
            self._engine.dispose()
            self._engine = None
        if self._async_engine:
            # Handle async engine disposal safely
            try:
                # Try to get the current event loop
                asyncio.get_running_loop()
                # If we have a running loop, create a task
                asyncio.create_task(self._async_engine.dispose())
            except RuntimeError:
                # No event loop running, we need to handle this differently
                try:
                    # Try to run the disposal in a new event loop
                    asyncio.run(self._async_engine.dispose())
                except Exception as e:
                    logger.warning(f"Could not properly dispose async engine: {e}")
                    # As a last resort, try synchronous disposal if available
                    try:
                        # Some engines support sync disposal
                        if hasattr(self._async_engine, "sync_engine"):
                            self._async_engine.sync_engine.dispose()
                    except Exception as sync_error:
                        logger.warning(
                            f"Could not dispose sync engine either: {sync_error}"
                        )
            except Exception as e:
                logger.warning(f"Error during async engine disposal: {e}")
            finally:
                self._async_engine = None


# Global client instance
_client: Optional[CloudSQLClient] = None


def get_cloud_sql_client() -> CloudSQLClient:
    """Get the global Cloud SQL client instance."""
    global _client
    if _client is None:
        _client = CloudSQLClient()
    return _client


def close_cloud_sql_client():
    """Close the global Cloud SQL client."""
    global _client
    if _client:
        _client.close()
        _client = None

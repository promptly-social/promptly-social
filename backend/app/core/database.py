"""
Database configuration and session management.
Uses SQLAlchemy with async support and connection pooling.
Supports both local databases and Google Cloud SQL.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


# Metadata for naming conventions (helpful for migrations)
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = metadata


def _is_cloud_sql_configured() -> bool:
    """Check if Cloud SQL is properly configured."""
    cloud_sql_configured = all(
        [
            settings.cloud_sql_instance_connection_name,
            settings.cloud_sql_database_name,
            settings.cloud_sql_user,
            settings.cloud_sql_password,
        ]
    )

    if cloud_sql_configured:
        logger.info("Cloud SQL configuration detected")
        logger.info(f"Instance: {settings.cloud_sql_instance_connection_name}")
        logger.info(f"Database: {settings.cloud_sql_database_name}")
        logger.info(f"User: {settings.cloud_sql_user}")
    else:
        logger.info("Cloud SQL not configured, using fallback database URL")
        logger.info(f"Fallback URL: {settings.database_url}")

    return cloud_sql_configured


def get_engine_config():
    """Get engine configuration based on database URL."""
    db_url = settings.get_async_database_url()
    is_sqlite = db_url.startswith("sqlite")
    is_cloud_sql = _is_cloud_sql_configured()

    if is_sqlite:
        return {"echo": settings.debug, "connect_args": {"check_same_thread": False}}
    elif is_cloud_sql:
        # Cloud SQL uses its own connection management
        return {
            "echo": settings.debug,
            "pool_pre_ping": True,
        }
    else:
        return {
            "echo": settings.debug,
            "pool_pre_ping": True,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_timeout": settings.db_pool_timeout,
        }


def get_sync_engine_config():
    """Get sync engine configuration based on database URL."""
    db_url = settings.get_database_url()
    is_sqlite = db_url.startswith("sqlite")
    is_cloud_sql = _is_cloud_sql_configured()

    if is_sqlite:
        return {"echo": settings.debug, "connect_args": {"check_same_thread": False}}
    elif is_cloud_sql:
        # Cloud SQL uses its own connection management
        return {
            "echo": settings.debug,
            "pool_pre_ping": True,
        }
    else:
        return {
            "echo": settings.debug,
            "pool_pre_ping": True,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_recycle": settings.db_pool_recycle,
            "pool_timeout": settings.db_pool_timeout,
        }


def _create_engines():
    """Create database engines based on configuration."""

    # Use Cloud SQL connection factory
    from app.core.cloud_sql import cloud_sql_factory

    logger.info("Using Google Cloud SQL for database connections")
    async_engine = cloud_sql_factory.create_async_engine()
    sync_engine = cloud_sql_factory.create_engine()

    return async_engine, sync_engine


# Create engines based on configuration
async_engine, sync_engine = _create_engines()

AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_db_with_user_context(
    user_id: str,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session with user context set for RLS.
    This should be used when you have a known user context to set.

    Args:
        user_id: UUID string of the current user

    Yields:
        AsyncSession: Database session with user context set
    """
    from app.core.rls import AuthContextHandler

    async with AsyncSessionLocal() as session:
        try:
            # Set user context for RLS
            await AuthContextHandler.set_current_user(session, user_id)
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            # Clear user context before closing
            try:
                await AuthContextHandler.clear_user_context(session)
            except Exception:
                # Don't fail if context clearing fails
                pass
            await session.close()


def get_sync_db():
    """
    Dependency to get sync database session.
    Used for migrations and sync operations.

    Yields:
        Session: Sync database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """
    Initialize database connection and apply pending migrations.
    This is typically called during application startup.

    Note: Table creation is now handled by migrations, not automatic creation.
    """
    # Import all models to ensure they are registered
    from app.models import (
        user,
        posts,
        idea_bank,
        chat,
        onboarding,
        profile,
        content_strategies,
        daily_suggestion_schedule,
    )  # noqa: F401

    # Import and run migrations
    from app.core.migrations import migration_manager
    from app.core.rls import rls_manager

    logger.info("Initializing database...")

    # Validate database connection first
    if not migration_manager.validate_database_connection():
        raise RuntimeError("Database connection validation failed")

    # Apply pending migrations automatically with proper error handling
    try:
        logger.info("Checking for pending migrations...")
        pending_migrations = migration_manager.check_pending_migrations()

        if pending_migrations:
            logger.info(
                f"Found {len(pending_migrations)} pending migrations: {pending_migrations}"
            )

            # Apply migrations with locking and error handling
            migration_success = migration_manager.auto_migrate_on_startup()

            if migration_success:
                logger.info("All pending migrations applied successfully")
            else:
                logger.warning("Migration completed with warnings")
        else:
            logger.info("No pending migrations found")

        # Validate RLS setup after migrations
        try:
            async with AsyncSessionLocal() as session:
                rls_valid = await rls_manager.validate_rls_setup(session)
                if rls_valid:
                    logger.info("RLS validation completed successfully")
                else:
                    logger.warning(
                        "RLS validation found issues - some policies may not be properly configured"
                    )
        except Exception as rls_error:
            logger.error(f"RLS validation failed: {rls_error}")
            # Don't fail startup for RLS validation issues in non-production
            if settings.environment == "production":
                raise RuntimeError(f"RLS validation failed in production: {rls_error}")

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Log migration history for debugging
        try:
            history = migration_manager.get_migration_history()
            logger.info(f"Migration history: {history}")
        except Exception:
            pass  # Don't fail if we can't get history
        raise RuntimeError(f"Database initialization failed: {e}")


async def close_db() -> None:
    """
    Close database connections.
    This is typically called during application shutdown.
    """
    await async_engine.dispose()

    # Close Cloud SQL connectors if they were used
    if _is_cloud_sql_configured():
        from app.core.cloud_sql import cloud_sql_factory

        cloud_sql_factory.close_connectors()

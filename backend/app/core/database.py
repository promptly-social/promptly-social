"""
Database configuration and session management.
Uses SQLAlchemy with async support and connection pooling.
"""

from typing import AsyncGenerator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# Metadata for naming conventions (helpful for migrations)
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata


def get_engine_config():
    """Get engine configuration based on database URL."""
    db_url = settings.database_url_async
    is_sqlite = db_url.startswith('sqlite')

    if is_sqlite:
        return {
            "echo": settings.debug,
            "connect_args": {"check_same_thread": False}
        }
    else:
        return {
            "echo": settings.debug,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        }


def get_sync_engine_config():
    """Get sync engine configuration based on database URL."""
    db_url = settings.database_url
    is_sqlite = db_url.startswith('sqlite')

    if is_sqlite:
        return {
            "echo": settings.debug,
            "connect_args": {"check_same_thread": False}
        }
    else:
        return {
            "echo": settings.debug,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,
        }


# Async engine and session factory
async_engine = create_async_engine(
    settings.database_url_async,
    **get_engine_config()
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for migrations and other sync operations
sync_engine = create_engine(
    settings.database_url,
    **get_sync_engine_config()
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


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
    Initialize database tables.
    This is typically called during application startup.
    """
    async with async_engine.begin() as conn:
        # Import all models to ensure they are registered
        from app.models import user  # noqa: F401

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.
    This is typically called during application shutdown.
    """
    await async_engine.dispose()

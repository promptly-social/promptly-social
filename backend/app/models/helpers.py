from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.core.config import settings


def get_json_column():
    """Get JSON column type that works with both PostgreSQL and SQLite."""
    if settings.database_url.startswith("sqlite"):
        return JSON
    else:
        return JSONB


def get_array_column(item_type):
    """Get Array column type that works with both PostgreSQL and SQLite."""
    if settings.database_url.startswith("sqlite"):
        # For SQLite, we'll store arrays as JSON
        return JSON
    else:
        return ARRAY(item_type)


def get_uuid_column():
    """Get UUID column type that works with both PostgreSQL and SQLite."""
    if settings.database_url.startswith("sqlite"):
        # For SQLite, use String to store UUID as string
        return String(36)
    else:
        return UUID(as_uuid=True)

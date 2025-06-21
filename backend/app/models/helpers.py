from sqlalchemy import JSON, String, TypeDecorator
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
import uuid

from app.core.config import settings


class UUIDType(TypeDecorator):
    """
    A SQLAlchemy TypeDecorator for handling UUIDs.

    Stores UUIDs as strings in SQLite and as native UUID types in PostgreSQL.
    Ensures that UUID objects can be used consistently across the application,
    while abstracting the underlying database storage details.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            return value


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
    return UUIDType()

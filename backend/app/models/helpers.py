"""
Common database type helpers for cross-database compatibility.
"""

import json
from uuid import UUID

from sqlalchemy import JSON, String, Text, VARCHAR
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PostgreSQLUUID
from sqlalchemy.types import TypeDecorator


class StringArray(TypeDecorator):
    """
    Custom type for storing arrays as JSON strings in SQLite
    and as arrays in PostgreSQL.
    """

    impl = VARCHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        else:
            return dialect.type_descriptor(VARCHAR)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        else:
            # For SQLite, store as JSON string
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        if dialect.name == "postgresql":
            return value if value else []
        else:
            # For SQLite, parse JSON string
            try:
                return json.loads(value) if value else []
            except (json.JSONDecodeError, TypeError):
                return []


class JSONType(TypeDecorator):
    """
    Custom JSON type that works with both PostgreSQL and SQLite.
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB)
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # PostgreSQL handles JSON serialization
        else:
            # For SQLite, ensure it's serialized
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value  # PostgreSQL handles JSON deserialization
        else:
            # For SQLite, parse JSON if it's a string
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return value


class UUIDType(TypeDecorator):
    """
    Custom UUID type that works with both PostgreSQL and SQLite.
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        else:
            return str(value) if value else None

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        else:
            return UUID(value) if value else None

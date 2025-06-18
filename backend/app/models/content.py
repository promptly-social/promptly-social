"""
Content-related database models.
"""

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid

from app.core.database import Base
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


class ContentIdea(Base):
    """Model for content_ideas table."""

    __tablename__ = "content_ideas"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    title = Column(Text, nullable=False)
    original_input = Column(Text)
    generated_outline = Column(get_json_column())
    content_type = Column(String, nullable=False)
    status = Column(String, default="draft")
    scheduled_date = Column(DateTime(timezone=True))
    published_date = Column(DateTime(timezone=True))
    publication_error = Column(Text)
    linkedin_post_id = Column(String)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ImportedContent(Base):
    """Model for imported_content table."""

    __tablename__ = "imported_content"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    platform = Column(String, nullable=False)
    title = Column(Text)
    content = Column(Text, nullable=False)
    published_date = Column(DateTime(timezone=True))
    source_url = Column(Text)
    content_metadata = Column(get_json_column())
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class WritingStyleAnalysis(Base):
    """Model for writing_style_analysis table."""

    __tablename__ = "writing_style_analysis"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    platform = Column(String, nullable=False)
    analysis_data = Column(get_json_column(), nullable=False)
    content_count = Column(Integer, default=0, nullable=False)
    last_analyzed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SocialConnection(Base):
    """Model for social_connections table."""

    __tablename__ = "social_connections"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    platform = Column(String, nullable=False)
    platform_username = Column(String)
    connection_data = Column(get_json_column())
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserPreferences(Base):
    """Model for user_preferences table."""

    __tablename__ = "user_preferences"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False, unique=True)
    topics_of_interest = Column(get_array_column(String), default=[])
    websites = Column(get_array_column(String), default=[])
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ScrapedContent(Base):
    """Model for scraped_content table."""

    __tablename__ = "scraped_content"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(Text)
    content = Column(Text, nullable=False)
    topics = Column(get_array_column(String), default=[])
    scraped_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SuggestedPost(Base):
    """Model for suggested_posts table."""

    __tablename__ = "suggested_posts"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    content_idea_id = Column(get_uuid_column(), ForeignKey("content_ideas.id"))
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    platform = Column(String, nullable=False)
    topics = Column(get_array_column(String), default=[])
    confidence_score = Column(Integer, default=0)
    generated_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

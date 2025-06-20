"""
Content-related database models.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.helpers import get_array_column, get_json_column, get_uuid_column


class Content(Base):
    """Model for contents table."""

    __tablename__ = "contents"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    title = Column(Text, nullable=False)
    original_input = Column(Text)
    generated_outline = Column(get_json_column())
    content_type = Column(String, nullable=False)
    status = Column(String, default="draft")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to publications
    publications = relationship(
        "Publication", back_populates="content", cascade="all, delete-orphan"
    )


class Publication(Base):
    """Model for publications table."""

    __tablename__ = "publications"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(get_uuid_column(), ForeignKey("contents.id"), nullable=False)
    platform = Column(String, nullable=False)
    post_id = Column(String)  # Platform-specific post ID
    scheduled_date = Column(DateTime(timezone=True))
    published_date = Column(DateTime(timezone=True))
    publication_error = Column(Text)
    status = Column(
        String, default="pending"
    )  # pending, scheduled, published, canceled, error
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship to content
    content = relationship("Content", back_populates="publications")


class SuggestedPost(Base):
    """Model for suggested_posts table."""

    __tablename__ = "suggested_posts"

    id = Column(get_uuid_column(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(get_uuid_column(), nullable=False)
    content_id = Column(
        get_uuid_column(), ForeignKey("contents.id")
    )  # Updated foreign key
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

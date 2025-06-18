from sqlalchemy import Column, String, DateTime, func, Boolean, Integer
import uuid

from app.core.database import Base
from app.models.helpers import get_uuid_column, get_array_column, get_json_column


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

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.core.database import Base
from app.models.helpers import get_array_column, get_json_column, get_uuid_column


class UserPreferences(Base):
    """Model for user_preferences table."""

    __tablename__ = "user_preferences"

    id = Column(get_uuid_column(), primary_key=True, default=uuid.uuid4)
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
    bio = Column(String, default="")


class WritingStyleAnalysis(Base):
    """Model for writing_style_analysis table."""

    __tablename__ = "writing_style_analysis"

    id = Column(get_uuid_column(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_column(), nullable=False)
    # Source of the writing sample (e.g. "import", "substack", "linkedin")
    source = Column(String, nullable=False)
    analysis_data = Column(String, nullable=False)
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

    id = Column(get_uuid_column(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_column(), nullable=False)
    platform = Column(String, nullable=False)
    platform_username = Column(String)
    # All authentication data is now stored in connection_data JSON field
    # Structure varies by auth method:
    # - Native LinkedIn: {"auth_method": "native", "access_token": "...", "refresh_token": "...", "expires_at": "...", "scope": "...", "linkedin_user_id": "...", "email": "..."}
    # - Unipile: {"auth_method": "unipile", "account_id": "...", "unipile_account_id": "...", "provider": "...", "status": "..."}
    connection_data = Column(get_json_column())
    is_active = Column(Boolean, default=True, nullable=False)
    analysis_started_at = Column(DateTime(timezone=True))
    analysis_completed_at = Column(DateTime(timezone=True))
    analysis_status = Column(String, default="not_started", nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

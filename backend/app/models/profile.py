"""
Profile models for user preferences and social connections.
"""

from datetime import datetime, time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.helpers import JSONType, StringArray, UUIDType


class UserPreferences(Base):
    """Model for user_preferences table."""

    __tablename__ = "user_preferences"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    topics_of_interest: Mapped[List[str]] = mapped_column(StringArray(), default=list)
    websites: Mapped[List[str]] = mapped_column(StringArray(), default=list)
    substacks: Mapped[List[str]] = mapped_column(StringArray(), default=list)
    bio: Mapped[str] = mapped_column(String, default="")
    preferred_posting_time: Mapped[Optional[time]] = mapped_column(
        Time(timezone=False), nullable=True
    )
    timezone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    image_generation_style: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WritingStyleAnalysis(Base):
    """Model for writing_style_analysis table."""

    __tablename__ = "writing_style_analysis"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    analysis_data: Mapped[str] = mapped_column(String, nullable=False)
    # Additional fields from migration
    content_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SocialConnection(Base):
    """Model for social_connections table."""

    __tablename__ = "social_connections"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[str] = mapped_column(String, nullable=False)
    platform_username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # All authentication data is now stored in connection_data JSON field
    # Structure varies by auth method:
    # - Native LinkedIn: {"auth_method": "native", "access_token": "...", "refresh_token": "...", "expires_at": "...", "scope": "...", "linkedin_user_id": "...", "email": "..."}
    connection_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONType(), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    analysis_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    analysis_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    analysis_status: Mapped[str] = mapped_column(
        String, default="not_started", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

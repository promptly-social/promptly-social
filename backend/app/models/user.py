"""
User models for authentication and user management.
Includes User and UserSession models with audit logging and soft deletes.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.helpers import get_uuid_column


class User(Base):
    """
    User model for authentication and profile management.

    Features:
    - Supabase integration for authentication
    - Audit logging with created/updated timestamps
    - Soft deletes with deleted_at
    - Profile information and preferences
    - Session tracking capability
    """

    __tablename__ = "users"

    # Primary key with UUID support for both PostgreSQL and SQLite
    id: Mapped[str] = mapped_column(
        get_uuid_column(),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    # Supabase integration
    supabase_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # Profile information
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # User preferences
    preferred_language: Mapped[str] = mapped_column(
        String(10), default="en", nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)

    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Login tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit logging
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )

    @hybrid_property
    def is_deleted(self) -> bool:
        """Check if user is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Soft delete the user by setting deleted_at timestamp."""
        self.deleted_at = datetime.now(timezone.utc)
        self.is_active = False

    def restore(self) -> None:
        """Restore a soft deleted user."""
        self.deleted_at = None
        self.is_active = True

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class UserSession(Base):
    """
    User session model for tracking authentication sessions.

    Features:
    - Session token management
    - Device and location tracking
    - Automatic expiration
    - Revocation capability
    """

    __tablename__ = "user_sessions"

    # Primary key
    id: Mapped[str] = mapped_column(
        get_uuid_column(),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        get_uuid_column(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session information
    session_token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    device_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Audit logging
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @hybrid_property
    def is_revoked(self) -> bool:
        """Check if session is revoked."""
        return self.revoked_at is not None

    @hybrid_property
    def is_valid(self) -> bool:
        """Check if session is valid (not expired, not revoked, and active)."""
        return self.is_active and not self.is_expired and not self.is_revoked

    def revoke(self) -> None:
        """Revoke the session."""
        self.revoked_at = datetime.now(timezone.utc)
        self.is_active = False

    def extend_expiration(self, new_expiration: datetime) -> None:
        """Extend session expiration."""
        self.expires_at = new_expiration
        self.last_used_at = datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_valid={self.is_valid})>"

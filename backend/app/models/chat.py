"""
Chat models for conversation and message management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as UUIDType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.helpers import JSONType


class Conversation(Base):
    """Model for conversations table."""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    idea_bank_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(), ForeignKey("idea_banks.id", ondelete="SET NULL"), nullable=True
    )
    post_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(), ForeignKey("posts.id", ondelete="SET NULL"), nullable=True
    )
    conversation_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "post_generation", etc.
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType(), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )  # "active", "completed", "cancelled"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """Model for messages table."""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        UUIDType(), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "user", "assistant", "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[str] = mapped_column(
        String(20), default="text", nullable=False
    )  # "text", "voice", "system"
    message_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONType(), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

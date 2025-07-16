"""
Posts model for storing generated posts.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.helpers import StringArray, UUIDType


class Post(Base):
    """Model for posts table."""

    __tablename__ = "posts"

    id: Mapped[UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(UUIDType(), nullable=False)
    idea_bank_id: Mapped[Optional[UUID]] = mapped_column(UUIDType(), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False, default="linkedin"
    )
    topics: Mapped[List[str]] = mapped_column(StringArray(), default=list)
    status: Mapped[str] = mapped_column(String(20), default="suggested")
    user_feedback: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    feedback_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduler_job_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_post_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sharing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    article_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_article_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    media: Mapped[List["PostMedia"]] = relationship(
        "PostMedia", back_populates="post", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Post {self.id}: {self.title[:50] if self.title else self.content[:50]}>"
        )


class PostMedia(Base):
    """Model for post_media table."""

    __tablename__ = "post_media"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(), nullable=False
    )  # For easier access control
    media_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # image, video
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gcs_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linkedin_asset_urn: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    post: Mapped["Post"] = relationship("Post", back_populates="media")

    def __repr__(self) -> str:
        return f"<PostMedia {self.id} for Post {self.post_id}>"

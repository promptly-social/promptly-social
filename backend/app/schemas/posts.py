"""
Posts related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
    """Base schema for posts."""

    title: Optional[str] = None
    content: str
    platform: str = Field(default="linkedin")
    topics: List[str] = Field(default_factory=list)
    recommendation_score: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="suggested")
    scheduled_at: Optional[datetime] = None


class PostCreate(PostBase):
    """Schema for creating posts."""

    idea_bank_id: Optional[UUID] = None


class PostUpdate(BaseModel):
    """Schema for updating posts."""

    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    topics: Optional[List[str]] = None
    recommendation_score: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class PostFeedback(BaseModel):
    """Schema for post feedback."""

    feedback_type: str = Field(..., pattern="^(positive|negative)$")
    comment: Optional[str] = None


class PostResponse(PostBase):
    """Schema for post responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    idea_bank_id: Optional[UUID] = None
    user_feedback: Optional[str] = None
    feedback_comment: Optional[str] = None
    feedback_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    """Schema for paginated posts list."""

    items: List[PostResponse]
    total: int
    page: int
    size: int
    has_next: bool

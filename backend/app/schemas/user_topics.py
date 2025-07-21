"""
User Topics schemas for API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class UserTopicBase(BaseModel):
    """Base schema for user topics."""

    topic: str = Field(..., min_length=1, max_length=100, description="Topic name")
    color: Optional[str] = Field(
        None, pattern=r"^#[0-9a-fA-F]{6}$", description="RGB hex color"
    )


class UserTopicCreate(UserTopicBase):
    """Schema for creating a new user topic."""

    pass


class UserTopicUpdate(BaseModel):
    """Schema for updating a user topic."""

    topic: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Topic name"
    )
    color: Optional[str] = Field(
        None, pattern=r"^#[0-9a-fA-F]{6}$", description="RGB hex color"
    )


class UserTopicResponse(UserTopicBase):
    """Schema for user topic response."""

    id: UUID
    user_id: UUID
    color: str  # Always present in response
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserTopicsListResponse(BaseModel):
    """Schema for list of user topics response."""

    topics: List[UserTopicResponse]
    total: int


class BulkTopicCreateRequest(BaseModel):
    """Schema for bulk creating topics from post topics."""

    topics: List[str] = Field(..., description="List of topic names to create")


class TopicColorMap(BaseModel):
    """Schema for topic-color mapping."""

    topic: str
    color: str


class TopicColorsResponse(BaseModel):
    """Schema for topic colors response."""

    topic_colors: List[TopicColorMap]

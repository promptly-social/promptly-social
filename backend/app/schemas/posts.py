"""
Posts related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel, Field, UUID4


class PostMediaBase(BaseModel):
    """Base schema for post media."""

    media_type: Optional[str] = None
    file_name: Optional[str] = None
    gcs_url: Optional[str] = None

    class Config:
        from_attributes = True


class PostMediaCreate(PostMediaBase):
    """Schema for creating post media."""

    post_id: UUID4
    user_id: UUID4
    storage_path: str


class PostMediaResponse(PostMediaBase):
    """Schema for returning post media."""

    id: UUID4
    post_id: UUID4
    user_id: UUID4
    linkedin_asset_urn: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    """Base schema for posts."""

    title: Optional[str] = None
    content: str
    platform: str = "linkedin"
    topics: Optional[List[str]] = []
    status: Optional[str] = "suggested"
    scheduled_at: Optional[datetime] = None
    idea_bank_id: Optional[UUID4] = None

    class Config:
        from_attributes = True


class PostCreate(PostBase):
    """Schema for creating a post."""

    pass


class PostUpdate(BaseModel):
    """Schema for updating a post."""

    title: Optional[str] = None
    content: Optional[str] = None
    platform: Optional[str] = None
    topics: Optional[List[str]] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    user_feedback: Optional[str] = None
    feedback_comment: Optional[str] = None
    posted_at: Optional[datetime] = None


class PostResponse(PostBase):
    """Schema for returning a post."""

    id: UUID4
    user_id: UUID4
    idea_bank_id: Optional[UUID4] = None
    media: List[PostMediaResponse] = []
    user_feedback: Optional[str] = None
    feedback_comment: Optional[str] = None
    feedback_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostFeedback(BaseModel):
    """Schema for post feedback."""

    feedback_type: str = Field(..., pattern="^(positive|negative)$")
    comment: Optional[str] = None


class PostListResponse(BaseModel):
    """Schema for a list of posts with pagination info."""

    items: List[PostResponse]
    total: int
    page: int
    size: int
    total_pages: int


class PostBatchUpdate(BaseModel):
    posts: list[dict[str, Any]]


class PostCountsResponse(BaseModel):
    """Schema for returning counts of posts by status categories."""

    drafts: int = 0
    scheduled: int = 0
    posted: int = 0

    class Config:
        from_attributes = True

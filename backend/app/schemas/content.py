"""
Content-related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ContentBase(BaseModel):
    """Base schema for content."""

    title: str
    original_input: Optional[str] = None
    content_type: str
    status: Optional[str] = "draft"


class ContentCreate(ContentBase):
    """Schema for creating content."""

    generated_outline: Optional[Dict[str, Any]] = None


class ContentUpdate(BaseModel):
    """Schema for updating content."""

    title: Optional[str] = None
    status: Optional[str] = None
    generated_outline: Optional[Dict[str, Any]] = None


class ContentResponse(ContentBase):
    """Schema for content responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    generated_outline: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    publications: Optional[List["PublicationResponse"]] = None


class ContentListResponse(BaseModel):
    """Schema for paginated content list."""

    items: List[ContentResponse]
    total: int
    page: int
    size: int
    has_next: bool


class PublicationBase(BaseModel):
    """Base schema for publications."""

    platform: str
    scheduled_date: Optional[datetime] = None
    status: Optional[str] = "pending"


class PublicationCreate(PublicationBase):
    """Schema for creating publications."""

    content_id: UUID


class PublicationUpdate(BaseModel):
    """Schema for updating publications."""

    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    publication_error: Optional[str] = None
    post_id: Optional[str] = None
    status: Optional[str] = None


class PublicationResponse(PublicationBase):
    """Schema for publication responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content_id: UUID
    post_id: Optional[str] = None
    published_date: Optional[datetime] = None
    publication_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

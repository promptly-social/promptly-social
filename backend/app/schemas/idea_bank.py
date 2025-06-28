"""
Idea Bank related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class IdeaBankData(BaseModel):
    """Schema for idea bank data structure."""

    type: str  # "article" or "text"
    value: str
    title: Optional[str] = None
    time_sensitive: Optional[bool] = False
    last_used_post_id: Optional[str] = None
    ai_suggested: Optional[bool] = False


class IdeaBankBase(BaseModel):
    """Base schema for idea bank."""

    data: Dict[str, Any]


class IdeaBankCreate(IdeaBankBase):
    """Schema for creating idea bank."""

    pass


class IdeaBankUpdate(BaseModel):
    """Schema for updating idea bank."""

    data: Optional[Dict[str, Any]] = None


class IdeaBankResponse(IdeaBankBase):
    """Schema for idea bank responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class IdeaBankListResponse(BaseModel):
    """Schema for paginated idea bank list."""

    items: List[IdeaBankResponse]
    total: int
    page: int
    size: int
    has_next: bool

"""
Idea Bank related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class IdeaBankData(BaseModel):
    """Schema for idea bank data structure."""

    type: str  # "url", "text", or "product"
    value: str  # URL for article/product, text content for text type
    title: Optional[str] = None
    # Product-specific fields
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    # Common fields
    time_sensitive: Optional[bool] = False
    last_used_post_id: Optional[str] = None
    ai_suggested: Optional[bool] = False

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ["url", "text", "product"]:
            raise ValueError("type must be one of: url, text, product")
        return v


class IdeaBankBase(BaseModel):
    """Base schema for idea bank."""

    data: IdeaBankData


class IdeaBankCreate(IdeaBankBase):
    """Schema for creating idea bank."""

    pass


class IdeaBankUpdate(BaseModel):
    """Schema for updating idea bank."""

    data: Optional[IdeaBankData] = None


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

"""
Content Strategies related Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContentStrategyBase(BaseModel):
    """Base schema for content strategies."""

    platform: str = Field(..., description="Platform for the content strategy")
    strategy: str = Field(..., description="Content strategy description")


class ContentStrategyCreate(ContentStrategyBase):
    """Schema for creating content strategies."""

    pass


class ContentStrategyUpdate(BaseModel):
    """Schema for updating content strategies."""

    platform: Optional[str] = Field(
        None, description="Platform for the content strategy"
    )
    strategy: Optional[str] = Field(None, description="Content strategy description")


class ContentStrategyResponse(ContentStrategyBase):
    """Schema for content strategy responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class ContentStrategyListResponse(BaseModel):
    """Schema for paginated content strategies list."""

    items: list[ContentStrategyResponse]
    total: int
    page: int
    size: int
    has_next: bool

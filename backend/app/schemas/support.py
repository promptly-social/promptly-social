"""
Support request schemas.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SupportRequestCreate(BaseModel):
    """Schema for creating a support request."""

    type: Literal["bug", "feature request", "other"] = Field(
        ..., description="Type of support request"
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Description of the issue or request",
    )


class SupportRequestResponse(BaseModel):
    """Schema for support request response."""

    id: UUID
    user_id: UUID
    type: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

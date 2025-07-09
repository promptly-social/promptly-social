"""
DailySuggestionSchedule related Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DailySuggestionScheduleBase(BaseModel):
    """Base schema for daily suggestion schedule."""

    cron_expression: str = Field(
        ...,
        min_length=1,
        description="Cron expression in Cloud Scheduler format (e.g., '0 9 * * *').",
    )
    timezone: str = Field(default="UTC", description="IANA timezone identifier.")


class DailySuggestionScheduleCreate(DailySuggestionScheduleBase):
    """Schema for creating schedule."""

    pass


class DailySuggestionScheduleUpdate(BaseModel):
    """Schema for updating schedule."""

    cron_expression: str | None = Field(
        None,
        min_length=1,
        description="Cron expression in Cloud Scheduler format.",
    )
    timezone: str | None = Field(None, description="IANA timezone identifier")


class DailySuggestionScheduleResponse(DailySuggestionScheduleBase):
    """Response schema for schedule."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

"""
DailySuggestionSchedule model for user-specific daily suggestion generation schedules.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.helpers import UUIDType


class DailySuggestionSchedule(Base):
    """Model for daily_suggestion_schedules table."""

    __tablename__ = "daily_suggestion_schedules"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDType(), nullable=False, unique=True)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    last_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<DailySuggestionSchedule {self.id} for user {self.user_id} - {self.cron_expression} ({self.timezone})>"

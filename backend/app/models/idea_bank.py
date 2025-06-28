"""
Idea Bank related database models.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.helpers import JSONType, UUIDType


class IdeaBank(Base):
    """Model for idea_banks table."""

    __tablename__ = "idea_banks"

    id: Mapped[UUID] = mapped_column(UUIDType(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id"), nullable=False
    )
    data: Mapped[Dict[str, Any]] = mapped_column(
        JSONType(), nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

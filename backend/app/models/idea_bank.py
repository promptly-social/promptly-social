"""
Idea Bank related database models.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.helpers import get_json_column, get_uuid_column


class IdeaBank(Base):
    """Model for idea_banks table."""

    __tablename__ = "idea_banks"

    id = Column(get_uuid_column(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_column(), ForeignKey("users.id"), nullable=False)
    data = Column(get_json_column(), nullable=False, default={})
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

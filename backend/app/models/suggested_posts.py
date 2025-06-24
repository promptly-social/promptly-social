"""
Suggested Posts SQLAlchemy model.
"""

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from app.core.database import Base
from app.models.helpers import get_array_column, get_uuid_column


class SuggestedPost(Base):
    """Model for suggested_posts table."""

    __tablename__ = "suggested_posts"

    id = Column(get_uuid_column(), primary_key=True, default=uuid.uuid4)
    user_id = Column(get_uuid_column(), ForeignKey("users.id"), nullable=False)
    idea_bank_id = Column(get_uuid_column(), ForeignKey("idea_banks.id"), nullable=True)
    title = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    platform = Column(String, nullable=False, default="linkedin")
    topics = Column(get_array_column(String), default=[])
    recommendation_score = Column(Integer, default=0)
    status = Column(String, default="suggested")
    # Feedback fields
    user_feedback = Column(String, nullable=True)  # 'positive', 'negative', null
    feedback_comment = Column(Text, nullable=True)  # Optional feedback text
    feedback_at = Column(
        DateTime(timezone=True), nullable=True
    )  # When feedback was given
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

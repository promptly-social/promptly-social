"""
User Topics model for storing user-specific topics with colors.
"""

import random
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.helpers import UUIDType


class UserTopic(Base):
    """Model for user_topics table to store topics with assigned colors."""

    __tablename__ = "user_topics"

    id: Mapped[UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # RGB hex color
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<UserTopic {self.id}: {self.topic} ({self.color})>"

    @staticmethod
    def generate_random_color() -> str:
        """Generate a random RGB hex color."""
        return f"#{random.randint(0, 255):02x}{random.randint(0, 255):02x}{random.randint(0, 255):02x}"

    @classmethod
    def create_with_random_color(cls, user_id: UUID, topic: str) -> "UserTopic":
        """Create a new UserTopic with a randomly generated color."""
        return cls(user_id=user_id, topic=topic, color=cls.generate_random_color())

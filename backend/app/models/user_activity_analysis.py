"""
User activity analysis models for tracking analysis state and progress.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.helpers import JSONType, UUIDType
from app.models.user import User


class UserAnalysisTracking(Base):
    """
    Model for tracking user activity analysis state and progress.

    This model tracks when analysis was last performed for each user,
    what content was included in the analysis, and provides utilities
    for determining what new content needs to be analyzed.

    Features:
    - Tracks last analysis timestamp for incremental processing
    - Records scope of analysis (posts, messages analyzed)
    - Provides hybrid properties for state management
    - Supports efficient querying for new content detection
    """

    __tablename__ = "user_analysis_tracking"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUIDType(),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )

    # Foreign key to user (unique constraint ensures one record per user)
    user_id: Mapped[UUID] = mapped_column(
        UUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Analysis timestamps
    last_analysis_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Content tracking for incremental analysis
    last_analyzed_post_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(),
        nullable=True,
    )

    last_analyzed_message_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(),
        nullable=True,
    )

    # Analysis scope tracking (JSON structure defined in design document)
    analysis_scope: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONType(),
        nullable=True,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")

    @hybrid_property
    def has_been_analyzed(self) -> bool:
        """Check if user has ever been analyzed."""
        return self.last_analysis_at is not None

    @hybrid_property
    def needs_analysis(self) -> bool:
        """
        Check if user needs analysis based on timestamp.
        This is a basic check - actual threshold checking is done in the service layer.
        """
        return self.last_analysis_at is None

    def get_posts_analyzed_count(self) -> int:
        """Get the total number of posts analyzed in the last analysis."""
        if not self.analysis_scope or "posts_analyzed" not in self.analysis_scope:
            return 0

        posts_data = self.analysis_scope["posts_analyzed"]
        return posts_data.get("scheduled_count", 0) + posts_data.get(
            "dismissed_count", 0
        )

    def get_messages_analyzed_count(self) -> int:
        """Get the total number of messages analyzed in the last analysis."""
        if not self.analysis_scope or "messages_analyzed" not in self.analysis_scope:
            return 0

        return self.analysis_scope["messages_analyzed"].get("total_count", 0)

    def get_analysis_types_performed(self) -> list[str]:
        """Get the list of analysis types performed in the last analysis."""
        if (
            not self.analysis_scope
            or "analysis_types_performed" not in self.analysis_scope
        ):
            return []

        return self.analysis_scope["analysis_types_performed"]

    def update_analysis_completion(
        self,
        analysis_timestamp: datetime,
        posts_analyzed: Dict[str, Any],
        messages_analyzed: Dict[str, Any],
        analysis_types: list[str],
        last_post_id: Optional[UUID] = None,
        last_message_id: Optional[UUID] = None,
    ) -> None:
        """
        Update the tracking record after successful analysis completion.

        Args:
            analysis_timestamp: When the analysis was completed
            posts_analyzed: Dictionary with post analysis details
            messages_analyzed: Dictionary with message analysis details
            analysis_types: List of analysis types performed
            last_post_id: ID of the last post analyzed (for incremental processing)
            last_message_id: ID of the last message analyzed (for incremental processing)
        """
        self.last_analysis_at = analysis_timestamp
        self.last_analyzed_post_id = last_post_id
        self.last_analyzed_message_id = last_message_id

        self.analysis_scope = {
            "posts_analyzed": posts_analyzed,
            "messages_analyzed": messages_analyzed,
            "analysis_types_performed": analysis_types,
        }

    def __repr__(self) -> str:
        return (
            f"<UserAnalysisTracking("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"last_analysis_at={self.last_analysis_at}, "
            f"has_been_analyzed={self.has_been_analyzed}"
            f")>"
        )

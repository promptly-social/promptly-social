"""create_user_activity_analysis_tracking

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2025-01-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "i9d0e1f2g3h4"
down_revision: Union[str, None] = "h8c9d0e1f2g3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_analysis_tracking table
    op.create_table(
        "user_analysis_tracking",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "last_analysis_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_analyzed_post_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "last_analyzed_message_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "analysis_scope",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Create indexes for user_analysis_tracking table
    op.create_index(
        "idx_user_analysis_tracking_user_id",
        "user_analysis_tracking",
        ["user_id"],
    )
    op.create_index(
        "idx_user_analysis_tracking_last_analysis",
        "user_analysis_tracking",
        ["last_analysis_at"],
    )

    # Add negative_analysis column to user_preferences table
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [
        col["name"] for col in inspector.get_columns("user_preferences")
    ]

    if "negative_analysis" not in existing_columns:
        op.add_column(
            "user_preferences",
            sa.Column("negative_analysis", sa.Text(), nullable=True),
        )

    # Create performance indexes on existing tables for efficient querying

    # Index for posts table - user_id, created_at, status for efficient activity queries
    try:
        op.create_index(
            "idx_posts_user_created_status",
            "posts",
            ["user_id", "created_at", "status"],
        )
    except Exception:
        # Index might already exist, continue
        pass

    # Index for messages table - conversation_id, created_at for efficient message counting
    try:
        op.create_index(
            "idx_messages_conversation_created",
            "messages",
            ["conversation_id", "created_at"],
        )
    except Exception:
        # Index might already exist, continue
        pass

    # Index for conversations table - user_id, idea_bank_id, created_at for efficient conversation queries
    try:
        op.create_index(
            "idx_conversations_user_idea_created",
            "conversations",
            ["user_id", "idea_bank_id", "created_at"],
        )
    except Exception:
        # Index might already exist, continue
        pass

    # Index for posts table - user_id, feedback_at for dismissed posts analysis
    try:
        op.create_index(
            "idx_posts_user_feedback_at",
            "posts",
            ["user_id", "feedback_at"],
        )
    except Exception:
        # Index might already exist, continue
        pass

    # Index for posts table - user_id, scheduled_at for scheduled posts analysis
    try:
        op.create_index(
            "idx_posts_user_scheduled_at",
            "posts",
            ["user_id", "scheduled_at"],
        )
    except Exception:
        # Index might already exist, continue
        pass


def downgrade() -> None:
    # Drop performance indexes
    try:
        op.drop_index("idx_posts_user_scheduled_at", "posts")
    except Exception:
        pass

    try:
        op.drop_index("idx_posts_user_feedback_at", "posts")
    except Exception:
        pass

    try:
        op.drop_index("idx_conversations_user_idea_created", "conversations")
    except Exception:
        pass

    try:
        op.drop_index("idx_messages_conversation_created", "messages")
    except Exception:
        pass

    try:
        op.drop_index("idx_posts_user_created_status", "posts")
    except Exception:
        pass

    # Drop negative_analysis column from user_preferences
    op.drop_column("user_preferences", "negative_analysis")

    # Drop user_analysis_tracking table indexes
    op.drop_index("idx_user_analysis_tracking_last_analysis", "user_analysis_tracking")
    op.drop_index("idx_user_analysis_tracking_user_id", "user_analysis_tracking")

    # Drop user_analysis_tracking table
    op.drop_table("user_analysis_tracking")

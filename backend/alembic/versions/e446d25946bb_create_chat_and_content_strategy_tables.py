"""create_chat_and_content_strategy_tables

Revision ID: e446d25946bb
Revises: 2febca08b852
Create Date: 2025-07-18 10:12:47.797634

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e446d25946bb"
down_revision: Union[str, None] = "2febca08b852"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("idea_bank_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "conversation_type",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'post_generation'"),
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status", sa.String(50), nullable=False, server_default=sa.text("'active'")
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["idea_bank_id"], ["idea_banks.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'cancelled')",
            name="conversations_status_check",
        ),
    )

    # Create indexes for conversations table
    op.create_index("idx_conversations_user_id", "conversations", ["user_id"])
    op.create_index("idx_conversations_idea_bank_id", "conversations", ["idea_bank_id"])
    op.create_index("idx_conversations_status", "conversations", ["status"])
    op.create_index("idx_conversations_created_at", "conversations", ["created_at"])

    # Create update trigger for conversations
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_conversations_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER conversations_updated_at_trigger
            BEFORE UPDATE ON conversations
            FOR EACH ROW
            EXECUTE FUNCTION update_conversations_updated_at();
    """
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "message_type",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'text'"),
        ),
        sa.Column(
            "message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')",
            name="messages_role_check",
        ),
        sa.CheckConstraint(
            "message_type IN ('text', 'voice', 'system')",
            name="messages_message_type_check",
        ),
    )

    # Create indexes for messages table
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("idx_messages_role", "messages", ["role"])
    op.create_index("idx_messages_created_at", "messages", ["created_at"])

    # Create content_strategies table
    op.create_table(
        "content_strategies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id", "platform", name="content_strategies_user_platform_unique"
        ),
    )

    # Create indexes for content_strategies table
    op.create_index("idx_content_strategies_user_id", "content_strategies", ["user_id"])
    op.create_index(
        "idx_content_strategies_platform", "content_strategies", ["platform"]
    )

    # Create trigger for content_strategies updated_at
    op.execute(
        """
        CREATE TRIGGER trigger_update_content_strategies_updated_at
            BEFORE UPDATE ON content_strategies
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """
    )

    # Create daily_suggestion_schedules table
    op.create_table(
        "daily_suggestion_schedules",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cron_expression", sa.Text(), nullable=False),
        sa.Column(
            "timezone", sa.Text(), nullable=False, server_default=sa.text("'UTC'")
        ),
        sa.Column("last_run_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="daily_suggestion_schedules_user_unique"),
        sa.CheckConstraint(
            "cron_expression <> ''", name="daily_suggestion_schedules_cron_check"
        ),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("daily_suggestion_schedules")

    # Drop triggers and functions
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_content_strategies_updated_at ON content_strategies;"
    )
    op.drop_index("idx_content_strategies_platform", table_name="content_strategies")
    op.drop_index("idx_content_strategies_user_id", table_name="content_strategies")
    op.drop_table("content_strategies")

    op.drop_index("idx_messages_created_at", table_name="messages")
    op.drop_index("idx_messages_role", table_name="messages")
    op.drop_index("idx_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.execute(
        "DROP TRIGGER IF EXISTS conversations_updated_at_trigger ON conversations;"
    )
    op.execute("DROP FUNCTION IF EXISTS update_conversations_updated_at();")
    op.drop_index("idx_conversations_created_at", table_name="conversations")
    op.drop_index("idx_conversations_status", table_name="conversations")
    op.drop_index("idx_conversations_idea_bank_id", table_name="conversations")
    op.drop_index("idx_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")

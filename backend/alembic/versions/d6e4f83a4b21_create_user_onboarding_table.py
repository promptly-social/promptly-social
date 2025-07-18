"""create_user_onboarding_table

Revision ID: d6e4f83a4b21
Revises: e446d25946bb
Create Date: 2025-07-18 10:14:06.951721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d6e4f83a4b21"
down_revision: Union[str, None] = "e446d25946bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_onboarding table
    op.create_table(
        "user_onboarding",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Onboarding status
        sa.Column(
            "is_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_skipped", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        # Individual step completion tracking
        sa.Column(
            "step_profile_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "step_content_preferences_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "step_settings_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "step_my_posts_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "step_content_ideas_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "step_posting_schedule_completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        # Current step tracking (1-6 for the 6 steps)
        sa.Column(
            "current_step", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
        # Optional notes or feedback from user
        sa.Column("notes", sa.Text(), nullable=True),
        # Audit logging
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("skipped_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    # Create indexes for user_onboarding table
    op.create_index("idx_user_onboarding_user_id", "user_onboarding", ["user_id"])
    op.create_index(
        "idx_user_onboarding_status", "user_onboarding", ["is_completed", "is_skipped"]
    )

    # Create trigger function for updating updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_user_onboarding_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    # Create trigger for user_onboarding updated_at
    op.execute(
        """
        CREATE TRIGGER trigger_update_user_onboarding_updated_at
            BEFORE UPDATE ON user_onboarding
            FOR EACH ROW
            EXECUTE FUNCTION update_user_onboarding_updated_at();
    """
    )


def downgrade() -> None:
    # Drop trigger and function
    op.execute(
        "DROP TRIGGER IF EXISTS trigger_update_user_onboarding_updated_at ON user_onboarding;"
    )
    op.execute("DROP FUNCTION IF EXISTS update_user_onboarding_updated_at();")

    # Drop indexes
    op.drop_index("idx_user_onboarding_status", table_name="user_onboarding")
    op.drop_index("idx_user_onboarding_user_id", table_name="user_onboarding")

    # Drop table
    op.drop_table("user_onboarding")

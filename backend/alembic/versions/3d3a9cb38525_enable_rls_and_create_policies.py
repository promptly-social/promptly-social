"""enable_rls_and_create_policies

Revision ID: 3d3a9cb38525
Revises: d6e4f83a4b21
Create Date: 2025-07-18 10:21:33.148147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3d3a9cb38525"
down_revision: Union[str, None] = "d6e4f83a4b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable RLS and create policies for all tables."""

    # Create the user context function that RLS policies will use
    op.execute(
        """
        CREATE OR REPLACE FUNCTION current_app_user()
        RETURNS UUID AS $$
        BEGIN
            RETURN current_setting('app.current_user_id', true)::UUID;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    )

    # Enable RLS on all tables
    tables_with_rls = [
        "users",
        "user_sessions",
        "posts",
        "post_media",
        "idea_banks",
        "conversations",
        "messages",
        "content_strategies",
        "daily_suggestion_schedules",
        "user_onboarding",
    ]

    for table in tables_with_rls:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # Create RLS policies for users table
    # Note: Users table policies are more restrictive - users can only see their own record
    op.execute(
        """
        CREATE POLICY "Users can view their own record"
        ON users
        FOR SELECT
        USING (current_app_user() = id::UUID)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own record"
        ON users
        FOR UPDATE
        USING (current_app_user() = id::UUID)
    """
    )

    # Create RLS policies for user_sessions table
    op.execute(
        """
        CREATE POLICY "Users can view their own sessions"
        ON user_sessions
        FOR SELECT
        USING (current_app_user() = user_id::UUID)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own sessions"
        ON user_sessions
        FOR INSERT
        WITH CHECK (current_app_user() = user_id::UUID)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own sessions"
        ON user_sessions
        FOR UPDATE
        USING (current_app_user() = user_id::UUID)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own sessions"
        ON user_sessions
        FOR DELETE
        USING (current_app_user() = user_id::UUID)
    """
    )

    # Create RLS policies for posts table
    op.execute(
        """
        CREATE POLICY "Users can view their own posts"
        ON posts
        FOR SELECT
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own posts"
        ON posts
        FOR INSERT
        WITH CHECK (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own posts"
        ON posts
        FOR UPDATE
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own posts"
        ON posts
        FOR DELETE
        USING (current_app_user() = user_id)
    """
    )

    # Create RLS policies for post_media table
    op.execute(
        """
        CREATE POLICY "Users can view their own post media"
        ON post_media
        FOR SELECT
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own post media"
        ON post_media
        FOR INSERT
        WITH CHECK (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own post media"
        ON post_media
        FOR UPDATE
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own post media"
        ON post_media
        FOR DELETE
        USING (current_app_user() = user_id)
    """
    )

    # Create RLS policies for idea_banks table
    op.execute(
        """
        CREATE POLICY "Users can view their own idea banks"
        ON idea_banks
        FOR SELECT
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own idea banks"
        ON idea_banks
        FOR INSERT
        WITH CHECK (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own idea banks"
        ON idea_banks
        FOR UPDATE
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own idea banks"
        ON idea_banks
        FOR DELETE
        USING (current_app_user() = user_id)
    """
    )

    # Create RLS policies for conversations table
    op.execute(
        """
        CREATE POLICY "Users can manage their own conversations"
        ON conversations
        FOR ALL
        USING (current_app_user() = user_id)
        WITH CHECK (current_app_user() = user_id)
    """
    )

    # Create RLS policies for messages table (special case - checks through conversations)
    op.execute(
        """
        CREATE POLICY "Users can manage messages in their own conversations"
        ON messages
        FOR ALL
        USING (
            EXISTS (
                SELECT 1
                FROM conversations
                WHERE id = messages.conversation_id AND user_id = current_app_user()
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM conversations
                WHERE id = messages.conversation_id AND user_id = current_app_user()
            )
        )
    """
    )

    # Create RLS policies for content_strategies table
    op.execute(
        """
        CREATE POLICY "Users can view their own content strategies"
        ON content_strategies
        FOR SELECT
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own content strategies"
        ON content_strategies
        FOR INSERT
        WITH CHECK (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own content strategies"
        ON content_strategies
        FOR UPDATE
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own content strategies"
        ON content_strategies
        FOR DELETE
        USING (current_app_user() = user_id)
    """
    )

    # Create RLS policies for daily_suggestion_schedules table
    op.execute(
        """
        CREATE POLICY "Users can view their own daily suggestion schedules"
        ON daily_suggestion_schedules
        FOR SELECT
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own daily suggestion schedules"
        ON daily_suggestion_schedules
        FOR INSERT
        WITH CHECK (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own daily suggestion schedules"
        ON daily_suggestion_schedules
        FOR UPDATE
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own daily suggestion schedules"
        ON daily_suggestion_schedules
        FOR DELETE
        USING (current_app_user() = user_id)
    """
    )

    # Create RLS policies for user_onboarding table
    op.execute(
        """
        CREATE POLICY "Users can view their own onboarding"
        ON user_onboarding
        FOR SELECT
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can create their own onboarding"
        ON user_onboarding
        FOR INSERT
        WITH CHECK (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can update their own onboarding"
        ON user_onboarding
        FOR UPDATE
        USING (current_app_user() = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "Users can delete their own onboarding"
        ON user_onboarding
        FOR DELETE
        USING (current_app_user() = user_id)
    """
    )


def downgrade() -> None:
    """Disable RLS and drop policies for all tables."""

    # Drop all RLS policies
    tables_with_policies = [
        (
            "users",
            ["Users can view their own record", "Users can update their own record"],
        ),
        (
            "user_sessions",
            [
                "Users can view their own sessions",
                "Users can create their own sessions",
                "Users can update their own sessions",
                "Users can delete their own sessions",
            ],
        ),
        (
            "posts",
            [
                "Users can view their own posts",
                "Users can create their own posts",
                "Users can update their own posts",
                "Users can delete their own posts",
            ],
        ),
        (
            "post_media",
            [
                "Users can view their own post media",
                "Users can create their own post media",
                "Users can update their own post media",
                "Users can delete their own post media",
            ],
        ),
        (
            "idea_banks",
            [
                "Users can view their own idea banks",
                "Users can create their own idea banks",
                "Users can update their own idea banks",
                "Users can delete their own idea banks",
            ],
        ),
        ("conversations", ["Users can manage their own conversations"]),
        ("messages", ["Users can manage messages in their own conversations"]),
        (
            "content_strategies",
            [
                "Users can view their own content strategies",
                "Users can create their own content strategies",
                "Users can update their own content strategies",
                "Users can delete their own content strategies",
            ],
        ),
        (
            "daily_suggestion_schedules",
            [
                "Users can view their own daily suggestion schedules",
                "Users can create their own daily suggestion schedules",
                "Users can update their own daily suggestion schedules",
                "Users can delete their own daily suggestion schedules",
            ],
        ),
        (
            "user_onboarding",
            [
                "Users can view their own onboarding",
                "Users can create their own onboarding",
                "Users can update their own onboarding",
                "Users can delete their own onboarding",
            ],
        ),
    ]

    # Drop all policies
    for table, policies in tables_with_policies:
        for policy in policies:
            op.execute(f'DROP POLICY IF EXISTS "{policy}" ON {table}')

    # Disable RLS on all tables
    tables_with_rls = [
        "users",
        "user_sessions",
        "posts",
        "post_media",
        "idea_banks",
        "conversations",
        "messages",
        "content_strategies",
        "daily_suggestion_schedules",
        "user_onboarding",
    ]

    for table in tables_with_rls:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop the user context function
    op.execute("DROP FUNCTION IF EXISTS current_app_user()")

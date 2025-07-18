"""
Row-Level Security (RLS) system for PostgreSQL.
Manages RLS policies and user authentication context for database sessions.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AuthContextHandler:
    """
    Handles user authentication context for database sessions.
    Sets and manages the current user context for RLS policies.
    """

    @staticmethod
    async def set_current_user(session: AsyncSession, user_id: UUID) -> None:
        """
        Set the current user context for the database session.
        This is used by RLS policies to determine data access permissions.

        Args:
            session: Database session
            user_id: UUID of the current user
        """
        try:
            # Set the user context in PostgreSQL session
            await session.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": str(user_id)},
            )
            logger.debug(f"Set user context to {user_id}")
        except Exception as e:
            logger.error(f"Failed to set user context: {e}")
            raise

    @staticmethod
    def set_current_user_sync(session: Session, user_id: UUID) -> None:
        """
        Set the current user context for the sync database session.
        This is used by RLS policies to determine data access permissions.

        Args:
            session: Sync database session
            user_id: UUID of the current user
        """
        try:
            # Set the user context in PostgreSQL session
            session.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": str(user_id)},
            )
            logger.debug(f"Set user context to {user_id} (sync)")
        except Exception as e:
            logger.error(f"Failed to set user context (sync): {e}")
            raise

    @staticmethod
    async def get_current_user(session: AsyncSession) -> Optional[UUID]:
        """
        Get the current user context from the database session.

        Args:
            session: Database session

        Returns:
            UUID of the current user or None if not set
        """
        try:
            result = await session.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
            user_id_str = result.scalar()

            if user_id_str and user_id_str != "":
                return UUID(user_id_str)
            return None
        except Exception as e:
            logger.debug(f"No user context set or error retrieving: {e}")
            return None

    @staticmethod
    def get_current_user_sync(session: Session) -> Optional[UUID]:
        """
        Get the current user context from the sync database session.

        Args:
            session: Sync database session

        Returns:
            UUID of the current user or None if not set
        """
        try:
            result = session.execute(
                text("SELECT current_setting('app.current_user_id', true)")
            )
            user_id_str = result.scalar()

            if user_id_str and user_id_str != "":
                return UUID(user_id_str)
            return None
        except Exception as e:
            logger.debug(f"No user context set or error retrieving (sync): {e}")
            return None

    @staticmethod
    async def clear_user_context(session: AsyncSession) -> None:
        """
        Clear the user context from the database session.

        Args:
            session: Database session
        """
        try:
            await session.execute(
                text("SELECT set_config('app.current_user_id', '', true)")
            )
            logger.debug("Cleared user context")
        except Exception as e:
            logger.error(f"Failed to clear user context: {e}")
            raise

    @staticmethod
    def clear_user_context_sync(session: Session) -> None:
        """
        Clear the user context from the sync database session.

        Args:
            session: Sync database session
        """
        try:
            session.execute(text("SELECT set_config('app.current_user_id', '', true)"))
            logger.debug("Cleared user context (sync)")
        except Exception as e:
            logger.error(f"Failed to clear user context (sync): {e}")
            raise


class RLSPolicyManager:
    """
    Manages PostgreSQL Row-Level Security policies.
    Handles creation, validation, and management of RLS policies for all tables.
    """

    def __init__(self):
        self.auth_context = AuthContextHandler()

    async def create_user_context_function(self, session: AsyncSession) -> None:
        """
        Create the PostgreSQL function to get current user context.
        This function is used by RLS policies to determine the current user.

        Args:
            session: Database session
        """
        try:
            # Create the function that RLS policies will use
            await session.execute(
                text(
                    """
                CREATE OR REPLACE FUNCTION current_app_user()
                RETURNS UUID AS $
                BEGIN
                    RETURN current_setting('app.current_user_id', true)::UUID;
                EXCEPTION
                    WHEN OTHERS THEN
                        RETURN NULL;
                END;
                $ LANGUAGE plpgsql SECURITY DEFINER;
            """
                )
            )

            logger.info("Created current_app_user() function for RLS")
        except Exception as e:
            logger.error(f"Failed to create user context function: {e}")
            raise

    def create_user_context_function_sync(self, session: Session) -> None:
        """
        Create the PostgreSQL function to get current user context (sync version).

        Args:
            session: Sync database session
        """
        try:
            # Create the function that RLS policies will use
            session.execute(
                text(
                    """
                CREATE OR REPLACE FUNCTION current_app_user()
                RETURNS UUID AS $
                BEGIN
                    RETURN current_setting('app.current_user_id', true)::UUID;
                EXCEPTION
                    WHEN OTHERS THEN
                        RETURN NULL;
                END;
                $ LANGUAGE plpgsql SECURITY DEFINER;
            """
                )
            )

            logger.info("Created current_app_user() function for RLS (sync)")
        except Exception as e:
            logger.error(f"Failed to create user context function (sync): {e}")
            raise

    async def enable_rls_on_table(self, session: AsyncSession, table_name: str) -> None:
        """
        Enable Row-Level Security on a specific table.

        Args:
            session: Database session
            table_name: Name of the table to enable RLS on
        """
        try:
            await session.execute(
                text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
            )
            logger.info(f"Enabled RLS on table: {table_name}")
        except Exception as e:
            logger.error(f"Failed to enable RLS on table {table_name}: {e}")
            raise

    def enable_rls_on_table_sync(self, session: Session, table_name: str) -> None:
        """
        Enable Row-Level Security on a specific table (sync version).

        Args:
            session: Sync database session
            table_name: Name of the table to enable RLS on
        """
        try:
            session.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
            logger.info(f"Enabled RLS on table: {table_name} (sync)")
        except Exception as e:
            logger.error(f"Failed to enable RLS on table {table_name} (sync): {e}")
            raise

    async def create_user_isolation_policy(
        self, session: AsyncSession, table_name: str, user_id_column: str = "user_id"
    ) -> None:
        """
        Create standard user isolation RLS policies for a table.
        Creates policies for SELECT, INSERT, UPDATE, and DELETE operations.

        Args:
            session: Database session
            table_name: Name of the table
            user_id_column: Name of the user ID column (default: "user_id")
        """
        try:
            # Drop existing policies if they exist
            policy_names = [
                f"Users can view their own {table_name}",
                f"Users can create their own {table_name}",
                f"Users can update their own {table_name}",
                f"Users can delete their own {table_name}",
            ]

            for policy_name in policy_names:
                await session.execute(
                    text(f'DROP POLICY IF EXISTS "{policy_name}" ON {table_name}')
                )

            # Create SELECT policy
            await session.execute(
                text(
                    f"""
                CREATE POLICY "Users can view their own {table_name}"
                ON {table_name}
                FOR SELECT
                USING (current_app_user() = {user_id_column})
            """
                )
            )

            # Create INSERT policy
            await session.execute(
                text(
                    f"""
                CREATE POLICY "Users can create their own {table_name}"
                ON {table_name}
                FOR INSERT
                WITH CHECK (current_app_user() = {user_id_column})
            """
                )
            )

            # Create UPDATE policy
            await session.execute(
                text(
                    f"""
                CREATE POLICY "Users can update their own {table_name}"
                ON {table_name}
                FOR UPDATE
                USING (current_app_user() = {user_id_column})
            """
                )
            )

            # Create DELETE policy
            await session.execute(
                text(
                    f"""
                CREATE POLICY "Users can delete their own {table_name}"
                ON {table_name}
                FOR DELETE
                USING (current_app_user() = {user_id_column})
            """
                )
            )

            logger.info(f"Created user isolation policies for table: {table_name}")
        except Exception as e:
            logger.error(
                f"Failed to create user isolation policies for {table_name}: {e}"
            )
            raise

    def create_user_isolation_policy_sync(
        self, session: Session, table_name: str, user_id_column: str = "user_id"
    ) -> None:
        """
        Create standard user isolation RLS policies for a table (sync version).

        Args:
            session: Sync database session
            table_name: Name of the table
            user_id_column: Name of the user ID column (default: "user_id")
        """
        try:
            # Drop existing policies if they exist
            policy_names = [
                f"Users can view their own {table_name}",
                f"Users can create their own {table_name}",
                f"Users can update their own {table_name}",
                f"Users can delete their own {table_name}",
            ]

            for policy_name in policy_names:
                session.execute(
                    text(f'DROP POLICY IF EXISTS "{policy_name}" ON {table_name}')
                )

            # Create SELECT policy
            session.execute(
                text(
                    f"""
                CREATE POLICY "Users can view their own {table_name}"
                ON {table_name}
                FOR SELECT
                USING (current_app_user() = {user_id_column})
            """
                )
            )

            # Create INSERT policy
            session.execute(
                text(
                    f"""
                CREATE POLICY "Users can create their own {table_name}"
                ON {table_name}
                FOR INSERT
                WITH CHECK (current_app_user() = {user_id_column})
            """
                )
            )

            # Create UPDATE policy
            session.execute(
                text(
                    f"""
                CREATE POLICY "Users can update their own {table_name}"
                ON {table_name}
                FOR UPDATE
                USING (current_app_user() = {user_id_column})
            """
                )
            )

            # Create DELETE policy
            session.execute(
                text(
                    f"""
                CREATE POLICY "Users can delete their own {table_name}"
                ON {table_name}
                FOR DELETE
                USING (current_app_user() = {user_id_column})
            """
                )
            )

            logger.info(
                f"Created user isolation policies for table: {table_name} (sync)"
            )
        except Exception as e:
            logger.error(
                f"Failed to create user isolation policies for {table_name} (sync): {e}"
            )
            raise

    async def create_messages_policy(self, session: AsyncSession) -> None:
        """
        Create special RLS policy for messages table that checks through conversations.

        Args:
            session: Database session
        """
        try:
            # Drop existing policy if it exists
            await session.execute(
                text(
                    'DROP POLICY IF EXISTS "Users can manage messages in their own conversations" ON messages'
                )
            )

            # Create policy for messages that checks through conversations
            await session.execute(
                text(
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
            )

            logger.info("Created messages RLS policy")
        except Exception as e:
            logger.error(f"Failed to create messages RLS policy: {e}")
            raise

    def create_messages_policy_sync(self, session: Session) -> None:
        """
        Create special RLS policy for messages table that checks through conversations (sync version).

        Args:
            session: Sync database session
        """
        try:
            # Drop existing policy if it exists
            session.execute(
                text(
                    'DROP POLICY IF EXISTS "Users can manage messages in their own conversations" ON messages'
                )
            )

            # Create policy for messages that checks through conversations
            session.execute(
                text(
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
            )

            logger.info("Created messages RLS policy (sync)")
        except Exception as e:
            logger.error(f"Failed to create messages RLS policy (sync): {e}")
            raise

    async def validate_rls_setup(self, session: AsyncSession) -> bool:
        """
        Validate that RLS is properly set up for all tables.

        Args:
            session: Database session

        Returns:
            bool: True if RLS is properly configured, False otherwise
        """
        try:
            # Check if current_app_user function exists
            result = await session.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc 
                    WHERE proname = 'current_app_user'
                )
            """
                )
            )

            if not result.scalar():
                logger.error("current_app_user function not found")
                return False

            # Check if RLS is enabled on key tables
            tables_to_check = [
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

            for table in tables_to_check:
                result = await session.execute(
                    text(
                        f"""
                    SELECT relrowsecurity 
                    FROM pg_class 
                    WHERE relname = '{table}'
                """
                    )
                )

                rls_enabled = result.scalar()
                if not rls_enabled:
                    logger.warning(f"RLS not enabled on table: {table}")

            logger.info("RLS validation completed")
            return True

        except Exception as e:
            logger.error(f"RLS validation failed: {e}")
            return False

    def validate_rls_setup_sync(self, session: Session) -> bool:
        """
        Validate that RLS is properly set up for all tables (sync version).

        Args:
            session: Sync database session

        Returns:
            bool: True if RLS is properly configured, False otherwise
        """
        try:
            # Check if current_app_user function exists
            result = session.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1 FROM pg_proc 
                    WHERE proname = 'current_app_user'
                )
            """
                )
            )

            if not result.scalar():
                logger.error("current_app_user function not found")
                return False

            # Check if RLS is enabled on key tables
            tables_to_check = [
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

            for table in tables_to_check:
                result = session.execute(
                    text(
                        f"""
                    SELECT relrowsecurity 
                    FROM pg_class 
                    WHERE relname = '{table}'
                """
                    )
                )

                rls_enabled = result.scalar()
                if not rls_enabled:
                    logger.warning(f"RLS not enabled on table: {table} (sync)")

            logger.info("RLS validation completed (sync)")
            return True

        except Exception as e:
            logger.error(f"RLS validation failed (sync): {e}")
            return False


# Global RLS policy manager instance
rls_manager = RLSPolicyManager()

"""
Migration management system for automated database migrations.
Handles Alembic integration and provides migration utilities.
"""

import logging
import os
import time
from typing import List, Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Base exception for migration errors."""

    def __init__(
        self,
        message: str,
        migration_id: Optional[str] = None,
        rollback_available: bool = False,
    ):
        self.message = message
        self.migration_id = migration_id
        self.rollback_available = rollback_available
        super().__init__(message)


class MigrationTimeoutError(MigrationError):
    """Exception raised when migration times out."""

    pass


class MigrationLockError(MigrationError):
    """Exception raised when migration lock cannot be acquired."""

    pass


class MigrationManager:
    """Manages database migrations using Alembic."""

    def __init__(self):
        self.alembic_cfg_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "alembic.ini"
        )
        self.alembic_cfg = Config(self.alembic_cfg_path)
        # Set the database URL from settings
        self.alembic_cfg.set_main_option("sqlalchemy.url", settings.get_database_url())

    def _get_sync_engine(self):
        """Get the sync engine from database module."""
        from app.core.database import get_sync_engine

        return get_sync_engine()

    def _acquire_migration_lock(self, timeout: int = 60) -> bool:
        """
        Acquire a migration lock to prevent concurrent migrations.

        Args:
            timeout: Maximum time to wait for lock in seconds

        Returns:
            bool: True if lock acquired successfully
        """
        start_time = time.time()
        hostname = os.uname().nodename

        while time.time() - start_time < timeout:
            try:
                with self._get_sync_engine().connect() as conn:
                    # Create migration_lock table if it doesn't exist (PostgreSQL compatible)
                    conn.execute(
                        text(
                            """
                        CREATE TABLE IF NOT EXISTS migration_lock (
                            id INTEGER PRIMARY KEY,
                            locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            locked_by TEXT,
                            process_id TEXT
                        )
                    """
                        )
                    )
                    conn.commit()

                    # Clean up stale locks (older than 30 minutes)
                    # Use database-agnostic approach
                    from datetime import datetime, timedelta

                    cutoff_time = datetime.now() - timedelta(minutes=30)
                    conn.execute(
                        text(
                            """
                        DELETE FROM migration_lock 
                        WHERE locked_at < :cutoff_time
                    """
                        ),
                        {"cutoff_time": cutoff_time},
                    )
                    conn.commit()

                    # Try to acquire lock
                    result = conn.execute(
                        text(
                            """
                        INSERT INTO migration_lock (id, locked_by, process_id) 
                        VALUES (1, :hostname, :process_id)
                        ON CONFLICT (id) DO NOTHING
                    """
                        ),
                        {
                            "hostname": hostname,
                            "process_id": f"{hostname}-{os.getpid()}",
                        },
                    )

                    conn.commit()

                    if result.rowcount > 0:
                        logger.info(
                            f"Migration lock acquired by {hostname}-{os.getpid()}"
                        )
                        return True
                    else:
                        # Check who has the lock
                        lock_info = conn.execute(
                            text(
                                """
                            SELECT locked_by, locked_at, process_id 
                            FROM migration_lock WHERE id = 1
                        """
                            )
                        ).fetchone()

                        if lock_info:
                            logger.info(
                                f"Migration lock held by {lock_info[2]} since {lock_info[1]}"
                            )

                        # Wait before retrying
                        time.sleep(2)

            except Exception as e:
                logger.error(f"Failed to acquire migration lock: {e}")
                time.sleep(2)

        logger.error(f"Failed to acquire migration lock within {timeout} seconds")
        return False

    def _release_migration_lock(self) -> None:
        """Release the migration lock."""
        try:
            with self._get_sync_engine().connect() as conn:
                result = conn.execute(text("DELETE FROM migration_lock WHERE id = 1"))
                conn.commit()
                if result.rowcount > 0:
                    logger.info("Migration lock released successfully")
                else:
                    logger.warning("No migration lock found to release")
        except Exception as e:
            logger.error(f"Failed to release migration lock: {e}")

    def check_pending_migrations(self) -> List[str]:
        """
        Check for pending migrations.

        Returns:
            List[str]: List of pending migration revision IDs
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)

            with self._get_sync_engine().connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()

                # Get all revisions
                revisions = list(script.walk_revisions())

                if not current_rev:
                    # No migrations applied yet, all are pending
                    return [rev.revision for rev in reversed(revisions)]

                # Find pending migrations
                # walk_revisions() returns in reverse chronological order (newest first)
                # We want to find revisions that are newer than current_rev
                pending = []
                found_current = False

                for rev in revisions:  # Don't reverse - we want newest first
                    if rev.revision == current_rev:
                        found_current = True
                        break
                    pending.append(rev.revision)

                # If we didn't find the current revision, all revisions are pending
                if not found_current:
                    pending = [rev.revision for rev in reversed(revisions)]

                return pending

        except Exception as e:
            logger.error(f"Failed to check pending migrations: {e}")
            raise MigrationError(f"Failed to check pending migrations: {e}")

    def apply_pending_migrations(self) -> bool:
        """
        Apply all pending migrations.

        Returns:
            bool: True if migrations applied successfully
        """
        pending = self.check_pending_migrations()

        if not pending:
            logger.info("No pending migrations to apply")
            return True

        logger.info(f"Found {len(pending)} pending migrations: {pending}")

        # Acquire migration lock
        if not self._acquire_migration_lock():
            raise MigrationLockError(
                "Could not acquire migration lock. Another migration may be in progress."
            )

        try:
            # Apply migrations with timeout
            start_time = time.time()

            logger.info("Applying pending migrations...")
            command.upgrade(self.alembic_cfg, "head")

            elapsed = time.time() - start_time
            if elapsed > settings.migration_timeout:
                raise MigrationTimeoutError(
                    f"Migration timed out after {elapsed:.2f} seconds"
                )

            logger.info(
                f"Successfully applied {len(pending)} migrations in {elapsed:.2f} seconds"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to apply migrations: {e}")
            raise MigrationError(f"Failed to apply migrations: {e}")

        finally:
            self._release_migration_lock()

    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """
        Create a new migration file.

        Args:
            message: Migration message/description
            autogenerate: Whether to auto-generate migration from model changes

        Returns:
            str: The revision ID of the created migration
        """
        try:
            if autogenerate:
                command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message=message)

            # Get the latest revision
            script = ScriptDirectory.from_config(self.alembic_cfg)
            latest_rev = script.get_current_head()

            logger.info(f"Created migration {latest_rev}: {message}")
            return latest_rev

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            raise MigrationError(f"Failed to create migration: {e}")

    def rollback_migration(self, revision: str) -> bool:
        """
        Rollback to a specific migration revision.

        Args:
            revision: Target revision to rollback to

        Returns:
            bool: True if rollback successful
        """
        if not self._acquire_migration_lock():
            raise MigrationLockError("Could not acquire migration lock for rollback")

        try:
            logger.warning(f"Rolling back to revision: {revision}")
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Successfully rolled back to revision: {revision}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback migration: {e}")
            raise MigrationError(
                f"Failed to rollback migration: {e}", rollback_available=False
            )

        finally:
            self._release_migration_lock()

    def get_migration_history(self) -> List[dict]:
        """
        Get migration history.

        Returns:
            List[dict]: List of applied migrations with metadata
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)

            with self._get_sync_engine().connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()

                history = []
                for rev in script.walk_revisions():
                    is_applied = False
                    if current_rev:
                        # Check if this revision is applied
                        is_applied = rev.revision == current_rev or rev.is_ancestor_of(
                            current_rev, script
                        )

                    history.append(
                        {
                            "revision": rev.revision,
                            "message": rev.doc,
                            "is_applied": is_applied,
                            "branch_labels": getattr(rev, "branch_labels", None),
                            "depends_on": getattr(rev, "depends_on", None),
                        }
                    )

                return history

        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            raise MigrationError(f"Failed to get migration history: {e}")

    def get_migration_status(self) -> dict:
        """
        Get current migration status for monitoring and debugging.

        Returns:
            dict: Migration status information
        """
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)

            with self._get_sync_engine().connect() as conn:
                context = MigrationContext.configure(conn)
                current_rev = context.get_current_revision()

                # Get all revisions
                all_revisions = list(script.walk_revisions())
                total_migrations = len(all_revisions)

                # Count applied migrations
                applied_count = 0
                if current_rev:
                    for rev in all_revisions:
                        if rev.revision == current_rev or rev.is_ancestor_of(
                            current_rev, script
                        ):
                            applied_count += 1

                pending = self.check_pending_migrations()

                return {
                    "current_revision": current_rev,
                    "total_migrations": total_migrations,
                    "applied_migrations": applied_count,
                    "pending_migrations": len(pending),
                    "pending_revision_ids": pending,
                    "database_connection_valid": True,
                    "auto_migration_enabled": settings.auto_apply_migrations,
                }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "error": str(e),
                "database_connection_valid": False,
                "auto_migration_enabled": settings.auto_apply_migrations,
            }

    def auto_migrate_on_startup(self) -> bool:
        """
        Automatically apply pending migrations on application startup.

        Returns:
            bool: True if successful or no migrations needed
        """
        if not settings.auto_apply_migrations:
            logger.info("Auto-migration disabled in settings")
            return True

        try:
            # Log startup migration status
            status = self.get_migration_status()
            logger.info(f"Migration status on startup: {status}")

            pending = self.check_pending_migrations()

            if not pending:
                logger.info("No pending migrations on startup")
                return True

            logger.info(
                f"Auto-applying {len(pending)} pending migrations on startup: {pending}"
            )

            # Apply migrations with detailed logging
            start_time = time.time()
            success = self.apply_pending_migrations()
            elapsed = time.time() - start_time

            if success:
                logger.info(
                    f"Startup migration completed successfully in {elapsed:.2f} seconds"
                )

                # Log final status
                final_status = self.get_migration_status()
                logger.info(f"Final migration status: {final_status}")
            else:
                logger.error("Startup migration failed")

            return success

        except Exception as e:
            logger.error(f"Auto-migration failed on startup: {e}")

            # Log migration status for debugging
            try:
                status = self.get_migration_status()
                logger.error(f"Migration status after failure: {status}")
            except Exception:
                pass  # Don't fail if we can't get status

            if settings.environment == "production":
                # In production, fail startup if migrations fail
                raise
            else:
                # In development, log error but continue
                logger.warning(
                    "Continuing startup despite migration failure in non-production environment"
                )
                return False

    def validate_database_connection(self) -> bool:
        """
        Validate that database connection is working.

        Returns:
            bool: True if connection is valid
        """
        try:
            logger.info("Validating database connection...")
            with self._get_sync_engine().connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("Database connection validation successful")
                    return True
                else:
                    logger.error(
                        "Database connection validation failed: unexpected result"
                    )
                    return False
        except Exception as e:
            logger.error(f"Database connection validation failed: {e}")
            return False


# Global migration manager instance
migration_manager = MigrationManager()

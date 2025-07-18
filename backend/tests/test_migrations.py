"""
Tests for the migration management system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.core.migrations import (
    MigrationManager,
    MigrationError,
    MigrationTimeoutError,
    MigrationLockError,
)


class TestMigrationManager:
    """Test cases for MigrationManager."""

    def test_migration_manager_initialization(self):
        """Test that MigrationManager initializes correctly."""
        manager = MigrationManager()
        assert manager.alembic_cfg is not None
        assert manager.alembic_cfg_path is not None

    @patch("app.core.migrations.sync_engine")
    def test_validate_database_connection_success(self, mock_engine):
        """Test successful database connection validation."""
        mock_conn = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        manager = MigrationManager()
        result = manager.validate_database_connection()

        assert result is True
        mock_conn.execute.assert_called_once()

    @patch("app.core.migrations.sync_engine")
    def test_validate_database_connection_failure(self, mock_engine):
        """Test database connection validation failure."""
        mock_engine.connect.side_effect = Exception("Connection failed")

        manager = MigrationManager()
        result = manager.validate_database_connection()

        assert result is False

    @patch("app.core.migrations.sync_engine")
    def test_acquire_migration_lock_success(self, mock_engine):
        """Test successful migration lock acquisition."""
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        manager = MigrationManager()
        result = manager._acquire_migration_lock()

        assert result is True

    @patch("app.core.migrations.sync_engine")
    def test_acquire_migration_lock_failure(self, mock_engine):
        """Test migration lock acquisition failure."""
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_conn.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        manager = MigrationManager()
        result = manager._acquire_migration_lock()

        assert result is False

    @patch("app.core.migrations.ScriptDirectory")
    @patch("app.core.migrations.sync_engine")
    def test_check_pending_migrations_none_applied(self, mock_engine, mock_script_dir):
        """Test checking pending migrations when none are applied."""
        # Mock the migration context
        mock_conn = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        mock_context = Mock()
        mock_context.get_current_revision.return_value = None

        # Mock script directory and revisions
        mock_script = Mock()
        mock_rev1 = Mock()
        mock_rev1.revision = "rev1"
        mock_rev2 = Mock()
        mock_rev2.revision = "rev2"
        mock_script.walk_revisions.return_value = [
            mock_rev2,
            mock_rev1,
        ]  # Reversed order
        mock_script_dir.from_config.return_value = mock_script

        with patch("app.core.migrations.MigrationContext") as mock_migration_context:
            mock_migration_context.configure.return_value = mock_context

            manager = MigrationManager()
            pending = manager.check_pending_migrations()

            assert pending == ["rev1", "rev2"]  # Should be in correct order

    @patch("app.core.migrations.ScriptDirectory")
    @patch("app.core.migrations.sync_engine")
    def test_check_pending_migrations_some_applied(self, mock_engine, mock_script_dir):
        """Test checking pending migrations when some are applied."""
        # Mock the migration context
        mock_conn = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        mock_context = Mock()
        mock_context.get_current_revision.return_value = "rev2"

        # Mock script directory and revisions
        mock_script = Mock()
        mock_rev1 = Mock()
        mock_rev1.revision = "rev1"
        mock_rev2 = Mock()
        mock_rev2.revision = "rev2"
        mock_rev3 = Mock()
        mock_rev3.revision = "rev3"
        # Walk revisions returns in reverse chronological order (newest first)
        # So rev3 is newest, rev2 is current, rev1 is oldest
        mock_script.walk_revisions.return_value = [mock_rev3, mock_rev2, mock_rev1]
        mock_script_dir.from_config.return_value = mock_script

        with patch("app.core.migrations.MigrationContext") as mock_migration_context:
            mock_migration_context.configure.return_value = mock_context

            manager = MigrationManager()
            pending = manager.check_pending_migrations()

            # Should return rev3 as pending (rev2 is current, rev1 is already applied)
            assert pending == ["rev3"]

    @patch("app.core.migrations.command")
    def test_apply_pending_migrations_success(self, mock_command):
        """Test successful migration application."""
        manager = MigrationManager()

        with patch.object(manager, "check_pending_migrations", return_value=["rev1"]):
            with patch.object(manager, "_acquire_migration_lock", return_value=True):
                with patch.object(manager, "_release_migration_lock"):
                    result = manager.apply_pending_migrations()

                    assert result is True
                    mock_command.upgrade.assert_called_once()

    def test_apply_pending_migrations_no_pending(self):
        """Test migration application when no migrations are pending."""
        manager = MigrationManager()

        with patch.object(manager, "check_pending_migrations", return_value=[]):
            result = manager.apply_pending_migrations()

            assert result is True

    def test_apply_pending_migrations_lock_failure(self):
        """Test migration application when lock cannot be acquired."""
        manager = MigrationManager()

        with patch.object(manager, "check_pending_migrations", return_value=["rev1"]):
            with patch.object(manager, "_acquire_migration_lock", return_value=False):
                with pytest.raises(MigrationLockError):
                    manager.apply_pending_migrations()

    @patch("app.core.migrations.command")
    def test_create_migration_success(self, mock_command):
        """Test successful migration creation."""
        mock_script = Mock()
        mock_script.get_current_head.return_value = "new_rev_id"

        with patch("app.core.migrations.ScriptDirectory") as mock_script_dir:
            mock_script_dir.from_config.return_value = mock_script

            manager = MigrationManager()
            result = manager.create_migration("test migration")

            assert result == "new_rev_id"
            mock_command.revision.assert_called_once()

    @patch("app.core.migrations.command")
    def test_rollback_migration_success(self, mock_command):
        """Test successful migration rollback."""
        manager = MigrationManager()

        with patch.object(manager, "_acquire_migration_lock", return_value=True):
            with patch.object(manager, "_release_migration_lock"):
                result = manager.rollback_migration("target_rev")

                assert result is True
                mock_command.downgrade.assert_called_once_with(
                    manager.alembic_cfg, "target_rev"
                )

    def test_rollback_migration_lock_failure(self):
        """Test migration rollback when lock cannot be acquired."""
        manager = MigrationManager()

        with patch.object(manager, "_acquire_migration_lock", return_value=False):
            with pytest.raises(MigrationLockError):
                manager.rollback_migration("target_rev")

#!/usr/bin/env python3
"""
Migration CLI script for managing database migrations.
Provides commands for creating, applying, and managing migrations.
"""

import argparse
import logging
import sys
from typing import Optional

from app.core.config import settings
from app.core.migrations import migration_manager, MigrationError


def setup_logging():
    """Set up logging for the CLI."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_migration(message: str, autogenerate: bool = True) -> None:
    """Create a new migration."""
    try:
        revision_id = migration_manager.create_migration(message, autogenerate)
        print(f"✅ Created migration {revision_id}: {message}")
    except MigrationError as e:
        print(f"❌ Failed to create migration: {e}")
        sys.exit(1)


def apply_migrations() -> None:
    """Apply pending migrations."""
    try:
        success = migration_manager.apply_pending_migrations()
        if success:
            print("✅ All migrations applied successfully")
        else:
            print("⚠️  Some migrations may have failed")
            sys.exit(1)
    except MigrationError as e:
        print(f"❌ Failed to apply migrations: {e}")
        sys.exit(1)


def check_migrations() -> None:
    """Check for pending migrations."""
    try:
        pending = migration_manager.check_pending_migrations()
        if pending:
            print(f"📋 Found {len(pending)} pending migrations:")
            for revision in pending:
                print(f"  - {revision}")
        else:
            print("✅ No pending migrations")
    except MigrationError as e:
        print(f"❌ Failed to check migrations: {e}")
        sys.exit(1)


def migration_history() -> None:
    """Show migration history."""
    try:
        history = migration_manager.get_migration_history()
        if not history:
            print("📋 No migrations found")
            return

        print("📋 Migration History:")
        print("-" * 80)
        for migration in history:
            status = "✅ Applied" if migration["is_applied"] else "⏳ Pending"
            print(f"{status} | {migration['revision']} | {migration['message']}")
    except MigrationError as e:
        print(f"❌ Failed to get migration history: {e}")
        sys.exit(1)


def rollback_migration(revision: str) -> None:
    """Rollback to a specific migration."""
    try:
        success = migration_manager.rollback_migration(revision)
        if success:
            print(f"✅ Successfully rolled back to revision: {revision}")
        else:
            print(f"❌ Failed to rollback to revision: {revision}")
            sys.exit(1)
    except MigrationError as e:
        print(f"❌ Rollback failed: {e}")
        sys.exit(1)


def validate_connection() -> None:
    """Validate database connection."""
    try:
        is_valid = migration_manager.validate_database_connection()
        if is_valid:
            print("✅ Database connection is valid")
        else:
            print("❌ Database connection failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection validation error: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    setup_logging()

    parser = argparse.ArgumentParser(description="Database migration management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create migration command
    create_parser = subparsers.add_parser("create", help="Create a new migration")
    create_parser.add_argument("message", help="Migration message/description")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Create empty migration without auto-generation",
    )

    # Apply migrations command
    subparsers.add_parser("apply", help="Apply pending migrations")

    # Check migrations command
    subparsers.add_parser("check", help="Check for pending migrations")

    # Migration history command
    subparsers.add_parser("history", help="Show migration history")

    # Rollback command
    rollback_parser = subparsers.add_parser(
        "rollback", help="Rollback to a specific migration"
    )
    rollback_parser.add_argument("revision", help="Target revision to rollback to")

    # Validate connection command
    subparsers.add_parser("validate", help="Validate database connection")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print(f"🔧 Migration CLI - Environment: {settings.environment}")
    print(f"🔗 Database: {settings.get_database_url()}")
    print("-" * 80)

    try:
        if args.command == "create":
            create_migration(args.message, not args.no_autogenerate)
        elif args.command == "apply":
            apply_migrations()
        elif args.command == "check":
            check_migrations()
        elif args.command == "history":
            migration_history()
        elif args.command == "rollback":
            rollback_migration(args.revision)
        elif args.command == "validate":
            validate_connection()
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify migration system is working correctly.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "."))

from app.core.migrations import migration_manager


def test_migration_status():
    """Test getting migration status."""
    print("Testing migration status...")

    try:
        status = migration_manager.get_migration_status()
        print(f"✓ Migration status: {status}")

        if "error" in status:
            print(f"✗ Error in migration status: {status['error']}")
            return False

        return True
    except Exception as e:
        print(f"✗ Migration status error: {e}")
        return False


def test_database_connection():
    """Test database connection."""
    print("\nTesting database connection...")

    try:
        is_valid = migration_manager.validate_database_connection()
        if is_valid:
            print("✓ Database connection is valid")
            return True
        else:
            print("✗ Database connection is invalid")
            return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False


def test_pending_migrations():
    """Test checking pending migrations."""
    print("\nTesting pending migrations check...")

    try:
        pending = migration_manager.check_pending_migrations()
        print(f"✓ Pending migrations: {pending}")
        return True
    except Exception as e:
        print(f"✗ Pending migrations error: {e}")
        return False


def main():
    """Run all migration tests."""
    print("=== Migration System Test ===\n")

    tests = [
        test_database_connection,
        test_migration_status,
        test_pending_migrations,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Results ===")
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("✓ All migration tests passed!")
        return True
    else:
        print("✗ Some migration tests failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

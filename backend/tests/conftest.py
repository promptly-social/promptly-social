"""
Test configuration and fixtures.
Sets up test database and environment variables for testing.
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the backend app directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables before importing app modules
os.environ.update(
    {
        "ENVIRONMENT": "testing",
        "APP_NAME": "Test API",
        "DEBUG": "true",
        "DATABASE_URL": "sqlite:///./test.db",
        "DATABASE_URL_ASYNC": "sqlite+aiosqlite:///./test.db",
        "SUPABASE_URL": "https://test.supabase.co",
        # Valid JWT format for Supabase keys to avoid validation errors
        "SUPABASE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "SUPABASE_SERVICE_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "JWT_SECRET_KEY": "test-jwt-secret-key",
        "CORS_ORIGINS": "http://localhost:3000",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "1440",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "console",
    }
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    from app.main import app

    return TestClient(app)


@pytest.fixture(scope="session")
def test_settings():
    """Provide test settings for the entire test session."""
    from app.core.config import settings

    return settings

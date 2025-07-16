"""
Tests for authentication functionality.
Includes unit tests for auth service and integration tests for auth endpoints.
"""

import os
import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_auth.db"


@pytest.fixture
def mock_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!",
        "full_name": "Test User",
        "preferred_language": "en",
        "timezone": "UTC",
    }


@pytest.fixture
def mock_login_data():
    """Sample login data for testing."""
    return {"email": "test@example.com", "password": "TestPassword123!"}


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = MagicMock()

    # Mock successful sign up
    mock_client.sign_up.return_value = {
        "user": Mock(id="12345", email="test@example.com", email_confirmed_at=None),
        "session": None,
        "error": None,
    }

    # Mock successful sign in
    mock_client.sign_in.return_value = {
        "user": Mock(id="12345", email="test@example.com"),
        "session": Mock(
            access_token="mock_access_token", refresh_token="mock_refresh_token"
        ),
        "error": None,
    }

    return mock_client


@pytest.fixture
def client(mock_supabase_client):
    """Create test client with mocked Supabase."""
    with patch("app.utils.supabase.supabase_client", mock_supabase_client):
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create test database session."""
    from app.core.database import Base

    # Remove existing test database
    if os.path.exists("./test_auth.db"):
        os.remove("./test_auth.db")

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables first
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Provide session for test
    async with async_session() as session:
        yield session

    # Clean up
    await engine.dispose()

    # Remove test database file
    if os.path.exists("./test_auth.db"):
        os.remove("./test_auth.db")


@pytest_asyncio.fixture
async def test_auth_service(test_db):
    """Create auth service with test database."""
    from app.services.auth import AuthService

    return AuthService(test_db)


class TestAuthService:
    """Test cases for AuthService."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, test_auth_service):
        """Test getting current user with valid token."""
        from app.core.security import create_access_token
        from app.models.user import User

        # Create test user in test database
        user_id = str(uuid.uuid4())
        test_user = User(id=user_id, email="test@example.com")
        test_auth_service.db.add(test_user)
        await test_auth_service.db.commit()
        await test_auth_service.db.refresh(test_user)

        # Create a token with the user's ID
        access_token = create_access_token(str(test_user.id))
        result = await test_auth_service.get_current_user(access_token)

        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, test_auth_service):
        """Test getting current user with invalid token."""
        result = await test_auth_service.get_current_user("invalid_token")
        assert result is None


class TestAuthEndpoints:
    """Test cases for authentication endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        """Mock current user for authenticated endpoints."""
        from datetime import datetime
        from app.schemas.auth import UserResponse
        from app.routers.auth import get_current_user
        from app.main import app

        user = UserResponse(
            id=str(uuid.uuid4()),
            email="test@example.com",
            full_name="Test User",
            preferred_language="en",
            timezone="UTC",
            is_active=True,
            is_verified=True,
            created_at=datetime.now(),
        )

        async def mock_get_current_user():
            return user

        app.dependency_overrides[get_current_user] = mock_get_current_user
        yield user
        app.dependency_overrides.clear()

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/auth/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "authentication"

    def test_app_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "status" in data

    def test_update_user_endpoint_success(
        self, client, mock_user_data, mock_current_user
    ):
        """Test successful user update endpoint."""
        with patch("app.services.auth.AuthService.update_user") as mock_update:
            from datetime import datetime
            from app.schemas.auth import UserResponse

            mock_user = UserResponse(
                id=str(uuid.uuid4()),
                email=mock_user_data["email"],
                full_name="Updated Name",
                preferred_language="en",
                timezone="UTC",
                is_active=True,
                is_verified=False,
                created_at=datetime.now(),
            )

            mock_update.return_value = mock_user

            update_data = {
                "full_name": "Updated Name",
            }

            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["full_name"] == "Updated Name"

    def test_update_user_endpoint_password_update(
        self, client, mock_user_data, mock_current_user
    ):
        """Test user update endpoint with password change."""
        with patch("app.services.auth.AuthService.update_user") as mock_update:
            from datetime import datetime
            from app.schemas.auth import UserResponse

            mock_user = UserResponse(
                id=str(uuid.uuid4()),
                email=mock_user_data["email"],
                full_name=mock_user_data["full_name"],
                preferred_language="en",
                timezone="UTC",
                is_active=True,
                is_verified=False,
                created_at=datetime.now(),
            )

            mock_update.return_value = mock_user

            update_data = {
                "password": "NewPassword123",
                "confirm_password": "NewPassword123",
            }

            response = client.put(
                "/api/v1/auth/me",
                json=update_data,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200


class TestSecurityUtilities:
    """Test cases for security utilities."""

    def test_create_access_token(self):
        """Test access token creation."""
        from app.core.security import create_access_token, verify_token

        user_id = "12345"
        token = create_access_token(user_id)

        assert token is not None
        assert len(token) > 0

        # Verify token
        decoded_user_id = verify_token(token, "access")
        assert decoded_user_id == user_id

    def test_password_hashing(self):
        """Test password hashing and verification."""
        from app.core.security import get_password_hash, verify_password

        password = "TestPassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_invalid_token_verification(self):
        """Test verification of invalid tokens."""
        from app.core.security import verify_token

        assert verify_token("invalid_token") is None
        assert verify_token("") is None


class TestConfiguration:
    """Test cases for configuration."""

    def test_settings_load(self):
        """Test that settings load correctly."""
        from app.core.config import settings

        assert settings.app_name == "Test API"
        assert settings.environment == "test"
        assert settings.debug is True
        assert isinstance(settings.get_cors_origins(), list)

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        from app.core.config import Settings

        # Test with comma-separated string
        test_settings = Settings(
            cors_origins="http://localhost:3000,https://example.com"
        )
        origins = test_settings.get_cors_origins()

        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "https://example.com" in origins

        # Test with empty string
        test_settings_empty = Settings(cors_origins="")
        origins_empty = test_settings_empty.get_cors_origins()
        assert origins_empty == []

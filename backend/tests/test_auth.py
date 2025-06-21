"""
Tests for authentication functionality.
Includes unit tests for auth service and integration tests for auth endpoints.
"""

import os
import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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
    async def test_sign_up_success(self, test_auth_service, mock_user_data):
        """Test successful user registration."""
        from app.schemas.auth import UserCreate

        # Mock all database and external dependencies
        with (
            patch("app.services.auth.supabase_client") as mock_supabase,
            patch.object(test_auth_service, "_get_user_by_email", return_value=None),
            patch.object(test_auth_service.db, "commit") as mock_commit,
            patch.object(test_auth_service.db, "refresh") as mock_refresh,
        ):
            # Since sign_up is now async, we need to return a coroutine
            async def mock_sign_up(*args, **kwargs):
                return {
                    "user": Mock(
                        id="12345", email="test@example.com", email_confirmed_at=None
                    ),
                    "session": None,
                    "error": None,
                }

            mock_supabase.sign_up = mock_sign_up

            # Mock async database operations
            mock_commit.return_value = AsyncMock()

            # Create a mock user with all required fields
            from datetime import datetime

            mock_user = Mock()
            mock_user.id = str(uuid.uuid4())
            mock_user.supabase_user_id = "12345"
            mock_user.email = mock_user_data["email"]
            mock_user.full_name = mock_user_data["full_name"]
            mock_user.preferred_language = "en"
            mock_user.timezone = "UTC"
            mock_user.is_active = True
            mock_user.is_verified = False
            mock_user.created_at = datetime.now()

            mock_refresh.return_value = AsyncMock()

            # Simulate the refresh operation setting values on the user
            async def mock_refresh_func(user):
                for attr, value in vars(mock_user).items():
                    setattr(user, attr, value)

            mock_refresh.side_effect = mock_refresh_func

            user_create = UserCreate(**mock_user_data)
            result = await test_auth_service.sign_up(user_create)

            assert result["error"] is None
            assert result["user"] is not None
            assert result["user"].email == mock_user_data["email"]

    @pytest.mark.asyncio
    async def test_sign_up_existing_user(self, test_auth_service, mock_user_data):
        """Test registration with existing email."""
        from app.models.user import User
        from app.schemas.auth import UserCreate

        # Create existing user in test database
        existing_user = User(
            supabase_user_id=str(uuid.uuid4()), email=mock_user_data["email"]
        )
        test_auth_service.db.add(existing_user)
        await test_auth_service.db.commit()

        user_create = UserCreate(**mock_user_data)
        result = await test_auth_service.sign_up(user_create)

        assert result["error"] == "User with this email already exists"
        assert result["user"] is None

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, test_auth_service):
        """Test getting current user with valid token."""
        from app.core.security import create_access_token
        from app.models.user import User

        # Create test user in test database
        user_id = str(uuid.uuid4())
        test_user = User(
            id=user_id, supabase_user_id=str(uuid.uuid4()), email="test@example.com"
        )
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

    def test_signup_endpoint_success(self, client, mock_user_data):
        """Test successful signup endpoint."""
        with patch("app.services.auth.AuthService.sign_up") as mock_signup:
            # Create proper mock objects for Pydantic validation
            from datetime import datetime

            from app.schemas.auth import TokenResponse, UserResponse

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

            mock_tokens = TokenResponse(
                access_token="access_token",
                refresh_token="refresh_token",
                expires_in=1800,
            )

            mock_signup.return_value = {
                "error": None,
                "user": mock_user,
                "tokens": mock_tokens,
                "message": "User registered successfully",
            }

            response = client.post("/api/v1/auth/signup", json=mock_user_data)

            assert response.status_code == 201
            data = response.json()
            assert "user" in data
            assert "tokens" in data

    def test_signup_endpoint_validation_error(self, client):
        """Test signup endpoint with validation errors."""
        invalid_data = {
            "email": "invalid-email",
            "password": "weak",
            "confirm_password": "different",
        }

        response = client.post("/api/v1/auth/signup", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        # Our custom error handler returns 'details' instead of 'detail'
        assert "details" in data

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
        assert settings.environment == "testing"
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

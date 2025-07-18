"""
Shared dependencies for FastAPI endpoints.
Provides common dependencies like authentication and database sessions with RLS context.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db, get_sync_db
from app.core.rls import AuthContextHandler
from app.core.security import verify_token
from app.schemas.auth import UserResponse
from app.services.auth import AuthService

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> UserResponse:
    """
    Dependency to get current authenticated user.

    Args:
        credentials: HTTP Authorization header
        db: Database session

    Returns:
        Current user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = await auth_service.get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_with_rls(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> UserResponse:
    """
    Dependency to get current authenticated user and set RLS context.
    This dependency combines authentication with RLS context setting.

    Args:
        credentials: HTTP Authorization header
        db: Database session

    Returns:
        Current user information (RLS context is set as side effect)

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token and get user ID
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set RLS context for this session
    await AuthContextHandler.set_current_user(db, user_id)

    # Get user information
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_db_with_rls_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
) -> AsyncSession:
    """
    Dependency to get database session with RLS context set.
    This is useful when you need the database session but not the user object.

    Args:
        credentials: HTTP Authorization header
        db: Database session

    Returns:
        Database session with RLS context set

    Raises:
        HTTPException: If token is invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token and get user ID
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set RLS context for this session
    await AuthContextHandler.set_current_user(db, user_id)

    return db


def get_current_user_with_rls_sync(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_sync_db),
) -> UserResponse:
    """
    Sync dependency to get current authenticated user and set RLS context.
    This is for sync endpoints that use sync database sessions.

    Args:
        credentials: HTTP Authorization header
        db: Sync database session

    Returns:
        Current user information (RLS context is set as side effect)

    Raises:
        HTTPException: If token is invalid or user not found
    """

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token and get user ID
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set RLS context for this session (sync version)
    AuthContextHandler.set_current_user_sync(db, user_id)

    # For sync operations, we need to get user differently
    # Since AuthService is async, we'll create a simple sync user lookup
    from sqlalchemy import select
    from app.models.user import User

    stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
    result = db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse.model_validate({**user.__dict__, "id": str(user.id)})

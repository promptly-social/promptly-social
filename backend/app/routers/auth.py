"""
Authentication router with endpoints for user management.
Provides API endpoints that mirror the frontend AuthContext functionality.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.schemas.auth import (
    AuthResponse,
    GoogleAuthRequest,
    GoogleSignInWithToken,
    PasswordResetRequest,
    RefreshTokenRequest,
    SuccessResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth import AuthService

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

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


@router.post(
    "/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
async def sign_up(
    user_data: UserCreate, request: Request, db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user account.

    This endpoint mirrors the frontend signUp functionality from AuthContext.
    Creates a user in both Supabase Auth and local database.
    """
    try:
        # Get redirect URL from request origin
        origin = request.headers.get("origin", "http://localhost:3000")
        redirect_to = f"{origin}/"

        auth_service = AuthService(db)
        result = await auth_service.sign_up(user_data, redirect_to)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        # Build response
        response = AuthResponse(
            user=result["user"],
            tokens=result["tokens"]
            or TokenResponse(access_token="", refresh_token="", expires_in=0),
            message=result.get("message", "User registered successfully"),
        )

        logger.info(f"User registration successful: {user_data.email}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign up endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@router.post("/signin", response_model=AuthResponse)
async def sign_in(login_data: UserLogin, db: AsyncSession = Depends(get_async_db)):
    """
    Sign in a user with email and password.

    This endpoint mirrors the frontend signIn functionality from AuthContext.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.sign_in(login_data)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=result["error"]
            )

        response = AuthResponse(
            user=result["user"],
            tokens=result["tokens"],
            message=result.get("message", "Sign in successful"),
        )

        logger.info(f"User sign in successful: {login_data.email}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign in endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sign in failed"
        )


@router.post("/signin/google")
async def sign_in_with_google(
    oauth_request: GoogleAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Initiate Google OAuth sign in.

    This endpoint mirrors the frontend signInWithGoogle functionality from AuthContext.
    Returns the OAuth URL for client-side redirection.
    """
    try:
        # Get redirect URL from request or use default
        origin = request.headers.get("origin", "http://localhost:8080")
        # TODO: make the redirect_to configurable
        redirect_to = oauth_request.redirect_to or f"{origin}/new-content"

        auth_service = AuthService(db)
        result = await auth_service.sign_in_with_google(redirect_to)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        return {
            "url": result["url"],
            "message": result.get("message", "OAuth sign in initiated"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth sign in failed",
        )


@router.post("/signout", response_model=SuccessResponse)
async def sign_out(
    current_user: UserResponse = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Sign out the current user.

    This endpoint mirrors the frontend signOut functionality from AuthContext.
    Revokes the user's session and signs them out of Supabase.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.sign_out(credentials.credentials)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        logger.info(f"User sign out successful: {current_user.email}")
        return SuccessResponse(message=result.get("message", "Sign out successful"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sign out endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Sign out failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_async_db)
):
    """
    Refresh an access token using a refresh token.

    Provides token refresh functionality for maintaining user sessions.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(token_data.refresh_token)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=result["error"]
            )

        logger.info("Token refresh successful")
        return result["tokens"]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current user information.

    Returns the authenticated user's profile information.
    """
    return current_user


@router.post("/password/reset", response_model=SuccessResponse)
async def request_password_reset(reset_request: PasswordResetRequest, request: Request):
    """
    Request a password reset email.

    Sends a password reset email to the user via Supabase Auth.
    """
    try:
        from app.utils.supabase import supabase_client

        # Get redirect URL from request origin
        origin = request.headers.get("origin", "http://localhost:8080")
        redirect_to = f"{origin}/reset-password"

        result = await supabase_client.reset_password(reset_request.email, redirect_to)

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        logger.info(f"Password reset requested for: {reset_request.email}")
        return SuccessResponse(
            message="Password reset email sent. Please check your inbox."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed",
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the authentication service.
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": "2024-01-01T00:00:00Z",
    }


@router.get(
    "/callback/google",
    summary="Google OAuth Callback",
    description="Handles the server-side callback from Supabase after Google authentication. This endpoint exchanges the authorization code for a session, sets a secure cookie, and redirects to the frontend.",
    response_class=RedirectResponse,
)
async def google_oauth_callback(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handles the redirect from Supabase after a user authenticates with Google.
    - Exchanges the authorization code for a user session.
    - Sets secure, HTTPOnly cookies for the access and refresh tokens.
    - Redirects the user back to the frontend application.
    """
    code = request.query_params.get("code")
    if not code:
        logger.warning("Google OAuth callback called without an authorization code.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is missing from the callback.",
        )

    try:
        auth_service = AuthService(db)
        result = await auth_service.exchange_code_for_session(str(code))

        if result.get("error"):
            logger.error(f"Failed to exchange code for session: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error_description", "Invalid authorization code."),
            )

        tokens = result.get("tokens")
        if not tokens:
            logger.error("Token data is missing from the session exchange response.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve session tokens.",
            )

        # Redirect to the frontend, which will now have the session cookies.
        # The frontend URL should be configurable and depend on the environment.
        frontend_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "/"
        response = RedirectResponse(url=frontend_url)

        # Set secure, HTTPOnly cookies for the tokens
        response.set_cookie(
            key="sb-access-token",
            value=tokens.access_token,
            max_age=tokens.expires_in,
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT != "development",  # Use secure cookies in prod
            path="/",
        )
        response.set_cookie(
            key="sb-refresh-token",
            value=tokens.refresh_token,
            max_age=60 * 60 * 24 * 7,  # 7 days
            httponly=True,
            samesite="lax",
            secure=settings.ENVIRONMENT != "development",  # Use secure cookies in prod
            path="/",
        )

        logger.info(
            f"Successfully created session for user {result['user'].id} via Google OAuth."
        )
        return response

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc
    except Exception as e:
        logger.opt(exception=True).error(
            f"An unexpected error occurred during Google OAuth callback: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during the authentication process.",
        )


@router.post("/signin/google/token", response_model=AuthResponse)
async def sign_in_with_google_token(
    token_request: GoogleSignInWithToken,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Sign in with Google ID token.

    Alternative method for Google sign-in using ID token directly.
    """
    try:
        auth_service = AuthService(db)
        result = await auth_service.sign_in_with_google_token(
            token_request.id_token, token_request.redirect_to
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=result["error"]
            )

        response = AuthResponse(
            user=result["user"],
            tokens=result["tokens"],
            message=result.get("message", "Google sign in successful"),
        )

        logger.info(f"Google token sign in successful: {result['user'].email}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google token sign in endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google sign in failed",
        )

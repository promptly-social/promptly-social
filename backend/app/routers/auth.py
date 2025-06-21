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
    GoogleCallbackRequest,
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
            "code_verifier": result["code_verifier"],
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


@router.get("/callback/google")
async def google_oauth_callback_get(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle GET requests to the callback URL.
    These are typically from the user's browser redirection.
    This endpoint's primary job is to show a simple message or redirect.
    The actual code exchange happens via a POST from the frontend.
    """
    # This endpoint can be simplified as the real logic is in the POST
    logger.info("GET request to Google callback URL. Awaiting POST from frontend.")
    return {
        "message": "Authentication flow in progress. Please wait, you will be redirected shortly."
    }


@router.post("/callback/google", response_model=AuthResponse)
async def google_oauth_callback_post(
    callback_data: GoogleCallbackRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle Google OAuth callback from the frontend.

    This endpoint is called by the frontend, which passes the
    authorization code and the PKCE code_verifier.
    """
    try:
        logger.info(f"=== Google OAuth Callback POST Received ===")
        logger.info(
            f"Code: {callback_data.code[:20]}..." if callback_data.code else "No code"
        )

        auth_service = AuthService(db)
        result = await auth_service.handle_oauth_callback(
            code=callback_data.code,
            code_verifier=callback_data.code_verifier,
        )

        logger.info(f"Auth service result: {result.get('error', 'Success')}")

        if result["error"]:
            logger.error(f"OAuth callback error: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        # The user and tokens are valid, return them in an AuthResponse
        response = AuthResponse(
            user=result["user"],
            tokens=result["tokens"],
            message="Google sign in successful",
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"=== Google OAuth Callback POST Exception: {e} ===")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed",
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

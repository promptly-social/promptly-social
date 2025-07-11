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
    LinkedInAuthRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    ResendVerificationRequest,
    SuccessResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
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
        # Get redirect URL - point directly to frontend callback
        # Let frontend handle verification tokens using existing OAuth callback logic
        frontend_url = settings.frontend_url
        redirect_to = f"{frontend_url}/auth/callback"

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


@router.post("/signin/linkedin")
async def sign_in_with_linkedin(
    oauth_request: LinkedInAuthRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Initiate LinkedIn OAuth sign in.

    This endpoint mirrors the frontend signInWithLinkedIn functionality from AuthContext.
    Returns the OAuth URL for client-side redirection.
    """
    try:
        # Get redirect URL from request or use default
        origin = request.headers.get("origin", "http://localhost:8080")

        redirect_to = oauth_request.redirect_to or f"{origin}/new-content"

        auth_service = AuthService(db)
        result = await auth_service.sign_in_with_linkedin(redirect_to)

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
        logger.error(f"LinkedIn OAuth endpoint error: {e}")
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


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update current user's information.
    """
    auth_service = AuthService(db)
    updated_user = await auth_service.update_user(current_user.id, user_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated_user


@router.delete("/me", response_model=SuccessResponse)
async def delete_current_user(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete the current user's account and all associated data.
    """
    auth_service = AuthService(db)
    result = await auth_service.delete_account(current_user.id)
    if result["error"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["error"]
        )
    return SuccessResponse(message="Account deleted successfully")


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


@router.get("/callback/linkedin")
@router.get("/callback/linkedin_oidc")
async def linkedin_oauth_callback(
    request: Request,
    code: str,
    state: Optional[str] = None,
    redirect_to: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle LinkedIn OAuth callback.

    This endpoint is called by LinkedIn after user authorization.
    It exchanges the authorization code for user session.
    """
    try:
        # Check if this is called by the frontend (has specific headers)
        is_frontend_request = (
            request.headers.get("content-type") == "application/json"
            or "fetch" in request.headers.get("user-agent", "").lower()
            or request.headers.get("sec-fetch-mode") == "cors"
        )

        auth_service = AuthService(db)
        result = await auth_service.handle_oauth_callback(code, redirect_to)

        if result["error"]:
            logger.error(f"OAuth callback error: {result['error']}")

            if is_frontend_request:
                # Return JSON error for frontend requests
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
                )
            else:
                # Redirect to frontend with error for direct browser requests
                error_url = (
                    f"{redirect_to or 'http://localhost:8080'}?error={result['error']}"
                )
                logger.info(f"Redirecting to error URL: {error_url}")
                return RedirectResponse(url=error_url)

        if is_frontend_request:
            # Return JSON response for frontend requests
            response_data = {
                "access_token": result["tokens"].access_token,
                "refresh_token": result["tokens"].refresh_token,
                "expires_in": result["tokens"].expires_in,
                "user": {
                    "id": result["user"].id,
                    "email": result["user"].email,
                    "created_at": result["user"].created_at.isoformat()
                    if result["user"].created_at
                    else None,
                },
            }
            return response_data
        else:
            # Redirect to frontend with success and tokens for direct browser requests
            success_url = f"{redirect_to or 'http://localhost:8080'}/auth/callback"
            success_url += f"?access_token={result['tokens'].access_token}"
            success_url += f"&refresh_token={result['tokens'].refresh_token}"
            success_url += f"&expires_in={result['tokens'].expires_in}"
            success_url += f"&user_id={result['user'].id}"

            return RedirectResponse(url=success_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        is_frontend_request = (
            request.headers.get("content-type") == "application/json"
            or "fetch" in request.headers.get("user-agent", "").lower()
            or request.headers.get("sec-fetch-mode") == "cors"
        )

        if is_frontend_request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth callback failed",
            )
        else:
            error_url = (
                f"{redirect_to or 'http://localhost:8080'}?error=oauth_callback_failed"
            )
            logger.info(f"Redirecting to error URL: {error_url}")
            return RedirectResponse(url=error_url)


@router.get("/verify")
async def email_verification_callback(
    request: Request,
    token_hash: Optional[str] = None,
    token: Optional[str] = None,
    type: str = "signup",
    email: Optional[str] = None,
    redirect_to: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle email verification callback from Supabase.

    This endpoint is called when users click the verification link in their email.
    """
    try:
        # Validate required parameters
        if not (token_hash or token):
            logger.error("No verification token or token_hash provided")
            frontend_url = settings.frontend_url
            error_url = f"{frontend_url}/auth/callback#error=missing_token"
            return RedirectResponse(url=error_url)

        if not email:
            logger.error("Email address is required for verification")
            frontend_url = settings.frontend_url
            error_url = f"{frontend_url}/auth/callback#error=missing_email"
            return RedirectResponse(url=error_url)

        auth_service = AuthService(db)

        # Use token_hash if available, otherwise use token
        verification_token = token_hash if token_hash else token
        result = await auth_service.handle_email_verification(
            verification_token,
            type,
            email,
            redirect_to,
            use_token_hash=bool(token_hash),
        )

        if result["error"]:
            logger.error(f"Email verification error: {result['error']}")
            # Redirect to frontend with error - use URL fragment to match OAuth callback pattern
            frontend_url = settings.frontend_url
            error_url = f"{frontend_url}/auth/callback#error={result['error']}"
            return RedirectResponse(url=error_url)

        # Redirect to frontend with success and tokens using URL fragment (like OAuth callback)
        frontend_url = settings.frontend_url
        success_url = f"{frontend_url}/auth/callback"
        success_url += f"#access_token={result['tokens'].access_token}"
        success_url += f"&refresh_token={result['tokens'].refresh_token}"
        success_url += f"&expires_in={result['tokens'].expires_in}"
        success_url += f"&token_type=bearer"
        success_url += f"&type=signup"  # This helps frontend detect it's a verification

        return RedirectResponse(url=success_url)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification callback failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        frontend_url = settings.frontend_url
        error_url = f"{frontend_url}/auth/callback#error=email_verification_failed"
        return RedirectResponse(url=error_url)


@router.post("/resend-verification", response_model=SuccessResponse)
async def resend_verification_email(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Resend email verification link.

    Allows users to request a new verification email if they didn't receive it.
    """
    try:
        # Get redirect URL for the verification link - point to backend verification endpoint
        backend_redirect_url = f"{settings.backend_url}/api/v1/auth/verify"

        auth_service = AuthService(db)
        result = await auth_service.resend_verification_email(
            request.email, backend_redirect_url
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        logger.info(f"Verification email resent to: {request.email}")
        return SuccessResponse(
            message=result.get("message", "Verification email sent successfully")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resend verification email endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email",
        )


@router.post("/verify")
async def exchange_supabase_tokens(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Exchange Supabase tokens for backend tokens after email verification.

    This endpoint is called by the frontend when it receives Supabase tokens
    from email verification and needs to exchange them for backend tokens.
    """
    try:
        # Get the request body
        body = await request.json()
        supabase_access_token = body.get("supabase_access_token")
        supabase_refresh_token = body.get("supabase_refresh_token")
        email = body.get("email")

        if not supabase_access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase access token is required",
            )

        # Get user info from Supabase token
        from app.utils.supabase import supabase_client

        supabase_user_response = supabase_client.get_user(supabase_access_token)

        if supabase_user_response.get("error") or not supabase_user_response.get(
            "user"
        ):
            logger.error(
                f"Failed to get user from Supabase: {supabase_user_response.get('error')}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Supabase token",
            )

        supabase_user = supabase_user_response["user"]

        # Get or create local user record
        auth_service = AuthService(db)
        local_user = await auth_service._get_user_by_supabase_id(str(supabase_user.id))

        if not local_user:
            logger.error(
                f"User not found in local database for Supabase ID: {supabase_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in local database",
            )

        # Update user as verified if not already
        if not local_user.is_verified:
            from sqlalchemy import update
            from app.models.user import User

            stmt = update(User).where(User.id == local_user.id).values(is_verified=True)
            await db.execute(stmt)
            await db.commit()
            await db.refresh(local_user)

        # Update last login
        await auth_service._update_last_login(local_user.id)

        # Create backend tokens
        tokens = await auth_service._create_tokens(local_user)

        # Create session in local database
        await auth_service._create_session(
            local_user.id, tokens.access_token, tokens.refresh_token
        )

        logger.info(f"Successfully exchanged tokens for user: {local_user.email}")

        return {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_in": tokens.expires_in,
            "user": {
                "id": str(local_user.id),
                "email": local_user.email,
                "is_verified": local_user.is_verified,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token exchange failed",
        )

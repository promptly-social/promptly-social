"""
Authentication router with endpoints for user management.
Provides API endpoints that mirror the frontend AuthContext functionality.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_db
from app.dependencies import get_current_user
from app.schemas.auth import (
    LinkedInAnalyticsAuthRequest,
    LinkedInAuthRequest,
    RefreshTokenRequest,
    SuccessResponse,
    TokenResponse,
    UserResponse,
    UserUpdate,
)
from app.services.auth import AuthService

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer(auto_error=False)


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
        origin = request.headers.get("origin", settings.frontend_url)

        redirect_to = oauth_request.redirect_to or f"{origin}/auth/callback"

        auth_service = AuthService(db)
        result = await auth_service.initiate_linkedin_native(redirect_to)

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


@router.post("/signin/linkedin-analytics")
async def sign_in_with_linkedin_analytics(
    oauth_request: LinkedInAnalyticsAuthRequest,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Initiate LinkedIn Analytics OAuth for additional scopes.

    This endpoint creates a separate OAuth flow for LinkedIn analytics scopes
    (r_member_postAnalytics, r_member_profileAnalytics) using separate API credentials.
    Requires user to be authenticated.
    """
    try:
        # Get redirect URL from request or use default
        origin = request.headers.get("origin", settings.frontend_url)

        # Create callback URL with origin parameter to determine final redirect
        callback_url = f"{origin}/auth/linkedin-analytics-callback"
        if oauth_request.origin:
            callback_url += f"?origin={oauth_request.origin}"

        auth_service = AuthService(db)
        result = await auth_service.initiate_linkedin_analytics_auth(
            callback_url, oauth_request.origin, current_user.id
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        return {
            "url": result["url"],
            "message": result.get("message", "LinkedIn Analytics OAuth initiated"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LinkedIn Analytics OAuth endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LinkedIn Analytics OAuth failed",
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


@router.get("/linkedin/callback")
async def linkedin_oauth_callback_v2(
    request: Request,
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    New 3-legged LinkedIn OAuth callback.
    """
    try:
        # The redirect_uri must exactly match the one used in the initial auth request
        redirect_uri = f"{settings.frontend_url}/auth/callback"

        auth_service = AuthService(db)
        result = await auth_service.handle_linkedin_callback(
            code, state or "", redirect_uri
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        return {
            "access_token": result["tokens"].access_token,
            "refresh_token": result["tokens"].refresh_token,
            "expires_in": result["tokens"].expires_in,
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LinkedIn OAuth v2 callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth callback failed",
        )


@router.get("/linkedin-analytics/callback")
async def linkedin_analytics_oauth_callback(
    request: Request,
    code: str,
    origin: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """
    LinkedIn Analytics OAuth callback.
    Handles the callback from LinkedIn analytics OAuth and redirects to appropriate page.
    """
    try:
        # The redirect_uri must exactly match the one used in the initial auth request
        callback_url = f"{settings.frontend_url}/auth/linkedin-analytics-callback"
        if origin:
            callback_url += f"?origin={origin}"

        auth_service = AuthService(db)
        result = await auth_service.handle_linkedin_analytics_callback(
            code, state or "", callback_url
        )

        if result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"]
            )

        # Determine redirect destination based on origin
        redirect_path = "/profile"  # default
        if origin == "my-posts":
            redirect_path = "/my-posts"
        elif origin == "profile":
            redirect_path = "/profile"

        return {
            "success": True,
            "message": "LinkedIn Analytics authentication successful",
            "redirect_to": redirect_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LinkedIn Analytics OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LinkedIn Analytics OAuth callback failed",
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

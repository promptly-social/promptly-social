from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.routers.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.profile import (
    PlatformAnalysisResponse,
    SocialConnectionResponse,
    SocialConnectionUpdate,
    SubstackAnalysisResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    WritingStyleAnalysisUpdate,
    LinkedInAuthResponse,
    LinkedInShareRequest,
)
from app.services.profile import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


# User Preferences Endpoints
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get user preferences."""
    try:
        profile_service = ProfileService(db)
        preferences = await profile_service.get_user_preferences(current_user.id)

        if not preferences:
            # Return default preferences
            return UserPreferencesResponse(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                user_id=current_user.id,
                topics_of_interest=[],
                websites=[],
                created_at=current_user.created_at,
                updated_at=current_user.created_at,
            )

        return UserPreferencesResponse.model_validate(preferences)
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user preferences",
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create or update user preferences."""
    try:
        profile_service = ProfileService(db)
        preferences = await profile_service.upsert_user_preferences(
            current_user.id, preferences_data
        )
        return UserPreferencesResponse.model_validate(preferences)
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences",
        )


# Social Connections Endpoints
@router.get("/social-connections", response_model=List[SocialConnectionResponse])
async def get_social_connections(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get all social connections."""
    try:
        profile_service = ProfileService(db)
        connections = await profile_service.get_social_connections(current_user.id)
        return [SocialConnectionResponse.model_validate(conn) for conn in connections]
    except Exception as e:
        logger.error(f"Error getting social connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch social connections",
        )


@router.get("/social-connections/{platform}", response_model=SocialConnectionResponse)
async def get_social_connection(
    platform: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a specific social connection.
    Replaces frontend supabase.from("social_connections").select().eq("platform", platform).
    """
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.get_social_connection(
            current_user.id, platform
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Social connection for {platform} not found",
            )

        return SocialConnectionResponse.model_validate(connection)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting social connection {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch social connection",
        )


@router.put("/social-connections/{platform}", response_model=SocialConnectionResponse)
async def update_social_connection(
    platform: str,
    connection_data: SocialConnectionUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create or update a social connection."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.upsert_social_connection(
            current_user.id, platform, connection_data
        )
        return SocialConnectionResponse.model_validate(connection)
    except Exception as e:
        logger.error(f"Error updating social connection {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update social connection",
        )


# LinkedIn Integration Endpoints
@router.get("/linkedin/auth-info")
async def get_linkedin_auth_info():
    """Get information about the current LinkedIn authentication method."""
    from app.core.config import settings

    return {
        "auth_method": "unipile" if settings.use_unipile_for_linkedin else "native",
        "provider": "Unipile"
        if settings.use_unipile_for_linkedin
        else "LinkedIn OAuth",
        "configured": (
            bool(settings.unipile_dsn and settings.unipile_access_token)
            if settings.use_unipile_for_linkedin
            else bool(settings.linkedin_client_id and settings.linkedin_client_secret)
        ),
    }


@router.get("/linkedin/authorize", response_model=LinkedInAuthResponse)
async def linkedin_authorize(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get LinkedIn authorization URL.

    This endpoint supports both native LinkedIn OAuth and Unipile integration.
    The method used is controlled by the USE_UNIPILE_FOR_LINKEDIN environment variable.

    - Native LinkedIn OAuth: Returns standard LinkedIn OAuth authorization URL
    - Unipile: Returns Unipile hosted auth wizard URL for LinkedIn
    """
    try:
        # Using a simple state for now, but should be more robust in production
        state = "linkedin_oauth_state_" + current_user.id.hex
        profile_service = ProfileService(db)
        auth_url = profile_service.create_linkedin_authorization_url(state)
        return LinkedInAuthResponse(authorization_url=auth_url)
    except Exception as e:
        logger.error(f"Error creating LinkedIn auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create LinkedIn authorization URL",
        )


@router.post("/linkedin/unipile-callback")
async def linkedin_unipile_callback(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """Handle Unipile webhook callback when user connects LinkedIn account."""
    try:
        body = await request.json()
        logger.info(f"Received Unipile callback: {body}")

        # Extract data from Unipile webhook
        status = body.get("status")
        account_id = body.get("account_id")
        name = body.get("name")  # This is our state value

        if status != "CREATION_SUCCESS":
            logger.warning(f"Unipile callback with non-success status: {status}")
            return {"status": "ignored", "reason": f"Non-success status: {status}"}

        if not account_id or not name:
            logger.error("Missing account_id or name in Unipile callback")
            return {"status": "error", "reason": "Missing required fields"}

        # Extract user_id from the state/name
        if not name.startswith("linkedin_oauth_state_"):
            logger.error(f"Invalid state format in Unipile callback: {name}")
            return {"status": "error", "reason": "Invalid state format"}

        user_id_hex = name.replace("linkedin_oauth_state_", "")
        try:
            user_id = UUID(user_id_hex.replace("-", ""))
        except ValueError:
            logger.error(f"Invalid user ID in state: {user_id_hex}")
            return {"status": "error", "reason": "Invalid user ID"}

        # Store the connection with all auth data in connection_data JSON
        profile_service = ProfileService(db)

        connection_data = SocialConnectionUpdate(
            platform_username="LinkedIn User",  # Will be updated when we fetch account details
            is_active=True,
            connection_data={
                "auth_method": "unipile",
                "account_id": account_id,
                "unipile_account_id": account_id,  # Keep both for backward compatibility
                "status": "connected",
                "provider": "linkedin",
                # Additional webhook data
                "webhook_status": status,
                "webhook_data": body,
            },
        )

        await profile_service.upsert_social_connection(
            user_id, "linkedin", connection_data
        )

        logger.info(f"Successfully processed Unipile callback for user {user_id}")
        return {"status": "success", "account_id": account_id}

    except Exception as e:
        logger.error(f"Error processing Unipile callback: {e}")
        return {"status": "error", "reason": str(e)}


@router.get("/linkedin/callback", response_model=SocialConnectionResponse)
async def linkedin_callback(
    code: str,
    state: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Handle LinkedIn callback, exchange code for token, and store connection.

    This endpoint handles callbacks from both native LinkedIn OAuth and Unipile:
    - Native LinkedIn OAuth: 'code' is the authorization code from LinkedIn
    - Unipile: 'code' is the account_id returned from Unipile's auth flow (deprecated - use webhook)

    Note: For Unipile, this endpoint may not be called as Unipile uses webhooks.
    The frontend should poll the connection status or listen for real-time updates.
    """
    try:
        # Validate state to prevent CSRF attacks
        expected_state = "linkedin_oauth_state_" + current_user.id.hex
        if state != expected_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        profile_service = ProfileService(db)

        # Check if this is a native LinkedIn callback or if we already have a Unipile connection
        from app.core.config import settings

        if settings.use_unipile_for_linkedin:
            # For Unipile, check if we already have a connection from the webhook
            existing_connection = (
                await profile_service.get_social_connection_for_analysis(
                    current_user.id, "linkedin"
                )
            )
            if (
                existing_connection
                and existing_connection.connection_data.get("auth_method") == "unipile"
            ):
                return SocialConnectionResponse.model_validate(existing_connection)
            else:
                # Fallback: treat code as account_id for backward compatibility
                logger.warning(
                    "Unipile callback received at OAuth endpoint - using fallback handling"
                )
                connection = await profile_service._exchange_unipile_linkedin_code(
                    code, current_user.id
                )
                return SocialConnectionResponse.model_validate(connection)
        else:
            # Native LinkedIn OAuth flow
            connection = await profile_service.exchange_linkedin_code_for_token(
                code, current_user.id
            )
            return SocialConnectionResponse.model_validate(connection)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in LinkedIn callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process LinkedIn callback",
        )


@router.post("/linkedin/share")
async def share_on_linkedin(
    share_request: LinkedInShareRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Share a post on LinkedIn.

    This endpoint supports sharing via both native LinkedIn API and Unipile:
    - Native LinkedIn OAuth: Uses LinkedIn's ugcPosts API
    - Unipile: Uses Unipile's unified messaging API

    The method used depends on how the user's LinkedIn connection was established.
    """
    try:
        profile_service = ProfileService(db)
        result = await profile_service.share_on_linkedin(
            current_user.id, share_request.text
        )
        return result
    except ValueError as e:
        logger.error(f"Value error sharing to LinkedIn: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error sharing to LinkedIn: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to share on LinkedIn",
        )


@router.get("/linkedin/unipile-accounts")
async def get_unipile_accounts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get all Unipile accounts (only available when USE_UNIPILE_FOR_LINKEDIN=true).

    This endpoint lists all connected accounts in your Unipile workspace,
    useful for debugging and administration.
    """
    from app.core.config import settings

    if not settings.use_unipile_for_linkedin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only available when using Unipile for LinkedIn integration",
        )

    try:
        profile_service = ProfileService(db)
        accounts = await profile_service.get_unipile_accounts()
        return {"accounts": accounts}
    except ValueError as e:
        logger.error(f"Value error getting Unipile accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error getting Unipile accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Unipile accounts",
        )


# Substack Analysis Endpoints
@router.get("/substack-analysis", response_model=SubstackAnalysisResponse)
async def get_substack_analysis(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get Substack analysis data."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.get_social_connection_for_analysis(
            current_user.id, "substack"
        )

        if not connection:
            return SubstackAnalysisResponse(
                is_connected=False,
                analyzed_at=None,
                analysis_started_at=None,
                analysis_completed_at=None,
                is_analyzing=False,
            )

        # Prepare response based on current connection state
        analyzed_at = None
        analysis_started_at = (
            connection.analysis_started_at.isoformat()
            if connection.analysis_started_at
            else None
        )
        analysis_completed_at = (
            connection.analysis_completed_at.isoformat()
            if connection.analysis_completed_at
            else None
        )
        is_analyzing = (
            connection.analysis_started_at is not None
            and connection.analysis_completed_at is None
        )

        # Check for new analysis results
        if (
            connection.connection_data
            and "analysis_result" in connection.connection_data
        ):
            analyzed_at = analysis_completed_at

        return SubstackAnalysisResponse(
            is_connected=True,
            analyzed_at=analyzed_at,
            analysis_started_at=analysis_started_at,
            analysis_completed_at=analysis_completed_at,
            is_analyzing=is_analyzing,
        )

    except Exception as e:
        logger.error(f"Error getting Substack analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Substack analysis",
        )


@router.post("/analyze-substack", response_model=SubstackAnalysisResponse)
async def run_substack_analysis(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run Substack analysis for the user to analyze their bio and interests."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.analyze_substack(
            current_user.id, ["bio", "interests"]
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Substack connection not found or not configured for analysis",
            )

        # Re-fetch the data to populate the response model
        analysis_data = await get_substack_analysis(current_user, db)
        analysis_data.is_analyzing = True
        return analysis_data

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error running Substack analysis: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error running Substack analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run Substack analysis: {e}",
        )


@router.post(
    "/analyze-linkedin", response_model=SubstackAnalysisResponse
)  # Using SubstackAnalysisResponse for now, TODO: Create LinkedInAnalysisResponse
async def run_linkedin_analysis(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run LinkedIn analysis for the user to analyze their bio and writing style."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.analyze_linkedin(
            current_user.id, ["bio", "writing_style"]
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LinkedIn connection not found or not configured for analysis",
            )

        # Return analysis status - TODO: Implement proper LinkedIn analysis response
        return SubstackAnalysisResponse(
            is_connected=True,
            analyzed_at=None,
            analysis_started_at=connection.analysis_started_at.isoformat()
            if connection.analysis_started_at
            else None,
            analysis_completed_at=connection.analysis_completed_at.isoformat()
            if connection.analysis_completed_at
            else None,
            is_analyzing=True,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error running LinkedIn analysis: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error running LinkedIn analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run LinkedIn analysis: {e}",
        )


# Writing Style Analysis Endpoints
@router.post("/writing-analysis/{source}", response_model=PlatformAnalysisResponse)
async def run_writing_style_analysis(
    source: str,
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run writing style analysis for a platform."""
    try:
        profile_service = ProfileService(db)

        # Special handling for importing manual text samples
        if source == "import":
            body = await request.json()
            text = body.get("text") if isinstance(body, dict) else None
            if not text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="`text` field is required when source is 'import'",
                )

            # Call the cloud function for import analysis
            await profile_service.analyze_import_sample(
                current_user.id, text, ["writing_style"]
            )

            # Return the updated analysis
            analysis = await profile_service.get_latest_writing_style_analysis(
                current_user.id
            )

            if analysis:
                return PlatformAnalysisResponse(
                    analysis_data=analysis.analysis_data,
                    last_analyzed=analysis.last_analyzed_at.isoformat()
                    if analysis.last_analyzed_at
                    else analysis.updated_at.isoformat(),
                    is_connected=True,
                )
            else:
                return PlatformAnalysisResponse(
                    analysis_data=None,
                    last_analyzed=None,
                    is_connected=True,
                )

        elif source == "substack":
            profile_service = ProfileService(db)
            connection = await profile_service.analyze_substack(
                current_user.id, ["writing_style"]
            )

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Substack connection not found or not configured for analysis",
                )

            # Re-fetch the data to populate the response model
            analysis_data = await get_substack_analysis(current_user, db)
            analysis_data.is_analyzing = True
            return analysis_data

        elif source == "linkedin":
            # Run LinkedIn writing style analysis
            connection = await profile_service.analyze_linkedin(
                current_user.id, ["writing_style"]
            )

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="LinkedIn connection not found or not configured for analysis",
                )

            return PlatformAnalysisResponse(
                analysis_data=None,
                last_analyzed=None,
                is_connected=True,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid source: {source}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running writing style analysis {source}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run writing style analysis",
        )


@router.get("/writing-analysis", response_model=PlatformAnalysisResponse)
async def get_latest_writing_style_analysis(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Return the most recent writing style analysis for the user, regardless of source."""
    try:
        profile_service = ProfileService(db)
        analysis = await profile_service.get_latest_writing_style_analysis(
            current_user.id
        )

        if analysis:
            return PlatformAnalysisResponse(
                analysis_data=analysis.analysis_data,
                last_analyzed=analysis.last_analyzed_at.isoformat()
                if analysis.last_analyzed_at
                else analysis.updated_at.isoformat(),
                is_connected=True,
            )
        else:
            # No analysis yet – return empty payload
            return PlatformAnalysisResponse(
                analysis_data=None, last_analyzed=None, is_connected=False
            )

    except Exception as e:
        logger.error(f"Error getting consolidated writing style analysis for user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch writing style analysis",
        )


@router.put("/writing-analysis", response_model=PlatformAnalysisResponse)
async def update_latest_writing_style_analysis(
    update_data: WritingStyleAnalysisUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update the most recent writing style analysis for the user. If none exists, one is created using a default 'import' source."""
    try:
        profile_service = ProfileService(db)

        # Find the current analysis (if any) to determine source
        existing = await profile_service.get_latest_writing_style_analysis(
            current_user.id
        )

        # Fallback source if there is no previous record
        source = existing.source if existing else "import"

        if update_data.analysis_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="analysis_data is required for update",
            )

        analysis = await profile_service.upsert_writing_style_analysis(
            current_user.id, source, update_data.analysis_data
        )

        return PlatformAnalysisResponse(
            analysis_data=analysis.analysis_data,
            last_analyzed=analysis.last_analyzed_at.isoformat(),
            is_connected=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating consolidated writing style analysis for user: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update writing style analysis",
        )


@router.get("/linkedin/connection-status/{state}")
async def check_linkedin_connection_status(
    state: str,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Check if a LinkedIn connection was established for a given state.
    This endpoint doesn't require authentication and is used by the frontend
    to check if a Unipile webhook was processed successfully.
    """
    try:
        # Extract user_id from the state
        if not state.startswith("linkedin_oauth_state_"):
            return {"connected": False, "error": "Invalid state format"}

        user_id_hex = state.replace("linkedin_oauth_state_", "")
        try:
            user_id = UUID(user_id_hex.replace("-", ""))
        except ValueError:
            return {"connected": False, "error": "Invalid user ID"}

        # Check if a LinkedIn connection exists for this user
        profile_service = ProfileService(db)
        connection = await profile_service.get_social_connection_for_analysis(
            user_id, "linkedin"
        )

        if connection and connection.connection_data:
            auth_method = connection.connection_data.get("auth_method")
            if auth_method == "unipile" and connection.is_active:
                return {
                    "connected": True,
                    "auth_method": "unipile",
                    "account_id": connection.connection_data.get("account_id"),
                }

        return {"connected": False}

    except Exception as e:
        logger.error(f"Error checking connection status: {e}")
        return {"connected": False, "error": str(e)}

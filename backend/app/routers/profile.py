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
@router.get("/linkedin/authorize", response_model=LinkedInAuthResponse)
async def linkedin_authorize(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get LinkedIn authorization URL."""
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


@router.get("/linkedin/callback", response_model=SocialConnectionResponse)
async def linkedin_callback(
    code: str,
    state: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Handle LinkedIn callback, exchange code for token, and store connection."""
    try:
        # Validate state to prevent CSRF attacks
        expected_state = "linkedin_oauth_state_" + current_user.id.hex
        if state != expected_state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        profile_service = ProfileService(db)
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
    """Share a post on LinkedIn."""
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

            # TODO: Implement real analysis logic for free-form text
            mock_analysis_data = text  # For now just echo back

            analysis = await profile_service.upsert_writing_style_analysis(
                current_user.id, source, mock_analysis_data
            )

            return PlatformAnalysisResponse(
                analysis_data=analysis.analysis_data,
                last_analyzed=analysis.last_analyzed_at.isoformat(),
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
            # For linked platforms (linkedin, substack) ensure connection exists
            connection = await profile_service.get_social_connection(
                current_user.id, "linkedin"
            )

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Social connection for {source} not found",
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

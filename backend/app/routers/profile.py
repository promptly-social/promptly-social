from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
    SubstackConnectionData,
    SubstackData,
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


# Writing Style Analysis Endpoints
@router.get("/writing-analysis/{platform}", response_model=PlatformAnalysisResponse)
async def get_writing_style_analysis(
    platform: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get writing style analysis for a platform."""
    try:
        profile_service = ProfileService(db)

        # Check connection
        connection = await profile_service.get_social_connection(
            current_user.id, platform
        )
        is_connected = connection is not None

        # Get analysis
        analysis = await profile_service.get_writing_style_analysis(
            current_user.id, platform
        )

        if analysis:
            return PlatformAnalysisResponse(
                analysis_data=analysis.analysis_data,
                last_analyzed=analysis.last_analyzed_at.isoformat(),
                is_connected=is_connected,
            )
        else:
            return PlatformAnalysisResponse(
                analysis_data=None, last_analyzed=None, is_connected=is_connected
            )

    except Exception as e:
        logger.error(f"Error getting writing style analysis {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch writing style analysis",
        )


@router.post("/writing-analysis/{platform}", response_model=PlatformAnalysisResponse)
async def run_writing_style_analysis(
    platform: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run writing style analysis for a platform."""
    try:
        profile_service = ProfileService(db)

        # Check connection
        connection = await profile_service.get_social_connection(
            current_user.id, platform
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Social connection for {platform} not found",
            )

        # For now, create a mock analysis - in real implementation this would trigger actual analysis
        mock_analysis_data = f"Writing style analysis for {platform} - placeholder data"

        # Create or update analysis
        analysis = await profile_service.upsert_writing_style_analysis(
            current_user.id, platform, mock_analysis_data
        )

        return PlatformAnalysisResponse(
            analysis_data=analysis.analysis_data,
            last_analyzed=analysis.last_analyzed_at.isoformat(),
            is_connected=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running writing style analysis {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run writing style analysis",
        )


@router.put("/writing-analysis/{platform}", response_model=PlatformAnalysisResponse)
async def update_writing_style_analysis(
    platform: str,
    update_data: WritingStyleAnalysisUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update writing style analysis for a platform."""
    try:
        profile_service = ProfileService(db)

        # Check if analysis exists
        existing_analysis = await profile_service.get_writing_style_analysis(
            current_user.id, platform
        )

        if not existing_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Writing style analysis for {platform} not found",
            )

        # Update analysis data if provided
        if update_data.analysis_data is not None:
            analysis = await profile_service.upsert_writing_style_analysis(
                current_user.id, platform, update_data.analysis_data
            )

            # Check connection status
            connection = await profile_service.get_social_connection(
                current_user.id, platform
            )
            is_connected = connection is not None

            return PlatformAnalysisResponse(
                analysis_data=analysis.analysis_data,
                last_analyzed=analysis.last_analyzed_at.isoformat(),
                is_connected=is_connected,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="analysis_data is required for update",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating writing style analysis {platform}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update writing style analysis",
        )


# LinkedIn Integration Endpoints
@router.get("/linkedin/authorize", response_model=LinkedInAuthResponse)
async def linkedin_authorize(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get LinkedIn authorization URL."""
    try:
        logger.info(
            "Executing linkedin_authorize with defensive string casting. Version: 2."
        )
        # Ensure user_id is a string before concatenation
        user_id_str = str(current_user.id)
        state = f"linkedin_oauth_state_{user_id_str}"
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
        user_id_str = str(current_user.id)
        expected_state = f"linkedin_oauth_state_{user_id_str}"
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
                substack_data=[],
                is_connected=False,
                analyzed_at=None,
                analysis_started_at=None,
                analysis_completed_at=None,
                is_analyzing=False,
            )

        # Prepare response based on current connection state
        substack_data = []
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
            analysis_result = connection.connection_data["analysis_result"]

            # Convert analysis result to SubstackData format
            substack_data = [
                SubstackData(
                    name=connection.platform_username or "Unknown",
                    url=f"https://{connection.platform_username}.substack.com"
                    if connection.platform_username
                    else "",
                    topics=analysis_result.get("topics", []),
                    subscriber_count=analysis_result.get("subscriber_insights", {}).get(
                        "estimated_subscribers"
                    ),
                    recent_posts=analysis_result.get("recent_posts", []),
                )
            ]
            analyzed_at = analysis_completed_at

        # Check for legacy format (for backward compatibility)
        elif (
            connection.connection_data and "substackData" in connection.connection_data
        ):
            try:
                connection_data = SubstackConnectionData(**connection.connection_data)
                substack_data = connection_data.substackData
                analyzed_at = connection_data.analyzed_at
            except Exception as e:
                logger.warning(f"Failed to parse legacy substack data: {e}")

        return SubstackAnalysisResponse(
            substack_data=substack_data,
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
    """Run Substack analysis."""
    try:
        profile_service = ProfileService(db)

        # Start the analysis
        connection = await profile_service.analyze_substack(current_user.id)

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Substack connection not found or not configured",
            )

        # Prepare response based on current connection state
        substack_data = []
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

        # If analysis is completed, extract the data
        if (
            connection.connection_data
            and "analysis_result" in connection.connection_data
        ):
            analysis_result = connection.connection_data["analysis_result"]

            # Convert analysis result to SubstackData format
            substack_data = [
                SubstackData(
                    name=connection.platform_username or "Unknown",
                    url=f"https://{connection.platform_username}.substack.com"
                    if connection.platform_username
                    else "",
                    topics=analysis_result.get("topics", []),
                    subscriber_count=analysis_result.get("subscriber_insights", {}).get(
                        "estimated_subscribers"
                    ),
                    recent_posts=analysis_result.get("recent_posts", []),
                )
            ]
            analyzed_at = analysis_completed_at

        return SubstackAnalysisResponse(
            substack_data=substack_data,
            is_connected=True,
            analyzed_at=analyzed_at,
            analysis_started_at=analysis_started_at,
            analysis_completed_at=analysis_completed_at,
            is_analyzing=is_analyzing,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running Substack analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run Substack analysis",
        )

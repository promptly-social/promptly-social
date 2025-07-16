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
    AnalysisRequest,
)
from app.schemas.content_strategies import ContentStrategyResponse
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
        content_strategies = await profile_service.get_content_strategies(
            current_user.id
        )

        if not preferences:
            # Ensure default LinkedIn strategy exists
            if not any(s.platform == "linkedin" for s in content_strategies):
                await profile_service.create_default_linkedin_strategy(current_user.id)
                content_strategies = await profile_service.get_content_strategies(
                    current_user.id
                )

            # Return default preferences
            return UserPreferencesResponse(
                id=UUID("00000000-0000-0000-0000-000000000000"),
                user_id=current_user.id,
                topics_of_interest=[],
                websites=[],
                substacks=[],
                preferred_posting_time=None,
                timezone=None,
                created_at=current_user.created_at,
                updated_at=current_user.created_at,
                content_strategies=[
                    ContentStrategyResponse.model_validate(cs)
                    for cs in content_strategies
                ],
            )

        # Handle None values for new fields added via migration
        if preferences.substacks is None:
            preferences.substacks = []
        if preferences.bio is None:
            preferences.bio = ""

        # Ensure default LinkedIn strategy exists
        if not any(s.platform == "linkedin" for s in content_strategies):
            await profile_service.create_default_linkedin_strategy(current_user.id)
            content_strategies = await profile_service.get_content_strategies(
                current_user.id
            )

        # Create response with content strategies
        response_data = UserPreferencesResponse.model_validate(preferences)
        response_data.content_strategies = [
            ContentStrategyResponse.model_validate(cs) for cs in content_strategies
        ]

        return response_data
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
        content_strategies = await profile_service.get_content_strategies(
            current_user.id
        )

        # Handle None values for new fields added via migration
        if preferences.substacks is None:
            preferences.substacks = []
        if preferences.bio is None:
            preferences.bio = ""

        # Create response with content strategies
        response_data = UserPreferencesResponse.model_validate(preferences)
        response_data.content_strategies = [
            ContentStrategyResponse.model_validate(cs) for cs in content_strategies
        ]

        return response_data
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
    request: AnalysisRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run Substack analysis for the user to analyze their bio and interests."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.analyze_substack(
            current_user.id, request.content_to_analyze
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
    request: AnalysisRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run LinkedIn analysis for the user to analyze their bio and writing style."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.analyze_linkedin(
            current_user.id, request.content_to_analyze
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
            return {"connected": True}
        return {"connected": False}

    except Exception as e:
        logger.error(f"Error checking connection status: {e}")
        return {"connected": False, "error": str(e)}

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.profile import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
    SocialConnectionResponse,
    SocialConnectionUpdate,
    PlatformAnalysisResponse,
    PlatformAnalysisData,
    SubstackAnalysisResponse,
    SubstackConnectionData,
    SubstackData,
    WritingStyleAnalysisUpdate,
)
from app.services.profile import ProfileService
from app.schemas.auth import UserResponse
from app.core.database import get_async_db
from app.routers.auth import get_current_user
from loguru import logger
from datetime import datetime
from uuid import UUID


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
                analysis_data=PlatformAnalysisData(**analysis.analysis_data),
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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please connect your {platform} account first",
            )

        # Sample analysis data
        sample_analysis = {
            "writing_style": {
                "tone": "Professional" if platform == "linkedin" else "Conversational",
                "complexity": "Intermediate",
                "avg_length": 150 if platform == "linkedin" else 800,
                "key_themes": (
                    ["Professional Growth", "Industry Insights", "Leadership"]
                    if platform == "linkedin"
                    else ["Deep Dives", "Analysis", "Commentary"]
                ),
            },
            "topics": (
                ["Technology", "Business Strategy", "Leadership", "Innovation"]
                if platform == "linkedin"
                else [
                    "Technology",
                    "Startups",
                    "Product Development",
                    "Industry Analysis",
                ]
            ),
            "posting_patterns": {
                "frequency": "Weekly",
                "best_times": ["9:00 AM", "1:00 PM", "5:00 PM"],
            },
            "engagement_insights": {
                "high_performing_topics": ["AI", "Remote Work", "Leadership"],
                "content_types": ["Insights", "Personal Stories", "Industry Updates"],
            },
        }

        # Save analysis
        analysis_update = WritingStyleAnalysisUpdate(
            analysis_data=sample_analysis, content_count=25
        )

        analysis = await profile_service.upsert_writing_style_analysis(
            current_user.id, platform, analysis_update
        )

        return PlatformAnalysisResponse(
            analysis_data=PlatformAnalysisData(**analysis.analysis_data),
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


# Substack Analysis Endpoints
@router.get("/substack-analysis", response_model=SubstackAnalysisResponse)
async def get_substack_analysis(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get Substack analysis data."""
    try:
        profile_service = ProfileService(db)
        connection = await profile_service.get_social_connection(
            current_user.id, "substack"
        )

        if not connection or not connection.connection_data:
            return SubstackAnalysisResponse(
                substack_data=[], is_connected=False, analyzed_at=None
            )

        connection_data = SubstackConnectionData(**connection.connection_data)

        return SubstackAnalysisResponse(
            substack_data=connection_data.substackData,
            is_connected=True,
            analyzed_at=connection_data.analyzed_at,
        )

    except Exception as e:
        logger.error(f"Error getting Substack analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Substack analysis",
        )


@router.post("/substack-analysis", response_model=SubstackAnalysisResponse)
async def run_substack_analysis(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Run Substack analysis."""
    try:
        profile_service = ProfileService(db)

        # Sample Substack data
        sample_substack_data = [
            SubstackData(
                name="The Tech Observer",
                url="https://techobserver.substack.com",
                topics=["Technology", "AI", "Startups", "Innovation"],
                subscriber_count=12500,
                recent_posts=[
                    {
                        "title": "The Rise of AI Agents in 2024",
                        "url": "https://techobserver.substack.com/p/ai-agents-2024",
                        "published_date": "2024-01-15",
                    }
                ],
            )
        ]

        # Update connection
        connection_data = SubstackConnectionData(
            substackData=sample_substack_data, analyzed_at=datetime.utcnow().isoformat()
        )

        connection_update = SocialConnectionUpdate(
            is_active=True, connection_data=connection_data.model_dump()
        )

        await profile_service.upsert_social_connection(
            current_user.id, "substack", connection_update
        )

        return SubstackAnalysisResponse(
            substack_data=sample_substack_data,
            is_connected=True,
            analyzed_at=connection_data.analyzed_at,
        )

    except Exception as e:
        logger.error(f"Error running Substack analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run Substack analysis",
        )

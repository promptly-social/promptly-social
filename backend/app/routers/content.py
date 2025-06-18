"""
Content router with endpoints for content management.
Replaces all frontend direct Supabase calls with backend API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.core.database import get_async_db
from app.services.content import ContentService
from app.routers.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.content import (
    ContentIdeaCreate,
    ContentIdeaUpdate,
    ContentIdeaResponse,
    ContentIdeaListResponse,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    SocialConnectionUpdate,
    SocialConnectionResponse,
    WritingStyleAnalysisUpdate,
    PlatformAnalysisResponse,
    SubstackAnalysisResponse,
    PlatformAnalysisData,
    SubstackData,
    SubstackConnectionData,
)

# Create router
router = APIRouter(prefix="/content", tags=["content"])


# Content Ideas Endpoints
@router.get("/ideas", response_model=ContentIdeaListResponse)
async def get_content_ideas(
    idea_status: Optional[List[str]] = Query(None, alias="status"),
    content_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get content ideas with filtering and pagination."""
    try:
        content_service = ContentService(db)
        result = await content_service.get_content_ideas(
            user_id=current_user.id,
            status=idea_status,
            content_type=content_type,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
        )
        return ContentIdeaListResponse(**result)
    except Exception as e:
        logger.error(f"Error getting content ideas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content ideas",
        )


@router.get("/ideas/{content_id}", response_model=ContentIdeaResponse)
async def get_content_idea(
    content_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a specific content idea.
    Replaces frontend supabase.from("content_ideas").select().eq("id", id).
    """
    try:
        content_service = ContentService(db)
        content_idea = await content_service.get_content_idea(
            current_user.id, content_id
        )

        if not content_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content idea not found"
            )

        return ContentIdeaResponse.model_validate(content_idea)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content idea {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content idea",
        )


@router.post(
    "/ideas", response_model=ContentIdeaResponse, status_code=status.HTTP_201_CREATED
)
async def create_content_idea(
    content_data: ContentIdeaCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new content idea.
    Replaces frontend supabase.from("content_ideas").insert().
    """
    try:
        content_service = ContentService(db)
        content_idea = await content_service.create_content_idea(
            current_user.id, content_data
        )
        return ContentIdeaResponse.model_validate(content_idea)
    except Exception as e:
        logger.error(f"Error creating content idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create content idea",
        )


@router.put("/ideas/{content_id}", response_model=ContentIdeaResponse)
async def update_content_idea(
    content_id: UUID,
    update_data: ContentIdeaUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a content idea."""
    try:
        content_service = ContentService(db)
        content_idea = await content_service.update_content_idea(
            current_user.id, content_id, update_data
        )

        if not content_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content idea not found"
            )

        return ContentIdeaResponse.model_validate(content_idea)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content idea {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content idea",
        )


@router.delete("/ideas/{content_id}")
async def delete_content_idea(
    content_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a content idea.
    Replaces frontend supabase.from("content_ideas").delete().eq("id", id).
    """
    try:
        content_service = ContentService(db)
        deleted = await content_service.delete_content_idea(current_user.id, content_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content idea not found"
            )

        return {"message": "Content idea deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content idea {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete content idea",
        )


# User Preferences Endpoints
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get user preferences."""
    try:
        content_service = ContentService(db)
        preferences = await content_service.get_user_preferences(current_user.id)

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
        content_service = ContentService(db)
        preferences = await content_service.upsert_user_preferences(
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
        content_service = ContentService(db)
        connections = await content_service.get_social_connections(current_user.id)
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
        content_service = ContentService(db)
        connection = await content_service.get_social_connection(
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
        content_service = ContentService(db)
        connection = await content_service.upsert_social_connection(
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
        content_service = ContentService(db)

        # Check connection
        connection = await content_service.get_social_connection(
            current_user.id, platform
        )
        is_connected = connection is not None

        # Get analysis
        analysis = await content_service.get_writing_style_analysis(
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
        content_service = ContentService(db)

        # Check connection
        connection = await content_service.get_social_connection(
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

        analysis = await content_service.upsert_writing_style_analysis(
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
        content_service = ContentService(db)
        connection = await content_service.get_social_connection(
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
        content_service = ContentService(db)

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

        await content_service.upsert_social_connection(
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

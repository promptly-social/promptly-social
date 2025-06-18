"""
Content router with endpoints for content management.
Replaces all frontend direct Supabase calls with backend API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from typing import Optional, List
from uuid import UUID

from app.core.database import get_async_db
from app.services.content import ContentService
from app.routers.auth import get_current_user
from app.schemas.auth import UserResponse
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentListResponse,
    PublicationCreate,
    PublicationUpdate,
    PublicationResponse,
)

# Create router
router = APIRouter(prefix="/content", tags=["content"])


# Content Endpoints
@router.get("/", response_model=ContentListResponse)
async def get_content_list(
    content_status: Optional[List[str]] = Query(None, alias="status"),
    content_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get content with filtering and pagination."""
    try:
        content_service = ContentService(db)
        result = await content_service.get_content_list(
            user_id=current_user.id,
            status=content_status,
            content_type=content_type,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
        )
        return ContentListResponse(**result)
    except Exception as e:
        logger.error(f"Error getting content list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content",
        )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get a specific content item.
    Replaces frontend supabase.from("contents").select().eq("id", id).
    """
    try:
        content_service = ContentService(db)
        content = await content_service.get_content(current_user.id, content_id)

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        # Create response without publications to avoid greenlet issues
        content_dict = {
            "id": content.id,
            "user_id": content.user_id,
            "title": content.title,
            "original_input": content.original_input,
            "generated_outline": content.generated_outline,
            "content_type": content.content_type,
            "status": content.status,
            "created_at": content.created_at,
            "updated_at": content.updated_at,
            "publications": None,
        }
        return ContentResponse(**content_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting content {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch content",
        )


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Create a new content item.
    Replaces frontend supabase.from("contents").insert().
    """
    try:
        content_service = ContentService(db)
        content = await content_service.create_content(current_user.id, content_data)
        # Create response without publications to avoid greenlet issues
        content_dict = {
            "id": content.id,
            "user_id": content.user_id,
            "title": content.title,
            "original_input": content.original_input,
            "generated_outline": content.generated_outline,
            "content_type": content.content_type,
            "status": content.status,
            "created_at": content.created_at,
            "updated_at": content.updated_at,
            "publications": None,
        }
        return ContentResponse(**content_dict)
    except Exception as e:
        logger.error(f"Error creating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create content",
        )


@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: UUID,
    update_data: ContentUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a content item."""
    try:
        content_service = ContentService(db)
        content = await content_service.update_content(
            current_user.id, content_id, update_data
        )

        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        # Create response without publications to avoid greenlet issues
        content_dict = {
            "id": content.id,
            "user_id": content.user_id,
            "title": content.title,
            "original_input": content.original_input,
            "generated_outline": content.generated_outline,
            "content_type": content.content_type,
            "status": content.status,
            "created_at": content.created_at,
            "updated_at": content.updated_at,
            "publications": None,
        }
        return ContentResponse(**content_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update content",
        )


@router.delete("/{content_id}")
async def delete_content(
    content_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a content item.
    Replaces frontend supabase.from("contents").delete().eq("id", id).
    """
    try:
        content_service = ContentService(db)
        deleted = await content_service.delete_content(current_user.id, content_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Content not found"
            )

        return {"message": "Content deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete content",
        )


# Publication Endpoints
@router.post(
    "/publications",
    response_model=PublicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_publication(
    publication_data: PublicationCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new publication for a content item."""
    try:
        content_service = ContentService(db)
        publication = await content_service.create_publication(
            current_user.id, publication_data
        )
        return PublicationResponse.model_validate(publication)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating publication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create publication",
        )


@router.put("/publications/{publication_id}", response_model=PublicationResponse)
async def update_publication(
    publication_id: UUID,
    update_data: PublicationUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a publication."""
    try:
        content_service = ContentService(db)
        publication = await content_service.update_publication(
            current_user.id, publication_id, update_data
        )

        if not publication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found"
            )

        return PublicationResponse.model_validate(publication)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating publication {publication_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update publication",
        )


@router.delete("/publications/{publication_id}")
async def delete_publication(
    publication_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a publication."""
    try:
        content_service = ContentService(db)
        deleted = await content_service.delete_publication(
            current_user.id, publication_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found"
            )

        return {"message": "Publication deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting publication {publication_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete publication",
        )


@router.get("/{content_id}/publications", response_model=List[PublicationResponse])
async def get_content_publications(
    content_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get all publications for a content item."""
    try:
        content_service = ContentService(db)
        publications = await content_service.get_publications_by_content(
            current_user.id, content_id
        )
        return [PublicationResponse.model_validate(pub) for pub in publications]
    except Exception as e:
        logger.error(f"Error getting publications for content {content_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch publications",
        )

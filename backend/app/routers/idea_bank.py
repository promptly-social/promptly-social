"""
Idea Bank router with endpoints for idea bank management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.dependencies import get_current_user_with_rls as get_current_user
from app.schemas.auth import UserResponse
from app.schemas.idea_bank import (
    IdeaBankCreate,
    IdeaBankListResponse,
    IdeaBankResponse,
    IdeaBankUpdate,
)
from app.services.idea_bank import IdeaBankService

# Create router
router = APIRouter(prefix="/idea-banks", tags=["idea-banks"])


@router.get("/", response_model=IdeaBankListResponse)
async def get_idea_bank_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("updated_at"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    ai_suggested: Optional[bool] = Query(
        None, description="Filter by AI suggested ideas"
    ),
    has_post: Optional[bool] = Query(
        None, description="Filter by whether the idea has associated posts"
    ),
    post_status: Optional[List[str]] = Query(
        None, description="Filter by status of associated posts"
    ),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get idea banks with filtering and pagination."""
    try:
        idea_bank_service = IdeaBankService(db)
        result = await idea_bank_service.get_idea_banks_list(
            user_id=current_user.id,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
            has_post=has_post,
            post_status=post_status[0]
            if post_status and len(post_status) > 0
            else None,
        )
        return IdeaBankListResponse(**result)
    except Exception as e:
        logger.error(f"Error getting idea bank list: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch idea banks",
        )


@router.get("/with-posts")
async def get_idea_banks_with_latest_posts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    order_by: str = Query("updated_at"),
    order_direction: str = Query("desc", pattern="^(asc|desc)$"),
    ai_suggested: Optional[bool] = Query(
        None, description="Filter by AI suggested ideas"
    ),
    has_post: Optional[bool] = Query(
        None, description="Filter by whether the idea has associated posts"
    ),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get idea banks with their latest suggested posts."""
    try:
        idea_bank_service = IdeaBankService(db)
        result = await idea_bank_service.get_idea_banks_with_latest_posts(
            user_id=current_user.id,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
            ai_suggested=ai_suggested,
            has_post=has_post,
        )
        return result
    except Exception as e:
        logger.error(f"Error getting idea banks with latest posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch idea banks with posts",
        )


@router.get("/batch", response_model=List[IdeaBankResponse])
async def get_idea_banks_batch(
    ids: List[UUID] = Query(..., description="List of idea bank IDs to fetch"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get multiple idea banks by their IDs."""
    try:
        idea_bank_service = IdeaBankService(db)
        idea_banks = await idea_bank_service.get_idea_banks_by_ids(current_user.id, ids)
        return [IdeaBankResponse.model_validate(idea_bank) for idea_bank in idea_banks]
    except Exception as e:
        logger.error(f"Error getting idea banks batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch idea banks",
        )


@router.get("/{idea_bank_id}", response_model=IdeaBankResponse)
async def get_idea_bank(
    idea_bank_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific idea bank item."""
    try:
        idea_bank_service = IdeaBankService(db)
        idea_bank = await idea_bank_service.get_idea_bank(current_user.id, idea_bank_id)

        if not idea_bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Idea bank not found"
            )

        return IdeaBankResponse.model_validate(idea_bank)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting idea bank {idea_bank_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch idea bank",
        )


@router.get("/{idea_bank_id}/with-post")
async def get_idea_bank_with_latest_post(
    idea_bank_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific idea bank item with its latest suggested post."""
    try:
        idea_bank_service = IdeaBankService(db)
        result = await idea_bank_service.get_idea_bank_with_latest_post(
            current_user.id, idea_bank_id
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Idea bank not found"
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting idea bank with latest post {idea_bank_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch idea bank with post",
        )


@router.post("/", response_model=IdeaBankResponse, status_code=status.HTTP_201_CREATED)
async def create_idea_bank(
    idea_bank_data: IdeaBankCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new idea bank item."""
    try:
        idea_bank_service = IdeaBankService(db)
        idea_bank = await idea_bank_service.create_idea_bank(
            current_user.id, idea_bank_data
        )
        return IdeaBankResponse.model_validate(idea_bank)
    except Exception as e:
        logger.error(f"Error creating idea bank: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create idea bank",
        )


@router.put("/{idea_bank_id}", response_model=IdeaBankResponse)
async def update_idea_bank(
    idea_bank_id: UUID,
    update_data: IdeaBankUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update an idea bank item."""
    try:
        idea_bank_service = IdeaBankService(db)
        idea_bank = await idea_bank_service.update_idea_bank(
            current_user.id, idea_bank_id, update_data
        )

        if not idea_bank:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Idea bank not found"
            )

        return IdeaBankResponse.model_validate(idea_bank)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating idea bank {idea_bank_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update idea bank",
        )


@router.delete("/{idea_bank_id}")
async def delete_idea_bank(
    idea_bank_id: UUID,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete an idea bank item."""
    try:
        idea_bank_service = IdeaBankService(db)
        deleted = await idea_bank_service.delete_idea_bank(
            current_user.id, idea_bank_id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Idea bank not found"
            )

        return {"message": "Idea bank deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting idea bank {idea_bank_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete idea bank",
        )

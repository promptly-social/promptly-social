"""
Idea Bank router with endpoints for idea bank management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.routers.auth import get_current_user
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
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get idea banks with filtering and pagination."""
    try:
        idea_bank_service = IdeaBankService(db)
        result = await idea_bank_service.get_idea_bank_list(
            user_id=current_user.id,
            page=page,
            size=size,
            order_by=order_by,
            order_direction=order_direction,
        )
        return IdeaBankListResponse(**result)
    except Exception as e:
        logger.error(f"Error getting idea bank list: {e}")
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

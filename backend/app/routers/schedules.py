"""
Router for managing daily suggestion schedules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.dependencies import get_current_user_with_rls as get_current_user
from app.schemas.auth import UserResponse
from app.schemas.daily_suggestion_schedule import (
    DailySuggestionScheduleCreate,
    DailySuggestionScheduleUpdate,
    DailySuggestionScheduleResponse,
)
from app.services.daily_suggestion_schedule import DailySuggestionScheduleService

router = APIRouter(prefix="/schedules/daily-suggestions", tags=["schedules"])


@router.get("/", response_model=DailySuggestionScheduleResponse | None)
async def get_schedule(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = DailySuggestionScheduleService(db, current_user.id)
    schedule = await service.get_schedule(current_user.id)
    return (
        DailySuggestionScheduleResponse.model_validate(schedule) if schedule else None
    )


@router.post(
    "/",
    response_model=DailySuggestionScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    schedule_data: DailySuggestionScheduleCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = DailySuggestionScheduleService(db, current_user.id)
    try:
        schedule = await service.create_schedule(current_user.id, schedule_data)
        return DailySuggestionScheduleResponse.model_validate(schedule)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule",
        )


@router.put("/", response_model=DailySuggestionScheduleResponse)
async def update_schedule(
    schedule_data: DailySuggestionScheduleUpdate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = DailySuggestionScheduleService(db, current_user.id)
    schedule = await service.update_schedule(current_user.id, schedule_data)
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    return DailySuggestionScheduleResponse.model_validate(schedule)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    service = DailySuggestionScheduleService(db, current_user.id)
    deleted = await service.delete_schedule(current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    return None

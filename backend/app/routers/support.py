"""
Support router for handling support requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.dependencies import get_current_user_with_rls as get_current_user
from app.schemas.auth import UserResponse
from app.schemas.support import SupportRequestCreate, SupportRequestResponse
from app.services.support import SupportService

router = APIRouter(prefix="/support", tags=["support"])


@router.post(
    "/", response_model=SupportRequestResponse, status_code=status.HTTP_201_CREATED
)
async def create_support_request(
    support_data: SupportRequestCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new support request and send email to support team."""
    try:
        service = SupportService(db)
        support_request = await service.create_support_request(
            user_id=current_user.id,
            support_data=support_data,
            user_email=current_user.email,
            user_name=current_user.full_name or current_user.email,
        )
        return SupportRequestResponse.model_validate(support_request)
    except Exception as e:
        logger.error(f"Error creating support request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support request",
        )

"""
API endpoints for chat functionality.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.dependencies import get_current_user_with_rls as get_current_user
from app.schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    StreamChatRequest,
    ConversationUpdate,
)
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
async def create_new_conversation(
    conversation_data: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new conversation."""
    chat_service = ChatService(db)
    # Check if conversation already exists for this idea bank or post
    existing_conversation = None
    if conversation_data.idea_bank_id or conversation_data.post_id:
        existing_conversation = await chat_service.get_conversation_by_params(
            user.id,
            conversation_data.idea_bank_id,
            conversation_data.post_id,
            conversation_data.conversation_type,
        )

    if existing_conversation:
        # This is not an error, we just return the existing one.
        # The frontend should ideally call the GET endpoint first.
        return existing_conversation

    try:
        conversation = await chat_service.create_conversation(user, conversation_data)
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Could not create conversation.")


@router.get("/conversations", response_model=Optional[ConversationResponse])
async def get_conversation_by_params(
    idea_bank_id: Optional[UUID] = Query(None, description="The ID of the idea bank"),
    post_id: Optional[UUID] = Query(None, description="The ID of the post"),
    conversation_type: Optional[str] = Query(
        None, description="The type of conversation"
    ),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Get a conversation by idea_bank_id or post_id."""
    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation_by_params(
        user.id, idea_bank_id, post_id, conversation_type
    )
    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation_status(
    conversation_id: UUID,
    update_data: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a conversation's status (e.g., archive)."""
    chat_service = ChatService(db)
    try:
        conversation = await chat_service.update_conversation_status(
            user.id, conversation_id, update_data.status or "active"
        )
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating conversation status: {e}")
        raise HTTPException(status_code=500, detail="Could not update conversation.")


@router.post("/stream")
async def stream_chat(
    chat_request: StreamChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Handle a streaming chat request."""
    chat_service = ChatService(db)

    async def generate():
        async for response in chat_service.stream_chat_response(
            user, chat_request.conversation_id, chat_request.messages
        ):
            yield f"data: {response.model_dump_json()}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

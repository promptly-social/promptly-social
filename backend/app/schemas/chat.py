"""
Chat schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MessageCreate(BaseModel):
    """Schema for creating a new message."""

    content: str = Field(..., description="The message content")
    message_type: str = Field(
        default="text", description="Message type: text, voice, or system"
    )
    message_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional message metadata"
    )


class MessageResponse(BaseModel):
    """Schema for message responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: str
    content: str
    message_type: str
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    idea_bank_id: UUID = Field(
        ..., description="The idea bank ID to generate a post for"
    )
    conversation_type: str = Field(
        default="post_generation", description="Type of conversation"
    )
    title: Optional[str] = Field(None, description="Optional conversation title")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for the conversation"
    )


class ConversationResponse(BaseModel):
    """Schema for conversation responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    idea_bank_id: Optional[UUID]
    conversation_type: str
    title: Optional[str]
    context: Optional[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []


class ChatRequest(BaseModel):
    """Schema for chat requests."""

    message: str = Field(..., description="The user's message")
    message_type: str = Field(default="text", description="Message type: text or voice")
    message_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional message metadata"
    )


class ChatStreamResponse(BaseModel):
    """Schema for streaming chat responses."""

    type: Literal["message", "tool_output", "error", "end"] = Field(
        ..., description="Response type: message, tool_output, error, or end"
    )
    content: Optional[str] = Field(None, description="The response content")
    tool_name: Optional[str] = Field(None, description="The name of the tool used")
    message_id: Optional[UUID] = Field(None, description="The message ID")
    conversation_id: Optional[UUID] = Field(None, description="The conversation ID")
    error: Optional[str] = Field(None, description="Error message if type is error")


class PostGenerationResult(BaseModel):
    """Schema for post generation results."""

    post_id: UUID = Field(..., description="The generated post ID")
    content: str = Field(..., description="The generated post content")
    topics: List[str] = Field(..., description="Relevant topics for the post")


class ConversationListResponse(BaseModel):
    """Schema for conversation list responses."""

    items: List[ConversationResponse]
    total: int
    page: int
    size: int
    has_next: bool


class ChatMessage(BaseModel):
    """Schema for chat messages passed in a streaming request."""

    role: str = Field(
        ..., description="Role of message sender: user, assistant, system"
    )
    content: str = Field(..., description="The message content")


class StreamChatRequest(BaseModel):
    """Schema for a streaming chat request."""

    conversation_id: UUID = Field(..., description="The conversation ID")
    messages: List[ChatMessage] = Field(
        ..., description="The history of messages in the conversation"
    )

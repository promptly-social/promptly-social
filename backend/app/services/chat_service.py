"""
Chat service for handling conversations and messages.
"""

import json
from typing import List, AsyncGenerator, Optional
from uuid import UUID
from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent

from pydantic_ai.messages import (
    TextPart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    ToolReturnPart,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Conversation, Message
from app.models.idea_bank import IdeaBank
from app.models.profile import UserPreferences, WritingStyleAnalysis
from app.models.content_strategies import ContentStrategy
from app.models.user import User
from app.schemas.chat import (
    ConversationCreate,
    ChatStreamResponse,
    ChatMessage,
)
from app.services.post_generator import (
    generate_linkedin_post_tool,
    revise_linkedin_post_tool,
    PostGenerationContext,
)
from app.services.model_config import model_config


class ChatService:
    """Service class for chat operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

        # Use shared model configuration for consistency
        self.model = model_config.get_chat_model()
        self.model_settings = model_config.get_chat_model_settings()

    def _create_agent(self, system_prompt: str) -> Agent:
        """
        Creates a Pydantic-AI agent with proper fallback configuration.
        Uses OpenRouter's native model fallback instead of manual handling.
        """

        # Create agent with tools and proper retry configuration
        agent = Agent[PostGenerationContext, str](
            self.model,
            tools=[generate_linkedin_post_tool, revise_linkedin_post_tool],
            model_settings=self.model_settings,
            output_type=str,
            instructions=system_prompt,
            retries=2,  # Built-in retry mechanism for agent failures
        )

        return agent

    async def get_conversation(
        self, user_id: UUID, conversation_id: UUID
    ) -> Optional[Conversation]:
        """Get a conversation by ID, ensuring it belongs to the user."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_conversation_by_params(
        self,
        user_id: UUID,
        idea_bank_id: Optional[UUID] = None,
        conversation_type: Optional[str] = None,
    ) -> Optional[Conversation]:
        """Get a conversation by idea_bank_id, ensuring it belongs to the user."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.idea_bank_id == idea_bank_id,
                Conversation.user_id == user_id,
                Conversation.conversation_type == conversation_type,
                Conversation.status == "active",
            )
            .order_by(Conversation.updated_at.desc())
            .options(selectinload(Conversation.messages))
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_conversation(
        self, user: User, conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        if conversation_data.idea_bank_id:
            idea_bank_stmt = select(IdeaBank).where(
                IdeaBank.id == conversation_data.idea_bank_id,
                IdeaBank.user_id == user.id,
            )
            result = await self.db.execute(idea_bank_stmt)
            idea_bank = result.scalars().first()
            if not idea_bank:
                raise ValueError("Idea bank not found")

        new_conversation = Conversation(
            user_id=user.id,
            idea_bank_id=conversation_data.idea_bank_id,
            conversation_type=conversation_data.conversation_type,
            title=conversation_data.title,
            context=conversation_data.context,
        )
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation, attribute_names=["messages"])
        return new_conversation

    async def update_conversation_status(
        self, user_id: UUID, conversation_id: UUID, status: str
    ) -> Conversation:
        """Update the status of a conversation, ensuring it belongs to the user."""
        conversation = await self.get_conversation(user_id, conversation_id)
        if not conversation:
            raise ValueError("Conversation not found or access denied")

        conversation.status = status
        await self.db.commit()

        # Refresh the whole instance so that all attributes (e.g. `updated_at`)
        # are eagerly loaded, avoiding lazy-load IO outside the async context.
        await self.db.refresh(conversation)

        # Ensure messages are available as well (they were previously selected
        # via `selectinload`, but we refresh again to be safe).
        await self.db.refresh(conversation, attribute_names=["messages"])
        return conversation

    async def _get_user_profile_data(self, user_id: UUID) -> dict:
        """Get user's bio, writing style, and strategy as a dictionary."""
        user_pref_stmt = select(UserPreferences).where(
            UserPreferences.user_id == user_id
        )
        writing_style_stmt = select(WritingStyleAnalysis).where(
            WritingStyleAnalysis.user_id == user_id
        )
        content_strategy_stmt = select(ContentStrategy).where(
            ContentStrategy.user_id == user_id, ContentStrategy.platform == "linkedin"
        )

        user_pref_res = await self.db.execute(user_pref_stmt)
        user_pref = user_pref_res.scalars().first()

        writing_style_res = await self.db.execute(writing_style_stmt)
        writing_style = writing_style_res.scalars().first()

        content_strategy_res = await self.db.execute(content_strategy_stmt)
        content_strategy = content_strategy_res.scalars().first()

        return {
            "bio": user_pref.bio if user_pref else "Not provided",
            "writing_style": writing_style.analysis_data
            if writing_style
            else "Not provided",
            "linkedin_post_strategy": content_strategy.strategy
            if content_strategy
            else "Not provided",
        }

    async def _add_message_to_db(
        self, conversation_id: UUID, role: str, content: str
    ) -> Message:
        """Add a message to the database."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    # ===================== Helper utilities =====================

    async def _stream_with_agent(
        self,
        conversation_id: UUID,
        system_prompt: str,
        user_message_content: str,
        history: list[ModelMessage],
        deps: PostGenerationContext,
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        """
        Simplified streaming logic that relies on PydanticAI's native error handling.
        OpenRouter's model fallback and agent retries handle failures automatically.
        """
        agent = self._create_agent(system_prompt)

        try:
            async with agent.run_stream(
                user_message_content,
                deps=deps,
                message_history=history,
            ) as result:
                full_response = ""
                last_len = 0

                # Stream text responses
                async for text in result.stream_text():
                    if text is None:
                        continue
                    delta = text[last_len:]
                    last_len = len(text)
                    if delta:
                        yield ChatStreamResponse(type="message", content=delta)
                    full_response = text

                # Persist assistant reply
                if full_response:
                    await self._add_message_to_db(
                        conversation_id, "assistant", full_response
                    )

                # Handle tool outputs
                for msg in result.new_messages():
                    for p in msg.parts:
                        if isinstance(p, ToolReturnPart):
                            content = p.content
                            # Extract the actual result from wrapper if needed
                            if hasattr(content, "output"):
                                content = content.output
                            tool_json = (
                                content.model_dump_json()
                                if isinstance(content, BaseModel)
                                else str(content)
                            )
                            # Persist tool output
                            await self._add_message_to_db(
                                conversation_id, "tool", tool_json
                            )
                            yield ChatStreamResponse(
                                type="tool_output", content=tool_json
                            )

        except Exception as e:
            logger.error(f"Error streaming chat response: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {getattr(e, 'args', 'No args')}")

            # Try to get more detailed error information
            if hasattr(e, "response"):
                logger.error(
                    f"Response status: {getattr(e.response, 'status_code', 'Unknown')}"
                )
                logger.error(f"Response text: {getattr(e.response, 'text', 'Unknown')}")

            if hasattr(e, "body"):
                logger.error(f"Error body: {e.body}")

            if hasattr(e, "message"):
                logger.error(f"Error message: {e.message}")

            # Check if it's a provider error
            error_msg = str(e)
            is_provider_error = "Provider returned error" in error_msg

            if is_provider_error and hasattr(e, "body") and isinstance(e.body, dict):
                # Extract provider information from error
                metadata = e.body.get("metadata", {})
                provider_name = metadata.get("provider_name", "Unknown")
                raw_error = metadata.get("raw", "")

                logger.error(f"Provider {provider_name} error: {raw_error}")

                # Check if it's a temporary provider issue (5xx errors)
                if "500" in raw_error or "502" in raw_error or "503" in raw_error:
                    error_msg = f"Provider {provider_name} is experiencing temporary issues (server error). The fallback models should handle this automatically. If the issue persists, try again in a few minutes."
                else:
                    error_msg = f"Provider {provider_name} error. Check your model configuration and API key."
            elif is_provider_error:
                error_msg += " - This may be due to model configuration or temporary provider issues. The fallback models should handle this automatically."

            yield ChatStreamResponse(type="error", error=error_msg)
        finally:
            # Always send the "end" signal to properly close the stream
            yield ChatStreamResponse(type="end")

    # ===================== Original helpers continue =====================

    @staticmethod
    def _convert_to_message_history(
        chat_messages: List["ChatMessage"],
    ) -> List[ModelMessage]:
        """Convert API `ChatMessage` items to Pydantic-AI `ModelMessage` objects."""
        history: List[ModelMessage] = []
        for msg in chat_messages:
            if msg.role == "user":
                history.append(
                    ModelRequest(parts=[UserPromptPart(content=msg.content)])
                )
            elif msg.role == "assistant":
                history.append(ModelResponse(parts=[TextPart(content=msg.content)]))
            # system messages and other roles are ignored here; adjust if needed
            elif msg.role == "tool":
                message = ""
                try:
                    message = json.loads(msg.content)["linkedin_post"]
                except json.JSONDecodeError:
                    message = msg.content
                history.append(ModelResponse(parts=[TextPart(content=message)]))
        return history

    @staticmethod
    def _convert_to_conversation_context(
        chat_messages: List["ChatMessage"],
    ) -> str:
        """Convert API `ChatMessage` items to a readable string format for context."""
        if not chat_messages:
            return ""

        context_parts = []
        for msg in chat_messages:
            if msg.role == "user":
                context_parts.append(f"USER: {msg.content}")
            elif msg.role == "assistant":
                context_parts.append(f"ASSISTANT: {msg.content}")
            elif msg.role == "tool":
                # Extract LinkedIn post content from tool output
                try:
                    parsed = json.loads(msg.content)
                    if isinstance(parsed, dict) and "linkedin_post" in parsed:
                        context_parts.append(
                            f"GENERATED POST:\n{parsed['linkedin_post']}"
                        )
                    else:
                        context_parts.append(f"TOOL OUTPUT: {msg.content}")
                except json.JSONDecodeError:
                    context_parts.append(f"TOOL OUTPUT: {msg.content}")

        return "\n\n".join(context_parts)

    async def _handle_generation(
        self,
        conversation_id: UUID,
        idea_content: str,
        user_message: ChatMessage,
        history: list[ModelMessage],
        profile_data: dict,
        messages: List[ChatMessage],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        # Convert message history to conversation context
        conversation_context = self._convert_to_conversation_context(messages[:-1])

        system_prompt = f"""
        You are a LinkedIn content strategist. Your job is to help users create LinkedIn posts.

        AVAILABLE INFORMATION:
        - Post Idea: {idea_content}
        - User Bio: {profile_data["bio"]}
        - User Writing Style: {profile_data["writing_style"]}
        - User LinkedIn Strategy: {profile_data["linkedin_post_strategy"]}
        - Conversation History: {conversation_context or "No previous conversation"}

        INSTRUCTIONS:
        1. When a user wants to create a LinkedIn post, ask 1-3 questions to understand their perspective, personal experiences, or key message they want to convey.

        2. After getting their input, use the 'generate_linkedin_post_tool' to create their post.
           The tool has access to all the user information automatically - you don't need to pass any parameters.

        3. Don't have long conversations - after 1-3 exchanges, generate the post.

        Example flow:
        - User: "Help me create a post about this article"
        - You: "What's your main takeaway from this? Any personal experience related to it?"
        - User: [provides their perspective]
        - You: [call generate_linkedin_post_tool - no parameters needed]
        """

        # Create context with all the required data
        context = PostGenerationContext(
            idea_content=idea_content,
            bio=profile_data["bio"],
            writing_style=profile_data["writing_style"],
            linkedin_post_strategy=profile_data["linkedin_post_strategy"],
            conversation_context=conversation_context,
        )

        async for chunk in self._stream_with_agent(
            conversation_id,
            system_prompt,
            user_message.content,
            history,
            context,
        ):
            yield chunk

    async def _handle_revision(
        self,
        conversation_id: UUID,
        idea_content: str,
        user_message: ChatMessage,
        history: list[ModelMessage],
        profile_data: dict,
        previous_draft: str,
        user_feedback: str,
        messages: List[ChatMessage],
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        # Convert message history to conversation context
        conversation_context = self._convert_to_conversation_context(messages[:-1])

        system_prompt = f"""
        You are an expert LinkedIn content strategist helping users refine their posts through conversation.
        Your role is to understand what the user wants to change and either engage them in discussion or use the 'revise_linkedin_post_tool' when you have clear direction.

        CONTEXT FOR REVISION:
        - Original Post Idea: {idea_content}
        - User Bio: {profile_data["bio"]}
        - Writing Style: {profile_data["writing_style"]}
        - LinkedIn Strategy: {profile_data["linkedin_post_strategy"]}
        - Previous Draft: {previous_draft}
        - User's Latest Request: {user_feedback}
        - Conversation History: {conversation_context or "No previous conversation"}

        REVISION APPROACH:
        1. **Understand the request**: If the user's feedback is clear and specific (like "make it shorter", "add more emotion", "remove the question"), use the revise_linkedin_post_tool immediately.
           The tool has access to all the user information and previous draft automatically - you don't need to pass any parameters.

        2. **Engage when unclear**: If the feedback is vague (like "make it better", "I don't like it"), ask clarifying questions to understand:
           - What specifically they want to change
           - What they liked or didn't like about the current version
           - What tone or approach they prefer
           - Any specific elements they want added or removed

        3. **Reference conversation history**: Use the conversation context to understand their preferences and previous feedback.

        4. **Be conversational**: Keep the tone collaborative and helpful. You're working together to refine their post.
        """

        # Create context with all the required data including revision-specific info
        context = PostGenerationContext(
            idea_content=idea_content,
            bio=profile_data["bio"],
            writing_style=profile_data["writing_style"],
            linkedin_post_strategy=profile_data["linkedin_post_strategy"],
            conversation_context=conversation_context,
            previous_draft=previous_draft,
            user_feedback=user_feedback,
        )

        async for chunk in self._stream_with_agent(
            conversation_id,
            system_prompt,
            user_message.content,
            history,
            context,
        ):
            yield chunk

    # ================================================================

    async def stream_chat_response(
        self, user: User, conversation_id: UUID, messages: List[ChatMessage]
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        """Stream a chat response from the AI model."""
        conversation = await self.get_conversation(user.id, conversation_id)
        if not conversation:
            yield ChatStreamResponse(type="error", error="Conversation not found")
            return

        idea_content = "Please reference the chat history."
        if conversation.idea_bank_id:
            idea_bank = await self.db.get(IdeaBank, conversation.idea_bank_id)
            if idea_bank:
                idea_content = idea_bank.data.get("value", "")

        user_message = messages[-1]
        await self._add_message_to_db(
            conversation.id, user_message.role, user_message.content
        )

        # Find the most recent tool-generated draft in the stored conversation history
        previous_draft: Optional[str] = None
        for m in reversed(conversation.messages):  # iterate over DB-persisted messages
            if m.role != "tool":
                continue
            try:
                parsed = json.loads(m.content)
                if isinstance(parsed, dict) and "linkedin_post" in parsed:
                    previous_draft = parsed["linkedin_post"]
                else:
                    previous_draft = m.content
            except json.JSONDecodeError:
                previous_draft = m.content
            if previous_draft:
                break

        profile_data = await self._get_user_profile_data(user.id)
        bio = profile_data["bio"]
        writing_style = profile_data["writing_style"]
        linkedin_post_strategy = profile_data["linkedin_post_strategy"]

        profile_data = {
            "bio": bio,
            "writing_style": writing_style,
            "linkedin_post_strategy": linkedin_post_strategy,
        }

        user_feedback = user_message.content

        # Build message history for agent (exclude most recent user message)
        history = self._convert_to_message_history(messages[:-1])

        # Route to appropriate handler
        if previous_draft:
            async for chunk in self._handle_revision(
                conversation_id,
                idea_content,
                user_message,
                history,
                profile_data,
                previous_draft,
                user_feedback,
                messages,
            ):
                yield chunk
            return
        else:
            async for chunk in self._handle_generation(
                conversation_id,
                idea_content,
                user_message,
                history,
                profile_data,
                messages,
            ):
                yield chunk
            return

"""
Chat service for handling conversations and messages.
"""

import json
from typing import List, AsyncGenerator, Optional
from uuid import UUID
from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.messages import (
    TextPart,
    ModelMessage,
    # Message history primitives
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    ToolReturnPart,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
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
    PostGeneratorService,
)


class ChatService:
    """Service class for chat operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _create_agent(self, system_prompt: str) -> Agent:
        """
        Creates the Pydantic-AI agent.
        It should use a smaller model for the chat and a larger model for the tool calls.
        """

        fallback_models = [
            model.strip()
            for model in settings.openrouter_models_fallback.split(",")
            if model.strip()
        ]

        provider = OpenRouterProvider(
            api_key=settings.openrouter_api_key,
        )

        model = OpenAIModel(
            settings.openrouter_model_primary,
            provider=provider,
        )

        return Agent[PostGeneratorService, str](
            model,
            tools=[generate_linkedin_post_tool, revise_linkedin_post_tool],
            model_settings=OpenAIModelSettings(
                temperature=settings.openrouter_model_temperature,
                extra_body={"models": fallback_models},
            ),
            output_type=str,
            instructions=system_prompt,
        )

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

    async def get_conversation_by_idea_bank(
        self, user_id: UUID, idea_bank_id: UUID
    ) -> Optional[Conversation]:
        """Get a conversation by idea_bank_id, ensuring it belongs to the user."""
        stmt = (
            select(Conversation)
            .where(
                Conversation.idea_bank_id == idea_bank_id,
                Conversation.user_id == user_id,
            )
            .options(selectinload(Conversation.messages))
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_conversation(
        self, user: User, conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        idea_bank_stmt = select(IdeaBank).where(
            IdeaBank.id == conversation_data.idea_bank_id, IdeaBank.user_id == user.id
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
        deps: PostGeneratorService,
        fallback_callable,
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        """Core streaming logic used by both generation and revision flows."""
        agent = self._create_agent(system_prompt)
        tool_called = False

        try:
            async with agent.run_stream(
                user_message_content,
                deps=deps,
                message_history=history,
            ) as result:
                full_response = ""
                last_len = 0
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

                # Tool return parts
                for msg in result.new_messages():
                    for p in msg.parts:
                        if isinstance(p, ToolReturnPart):
                            tool_called = True
                            content = p.content
                            if hasattr(content, "output"):
                                content = content.output
                            tool_json = (
                                content.model_dump_json()
                                if isinstance(content, BaseModel)
                                else str(content)
                            )
                            yield ChatStreamResponse(
                                type="tool_output", content=tool_json
                            )

                # Fallback if tool not invoked and no assistant response
                if (
                    not tool_called
                    and not full_response
                    and fallback_callable is not None
                ):
                    try:
                        fb_result = await fallback_callable()
                        if hasattr(fb_result, "output"):
                            fb_result = fb_result.output
                        tool_json = (
                            fb_result.model_dump_json()
                            if isinstance(fb_result, BaseModel)
                            else str(fb_result)
                        )
                        await self._add_message_to_db(
                            conversation_id, "tool", tool_json
                        )
                        yield ChatStreamResponse(type="tool_output", content=tool_json)
                    except Exception as e:
                        logger.error(f"Fallback error: {e}")
                        yield ChatStreamResponse(type="error", error=str(e))
        except Exception as e:
            logger.error(f"Error streaming chat response: {e}")
            # Try fallback if available
            if fallback_callable is not None:
                try:
                    fb_result = await fallback_callable()
                    if hasattr(fb_result, "output"):
                        fb_result = fb_result.output
                    tool_json = (
                        fb_result.model_dump_json()
                        if isinstance(fb_result, BaseModel)
                        else str(fb_result)
                    )
                    await self._add_message_to_db(conversation_id, "tool", tool_json)
                    yield ChatStreamResponse(type="tool_output", content=tool_json)
                except Exception as inner_e:
                    logger.error(f"Fallback after error failed: {inner_e}")
                    yield ChatStreamResponse(type="error", error=str(inner_e))
            else:
                yield ChatStreamResponse(type="error", error=str(e))
        finally:
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

    async def _handle_generation(
        self,
        conversation_id: UUID,
        idea_content: str,
        user_message: ChatMessage,
        history: list[ModelMessage],
        profile_data: dict,
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        system_prompt = f"""
        You are an expert at interviewing a user and brainstorming the specific content they want to post on LinkedIn.
        Your task is to create a LinkedIn post based on the provided content idea and user profile information.
        - Post Idea (can be a URL or text): {idea_content}
        - User Bio: {profile_data["bio"]}
        - User Writing Style: {profile_data["writing_style"]}
        - User LinkedIn Strategy: {profile_data["linkedin_post_strategy"]}

        If you have enough information, use the 'generate_linkedin_post_tool'.
        Ask clarifying questions one at a time to better understand the user's needs, perspective, anecdote, and angle, etc.
        You already have the user's bio and writing style. SO please ask questions that are relevant to the post idea.
        Keep your questions concise.
        """
        deps = PostGeneratorService()
        print(system_prompt)
        async for chunk in self._stream_with_agent(
            conversation_id,
            system_prompt,
            user_message.content,
            history,
            deps,
            lambda: deps.generate_post(
                idea_content=idea_content,
                bio=profile_data["bio"],
                writing_style=profile_data["writing_style"],
                linkedin_post_strategy=profile_data["linkedin_post_strategy"],
            ),
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
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        system_prompt = f"""
        You are an expert copy editor who helps users revise LinkedIn posts through conversation.
        The user's previous draft is included in CONTEXT FOR REVISION.
        You must call the revise_linkedin_post_tool when the feedback is clear.

        CONTEXT FOR REVISION:
        - Post Idea: {idea_content}
        - User Bio: {profile_data["bio"]}
        - Writing Style: {profile_data["writing_style"]}
        - LinkedIn Strategy: {profile_data["linkedin_post_strategy"]}
        - Previous Draft: {previous_draft}
        - User Feedback: {user_feedback}
        """
        print(system_prompt)
        deps = PostGeneratorService()
        async for chunk in self._stream_with_agent(
            conversation_id,
            system_prompt,
            user_message.content,
            history,
            deps,
            lambda: deps.revise_post(
                idea_content=idea_content,
                bio=profile_data["bio"],
                writing_style=profile_data["writing_style"],
                linkedin_post_strategy=profile_data["linkedin_post_strategy"],
                previous_draft=previous_draft,
                user_feedback=user_message.content,
            ),
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

        idea_content = ""
        idea_bank = await self.db.get(IdeaBank, conversation.idea_bank_id)

        if idea_bank:
            idea_content = idea_bank.data

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

        # Truncate long sections to guard against context overflow (approx 4k chars each)
        MAX_SECTION_LEN = 4000
        if previous_draft and len(previous_draft) > MAX_SECTION_LEN:
            previous_draft = previous_draft[:MAX_SECTION_LEN] + "... [truncated]"
        user_feedback = user_message.content
        if user_feedback and len(user_feedback) > MAX_SECTION_LEN:
            user_feedback = user_feedback[:MAX_SECTION_LEN] + "... [truncated]"

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
            ):
                yield chunk
            return

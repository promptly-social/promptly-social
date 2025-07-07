"""
Chat service for handling conversations and messages.
"""

from typing import List, AsyncGenerator, Optional
from uuid import UUID
from loguru import logger
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
                history.append(ModelResponse(parts=[TextPart(content=msg.content)]))
        return history

    async def stream_chat_response(
        self, user: User, conversation_id: UUID, messages: List[ChatMessage]
    ) -> AsyncGenerator[ChatStreamResponse, None]:
        """Stream a chat response from the AI model."""
        conversation = await self.get_conversation(user.id, conversation_id)
        if not conversation:
            yield ChatStreamResponse(type="error", error="Conversation not found")
            return

        idea_bank = await self.db.get(IdeaBank, conversation.idea_bank_id)
        if not idea_bank:
            yield ChatStreamResponse(type="error", error="Idea bank not found")
            return

        user_message = messages[-1]
        await self._add_message_to_db(
            conversation.id, user_message.role, user_message.content
        )

        # Check for a previous draft in the conversation history
        previous_draft = None
        # Check messages before the current user message
        for msg in reversed(messages[:-1]):
            if msg.role == "tool":
                previous_draft = msg.content
                break

        profile_data = await self._get_user_profile_data(user.id)
        bio = profile_data["bio"]
        writing_style = profile_data["writing_style"]
        linkedin_post_strategy = profile_data["linkedin_post_strategy"]
        idea_content = idea_bank.data.get("value") or idea_bank.data.get("title", "")

        user_feedback = user_message.content

        # Determine which prompt to use
        if previous_draft:
            # Revision prompt
            system_prompt = f"""
            You are an expert copy editor revising a LinkedIn post based on user feedback.
            - Previous Draft: {previous_draft}
            - User Feedback: {user_feedback}
            - Post Idea (can be a URL or text): {idea_content}
            - User Bio: {bio}
            - User Writing Style: {writing_style}
            - User LinkedIn Strategy: {linkedin_post_strategy}

            You MUST use the 'revise_linkedin_post_tool' to revise the draft.
            Do not ask questions. Do not add any extra text. ONLY return the revised draft.
            """
        else:
            # Generation prompt
            system_prompt = f"""
            You are an expert at generating posts for LinkedIn to gain the most engagement.
            Your task is to create a LinkedIn post based on the provided content idea and user profile information.
            - Post Idea (can be a URL or text): {idea_content}
            - User Bio: {bio}
            - User Writing Style: {writing_style}
            - User LinkedIn Strategy: {linkedin_post_strategy}

            If you have enough information, use the 'generate_linkedin_post_tool'.
            If not, ask clarifying questions one at a time to better understand the user's needs, perspective, anecdtoe, and angle, etc.
            Keep your questions concise.
            """

        # Convert prior messages (exclude the latest user message) to the correct datatype
        history = self._convert_to_message_history(messages[:-1])

        agent = self._create_agent(system_prompt)

        deps = PostGeneratorService()

        try:
            async with agent.run_stream(
                user_message.content,
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
                    # Keep track of the full accumulated response so we can persist it
                    full_response = text

                # Persist the assistant's final reply
                if full_response:
                    await self._add_message_to_db(
                        conversation.id, "assistant", full_response
                    )

                # After the text stream ends, there might still be tool results pending
                for msg in result.new_messages():
                    for p in msg.parts:
                        if isinstance(p, ToolReturnPart):
                            tool_output = str(p.content)
                            await self._add_message_to_db(
                                conversation.id, "tool", tool_output
                            )
                            yield ChatStreamResponse(
                                type="tool_output", content=tool_output
                            )

                # Signal the end of the stream to the client
                yield ChatStreamResponse(type="end")

        except Exception as e:
            logger.error(f"Error streaming chat response: {e}")
            yield ChatStreamResponse(type="error", error=str(e))

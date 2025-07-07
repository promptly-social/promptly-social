"""
This service uses Pydantic-AI to generate posts based on user context.
"""

from typing import Optional

from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.tools import RunContext

from app.core.config import settings


class PostGeneratorService:
    """Service to generate posts using an AI agent."""

    def __init__(self):
        fallback_models = [
            model.strip()
            for model in settings.openrouter_large_models_fallback.split(",")
            if model.strip()
        ]

        provider = OpenRouterProvider(
            api_key=settings.openrouter_api_key,
        )

        model = OpenAIModel(
            settings.openrouter_large_model_primary,
            provider=provider,
        )
        self.agent = Agent(
            model,
            output_type=str,
            model_settings=OpenAIModelSettings(
                temperature=settings.openrouter_large_model_temperature,
                extra_body={"models": fallback_models},
            ),
            system_prompt="",
        )

    async def generate_post(
        self,
        idea_content: str,
        bio: Optional[str],
        writing_style: Optional[str],
        linkedin_post_strategy: Optional[str],
    ) -> str:
        """
        Generates a LinkedIn post using the AI agent.
        """

        prompt = f"""
            You are an expert at generating posts for LinkedIn to gain the most engagement.
            Your task is to create a LinkedIn post based on the provided content idea and user profile information.

            Content Idea:
            ---
            {idea_content}
            ---

            User Profile:
            - Bio: {bio}
            - Writing Style: {writing_style}
            - LinkedIn Post Strategy: {linkedin_post_strategy}

            Instructions:
            1. Generate a LinkedIn-appropriate post that is engaging and likely to get high engagement.
            2. The post should be plain text, without any markdown or special characters like em-dashes or arrows, that might suggest AI generation.
            3. If the content idea is a URL, do not include the link in the post, but cite the source of the post in the post.
           
            Return the generated post in plain text. DO NOT INCLUDE MARKDOWN.
            """

        # Use streaming to start generating immediately and allow future extension.
        async with self.agent.run_stream(
            prompt,
        ) as run_result:
            final_text = ""
            async for text_chunk in run_result.stream_text():
                final_text = text_chunk  # stream_text returns cumulative text

            return final_text

    async def revise_post(
        self,
        idea_content: str,
        bio: Optional[str],
        writing_style: Optional[str],
        linkedin_post_strategy: Optional[str],
        previous_draft: Optional[str] = None,
        user_feedback: Optional[str] = None,
    ) -> str:
        """Revises a LinkedIn post based on user feedback."""

        prompt = f"""
            You are an expert copy editor revising a LinkedIn post based on user feedback.
            Your task is to apply the user's feedback to the 'previous draft' by making targeted edits.
            Do not rewrite the entire post unless the user explicitly asks for it. Your goal is to preserve the original post's structure and content as much as possible, only making changes based on the feedback.

            The original idea for the post was:
            ---
            {idea_content}
            ---

            Here is the previous draft:
            ---
            {previous_draft}
            ---

            Here is the user's feedback:
            ---
            {user_feedback}
            ---
            
            User Profile (for context):
            - Bio: {bio}
            - Writing Style: {writing_style}
            - LinkedIn Post Strategy: {linkedin_post_strategy}

            Instructions:
            1. Carefully analyze the user's feedback.
            2. Apply the requested changes directly to the 'previous draft'.
            3. Maintain the original tone and style unless the feedback specifies a change.
            4. The revised post should still be engaging and likely to get high engagement on LinkedIn.
            5. The post should be plain text, without any markdown or special characters like em-dashes or arrows, that might suggest AI generation.
            6. If the content idea is a URL, do not include the link in the post, but cite the source of the post in the post.
            7. DO NOT INCLUDE MARKDOWN.
           
            ONLY return the revised draft content as plain text. Do not include your thoughts, summaries, or any other text. 
            """

        # Use streaming to start generating immediately and allow future extension.
        async with self.agent.run_stream(
            prompt,
        ) as run_result:
            final_text = ""
            async for text_chunk in run_result.stream_text():
                final_text = text_chunk  # stream_text returns cumulative text

            return final_text


# Singleton instance used by the tool
post_generator_service = PostGeneratorService()


@post_generator_service.agent.tool
async def generate_linkedin_post_tool(
    ctx: RunContext[PostGeneratorService],
    idea_content: str = Field(
        description="The content of the post idea, this is the main topic of the post."
    ),
    bio: str = Field(description="The user's biography."),
    writing_style: str = Field(description="The user's writing style."),
    linkedin_post_strategy: str = Field(
        description="The user's LinkedIn post strategy."
    ),
) -> str:
    """Tool wrapper for generating a LinkedIn post."""

    post = await ctx.deps.generate_post(
        idea_content=idea_content,
        bio=bio,
        writing_style=writing_style,
        linkedin_post_strategy=linkedin_post_strategy,
    )

    return post


@post_generator_service.agent.tool
async def revise_linkedin_post_tool(
    ctx: RunContext[PostGeneratorService],
    idea_content: str = Field(
        description="The content of the post idea, this is the main topic of the post."
    ),
    bio: str = Field(description="The user's biography."),
    writing_style: str = Field(description="The user's writing style."),
    linkedin_post_strategy: str = Field(
        description="The user's LinkedIn post strategy."
    ),
    previous_draft: Optional[str] = Field(
        default=None, description="The previous draft of the post to revise."
    ),
    user_feedback: Optional[str] = Field(
        default=None, description="The user's feedback on the previous draft."
    ),
) -> str:
    """Tool wrapper for revising a LinkedIn post."""
    post = await ctx.deps.revise_post(
        idea_content=idea_content,
        bio=bio,
        writing_style=writing_style,
        linkedin_post_strategy=linkedin_post_strategy,
        previous_draft=previous_draft,
        user_feedback=user_feedback,
    )

    return post

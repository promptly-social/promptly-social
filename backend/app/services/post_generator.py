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
       
        Return the generated post in plain text.
        """

        # Use streaming to start generating immediately and allow future extension.
        async with self.agent.run_stream(prompt) as run_result:
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
    """Tool wrapper for generating a LinkedIn post.

    This tool should only be used when the agent has gathered enough information.
    It calls the `PostGeneratorService` and returns a JSON string of the generated post.
    """

    post = await ctx.deps.generate_post(
        idea_content=idea_content,
        bio=bio,
        writing_style=writing_style,
        linkedin_post_strategy=linkedin_post_strategy,
    )

    return post

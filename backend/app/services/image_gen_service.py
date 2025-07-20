from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai import Agent
from app.services.model_config import model_config
from app.models.profile import UserPreferences


class ImageGenService:
    def __init__(self):
        """
        Creates the Pydantic-AI agent using shared model configuration.
        Uses a smaller model for generating the image prompt.
        """
        # Use shared model configuration for consistency
        self.agent = Agent[str, str](
            model_config.get_chat_model(),
            model_settings=model_config.get_chat_model_settings(),
            output_type=str,
            retries=2,  # Built-in retry mechanism
        )

    async def generate_image_prompt(
        self,
        linkedin_post_text: str,
        user_id: Optional[UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> str:
        # Fetch user preferences if user_id and db are provided
        custom_style = None
        if user_id and db:
            try:
                user_pref_stmt = select(UserPreferences).where(
                    UserPreferences.user_id == user_id
                )
                user_pref_res = await db.execute(user_pref_stmt)
                user_pref = user_pref_res.scalars().first()

                if user_pref and user_pref.image_generation_style:
                    custom_style = user_pref.image_generation_style
            except Exception:
                # If there's any error fetching preferences, continue with default
                pass

        # Build the style options section
        if custom_style:
            style_section = f"""
Step 3: MANDATORY Custom Style - MUST FOLLOW EXACTLY
🎨 CRITICAL: The user has specified a custom image generation style that MUST be used.

CUSTOM STYLE REQUIREMENT: {custom_style}

⚠️ IMPORTANT INSTRUCTIONS:
- This custom style is MANDATORY and takes absolute priority over all default options
- You MUST incorporate this exact style into your final image generation prompt
- Do NOT deviate from or ignore this custom style preference
- The final prompt MUST reflect this style prominently and accurately
- If the custom style conflicts with the content, adapt the content presentation to fit the style"""
        else:
            style_section = """
Step 3: Select the Best Style
Based on the core metaphor and the professional context, choose the most appropriate high-end art style from the expanded list below. Select the one that will best convey the message with clarity and sophistication.

Options:

Photorealistic 3D Render: Best for clean, tangible, tech-focused concepts. Gives a polished, modern look.

Minimalist Vector Illustration: Excellent for representing abstract ideas, processes, or services. Uses clean lines and flat colors for ultimate clarity.

Conceptual Photography: Strong for human-centric or evocative themes. Features real-world objects arranged in a thought-provoking, symbolic way.

Blueprint/Schematic Style: Perfect for topics related to planning, engineering, strategy, or deconstructing a complex system or model.

Isometric Illustration: Ideal for showing systems, processes, or environments in a clean, 3D-without-perspective style. Appears friendly yet technical.

Double Exposure: A highly artistic style for combining two concepts visually (e.g., a human silhouette filled with data patterns) to represent abstract connections and relationships.

Elegant Line Art: For a sophisticated, classic, or premium feel. Uses fine, detailed lines, like a modern engraving, to suggest craftsmanship, precision, and quality.

Data Visualization Art: For posts about data, trends, or networks. Creates a beautiful, abstract representation of information rather than a literal chart or graph.

Glassmorphism/Claymorphism 3D: Modern UI/UX-inspired styles. Glassmorphism uses a frosted-glass effect for a sleek, futuristic feel. Claymorphism uses soft, rounded shapes for a friendly, approachable look."""

        # Build the main prompt with custom style emphasis if present
        style_emphasis = ""
        if custom_style:
            style_emphasis = f" CRITICAL: The user has provided a custom style ({custom_style}) that MUST be followed exactly."

        prompt = f"""
        You are an expert creative director specializing in corporate branding. Your task is to create one single, high-quality image generation prompt based on the LinkedIn post provided below. Your goal is to produce a prompt that will generate a professional, visually striking, and conceptually relevant image suitable for LinkedIn, avoiding generic "AI slop."{style_emphasis}

Follow these steps in your reasoning, but only output the final prompt:

Step 1: Analyze the Post
Read the text to understand its core message, tone, and intended audience.

Step 2: Identify the Core Metaphor
Extract the single most powerful and visually interesting metaphor, analogy, or contrast from the text. This will be the subject of the image.
{style_section}

Step 4: Construct the Final Prompt
Combine the elements above into a single, detailed paragraph. This prompt must be ready to be used in an image generation model. It must describe the scene, the style, the composition (e.g., "minimalist, centered on a clean background"), the lighting (e.g., "soft studio lighting," "dramatic side-lighting"), and the professional color palette.

{"🎨 REMINDER: If a custom style was specified in Step 3, it MUST be the dominant style element in your final prompt. Make sure the custom style is clearly and prominently featured." if custom_style else ""}

Your final output must ONLY be the ready-to-use image generation prompt itself. Do not include your analysis, reasoning, or any other text.

LINKEDIN POST:
{linkedin_post_text}
"""
        print(prompt)

        result = await self.agent.run(prompt)
        return result

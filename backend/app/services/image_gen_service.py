from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from app.core.config import settings


class ImageGenService:
    def __init__(self):
        """
        Creates the Pydantic-AI agent.
        It should use a smaller model for generating the image prompt.
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

        self.agent = Agent[str, str](
            model,
            model_settings=OpenAIModelSettings(
                temperature=settings.openrouter_model_temperature,
                extra_body={"models": fallback_models},
            ),
            output_type=str,
        )

    def generate_image_prompt(self, linkedin_post_text: str) -> str:
        prompt = f"""
        You are an expert creative director specializing in corporate branding. Your task is to create one single, high-quality image generation prompt based on the LinkedIn post provided below. Your goal is to produce a prompt that will generate a professional, visually striking, and conceptually relevant image suitable for LinkedIn, avoiding generic "AI slop."

Follow these steps in your reasoning, but only output the final prompt:

Step 1: Analyze the Post
Read the text to understand its core message, tone, and intended audience.

Step 2: Identify the Core Metaphor
Extract the single most powerful and visually interesting metaphor, analogy, or contrast from the text. This will be the subject of the image.

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

Glassmorphism/Claymorphism 3D: Modern UI/UX-inspired styles. Glassmorphism uses a frosted-glass effect for a sleek, futuristic feel. Claymorphism uses soft, rounded shapes for a friendly, approachable look.

Step 4: Construct the Final Prompt
Combine the elements above into a single, detailed paragraph. This prompt must be ready to be used in an image generation model. It must describe the scene, the style, the composition (e.g., "minimalist, centered on a clean background"), the lighting (e.g., "soft studio lighting," "dramatic side-lighting"), and the professional color palette.

Your final output must ONLY be the ready-to-use image generation prompt itself. Do not include your analysis, reasoning, or any other text.

LINKEDIN POST:
{linkedin_post_text}
"""
        result = self.agent.run(prompt)
        return result

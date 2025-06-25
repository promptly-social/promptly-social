"""
Import Sample Analysis Module

This module contains the core logic for analyzing imported writing samples.
It processes user-provided text and performs writing style analysis.
"""

import logging
import os
from typing import Dict, List, Any

from openai import OpenAI

logger = logging.getLogger(__name__)


class ImportSampleAnalyzer:
    """Analyzes imported writing samples for writing style and content patterns."""

    def __init__(self, openrouter_api_key: str = None):
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_api_key,
        )
        # Get model configuration from environment variables
        self.model_primary = os.getenv(
            "OPENROUTER_MODEL_PRIMARY", "google/gemini-2.5-flash-preview-05-20"
        )
        models_fallback_str = os.getenv(
            "OPENROUTER_MODELS_FALLBACK", "google/gemini-2.5-flash"
        )
        self.models_fallback = [
            model.strip() for model in models_fallback_str.split(",")
        ]
        self.temperature = float(os.getenv("OPENROUTER_TEMPERATURE", "0.0"))

    def analyze_import_sample(
        self, text_sample: str, current_bio: str, content_to_analyze: List[str]
    ) -> Dict[str, Any]:
        """
        Main analysis method that orchestrates the writing sample analysis process.

        Args:
            text_sample: The user-provided writing sample text
            current_bio: The current bio of the user
            content_to_analyze: A list of content to analyze, such as bio, writing_style, etc.

        Returns:
            Complete analysis results dictionary
        """
        logger.debug(
            f"Starting writing sample analysis for content: {', '.join(content_to_analyze)}"
        )

        try:
            if not text_sample or not text_sample.strip():
                logger.error("Empty text sample provided")
                return self._create_empty_analysis()

            writing_style = ""
            if "writing_style" in content_to_analyze:
                # Analyze writing style from the sample
                writing_style = self._analyze_writing_style_from_sample(text_sample)

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "topics": [],
                "websites": [],
                "bio": "",
            }

            logger.debug(
                f"Import sample analysis completed for content: {', '.join(content_to_analyze)}"
            )
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing import sample: {e}")
            raise

    def _analyze_writing_style_from_sample(self, text_sample: str) -> str:
        """Analyze writing style from the imported writing sample."""
        if not text_sample:
            logger.debug("No text sample provided for writing style analysis")
            return ""

        prompt = f"""
        You are an expert at analyzing writing style from text samples.
        You are given a text sample that represents someone's writing.
        Your task is to analyze the writing style, tone, voice, and characteristics of this writing using gender neutral descriptions.
        Consider elements like:
        - Tone (formal, casual, conversational, etc.)
        - Voice (authoritative, friendly, analytical, etc.)
        - Sentence structure and length
        - Use of humor, metaphors, or storytelling
        - Technical vs. accessible language
        - Persuasive techniques
        - Overall personality that comes through in the writing
        
        Return the writing style analysis in plain text format without any markdown. Each observation should be on a new line.
        Be specific and provide actionable insights that could help someone write in a similar style.
        
        Writing Sample:
        {text_sample}
        """

        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model_primary,
                extra_body={
                    "models": self.models_fallback,
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
            )

            if not response.choices:
                logger.error("API call for writing style analysis returned no choices.")
                return ""

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing writing style from sample: {e}")
            return ""

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis result when no valid sample is provided."""
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
            "bio": "",
        }

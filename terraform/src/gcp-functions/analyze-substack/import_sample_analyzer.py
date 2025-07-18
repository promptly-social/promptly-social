"""
Import Sample Analysis Module

This module contains the core logic for analyzing imported writing samples.
It processes user-provided text and performs writing style analysis.
"""

import logging
from typing import Dict, List, Any

from llm_client import LLMClient

logger = logging.getLogger(__name__)


class ImportSampleAnalyzer:
    """Analyzes imported writing samples for writing style and content patterns."""

    def __init__(self):
        # Centralized LLM client (shared config)
        self.llm_client = LLMClient()

    def analyze_import_sample(
        self, text_sample: str, content_to_analyze: List[str]
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
            raw_response = self.llm_client.run_prompt(prompt)

            return raw_response

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

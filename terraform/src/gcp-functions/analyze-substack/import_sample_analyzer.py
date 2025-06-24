"""
Import Sample Analysis Module

This module contains the core logic for analyzing imported writing samples.
It processes user-provided text and performs writing style analysis.
"""

import logging
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

            topics = []
            websites = []
            if "interests" in content_to_analyze:
                # Analyze topics from the writing sample
                topics = self._analyze_topics_from_sample(text_sample)
                websites = []  # Empty for import samples

            bio = current_bio
            if "bio" in content_to_analyze:
                # Create user bio from the writing sample
                bio = self._create_user_bio_from_sample(text_sample, current_bio)

            writing_style = ""
            if "writing_style" in content_to_analyze:
                # Analyze writing style from the sample
                writing_style = self._analyze_writing_style_from_sample(text_sample)

            # Compile results
            analysis_result = {
                "writing_style": writing_style,
                "topics": topics,
                "websites": websites,
                "bio": bio,
            }

            logger.debug(
                f"Import sample analysis completed for content: {', '.join(content_to_analyze)}"
            )
            return analysis_result

        except Exception as e:
            logger.error(f"Error analyzing import sample: {e}")
            raise

    def _analyze_topics_from_sample(self, text_sample: str) -> List[str]:
        """Analyze topics from the imported writing sample."""
        if not text_sample:
            logger.debug("No text sample provided for topic analysis")
            return []

        prompt = f"""
        You are an expert at analyzing topics and themes from writing samples.
        You are given a text sample that represents someone's writing.
        Your task is to identify the main topics and themes that this person writes about or is interested in.
        Return a list of topics, one per line, focusing on subject matters, interests, and themes.
        Each topic should be 1-3 words maximum.
        Limit your response to the top 10 most relevant topics.
        
        Writing Sample:
        {text_sample}
        """

        try:
            response = self.openrouter_client.chat.completions.create(
                model="google/gemini-2.5-pro",
                extra_body={
                    "models": ["openai/gpt-4o"],
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            if not response.choices:
                logger.error("API call for topic analysis returned no choices.")
                return []

            topics_text = response.choices[0].message.content
            # Split by lines and clean up
            topics = [
                topic.strip() for topic in topics_text.split("\n") if topic.strip()
            ]
            # Remove any numbering or bullet points
            topics = [topic.lstrip("0123456789.- ") for topic in topics]
            # Filter out empty topics
            topics = [topic for topic in topics if topic]

            logger.debug(f"Extracted {len(topics)} topics from writing sample")
            return topics[:10]  # Limit to top 10

        except Exception as e:
            logger.error(f"Error analyzing topics from sample: {e}")
            return []

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
                model="google/gemini-2.5-pro",
                extra_body={
                    "models": ["openai/gpt-4o"],
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            if not response.choices:
                logger.error("API call for writing style analysis returned no choices.")
                return ""

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error analyzing writing style from sample: {e}")
            return ""

    def _create_user_bio_from_sample(self, text_sample: str, current_bio: str) -> str:
        """Create or update user bio from the imported writing sample."""
        if not text_sample:
            logger.debug("No text sample provided for bio creation")
            return current_bio

        prompt = f"""
        You are an expert at creating user bios from writing samples.
        You are given a text sample that represents someone's writing and their current bio.
        Your task is to create or update the user bio based on the writing sample, using first person perspective and gender neutral descriptions.
        
        The bio should capture:
        - What the person does professionally or their expertise
        - Their interests and passions that come through in their writing
        - Their perspective or approach to topics
        - What makes them unique as a writer or professional
        
        If there's a current bio, use it as a foundation and enhance it with insights from the writing sample.
        If there's no current bio, create one based entirely on the writing sample.
        Keep the bio concise but informative (2-4 sentences).
        This will be used as a persona for LLM to generate content in their style, preferences, and point of view.
        You should return the bio in plain text format without any markdown.
        
        Writing Sample:
        {text_sample}
        
        Current Bio: {current_bio}
        """

        try:
            response = self.openrouter_client.chat.completions.create(
                model="google/gemini-2.5-pro",
                extra_body={
                    "models": ["openai/gpt-4o"],
                },
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )

            if not response.choices:
                logger.error("API call for bio creation returned no choices.")
                return current_bio

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error creating bio from sample: {e}")
            return current_bio

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis result when no valid sample is provided."""
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
            "bio": "",
        }

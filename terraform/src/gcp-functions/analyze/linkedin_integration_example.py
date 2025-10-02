"""
Example integration of LinkedInAnalyzerV2 with the existing backend system.

This shows how to integrate the new LinkedIn Community Management API analyzer
with the existing profile analysis workflow.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from linkedin_analyzer_v2 import LinkedInAnalyzerV2

logger = logging.getLogger(__name__)


class LinkedInAnalysisService:
    """
    Service class that integrates LinkedInAnalyzerV2 with the backend system.
    
    This handles the transition from the old scraping-based analyzer to the new
    API-based analyzer using analytics access tokens.
    """
    
    def __init__(self, openrouter_api_key: str):
        self.openrouter_api_key = openrouter_api_key
    
    async def analyze_linkedin_profile(
        self,
        analytics_access_token: str,
        person_urn: str,
        current_bio: str,
        content_to_analyze: list,
        user_writing_style: str,
        max_posts: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze LinkedIn profile using the v2 analyzer with analytics access token.
        
        Args:
            analytics_access_token: LinkedIn analytics access token
            person_urn: LinkedIn person URN (e.g., "urn:li:person:123456")
            current_bio: Current user bio
            content_to_analyze: List of content types to analyze
            user_writing_style: Current writing style
            max_posts: Maximum number of posts to analyze
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Initialize the v2 analyzer with analytics token
            analyzer = LinkedInAnalyzerV2(
                analytics_access_token=analytics_access_token,
                max_posts=max_posts,
                openrouter_api_key=self.openrouter_api_key
            )
            
            # Run the analysis
            result = await analyzer.analyze_linkedin(
                person_urn=person_urn,
                current_bio=current_bio,
                content_to_analyze=content_to_analyze,
                user_writing_style=user_writing_style
            )
            
            logger.info(f"Successfully analyzed LinkedIn profile {person_urn}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze LinkedIn profile {person_urn}: {e}")
            # Return empty analysis on failure
            return {
                "writing_style": "",
                "topics": [],
                "websites": [],
                "bio": current_bio,
                "error": str(e)
            }
    
    def should_use_v2_analyzer(self, analytics_access_token: Optional[str]) -> bool:
        """
        Determine whether to use the v2 analyzer or fall back to v1.
        
        Args:
            analytics_access_token: Analytics access token if available
            
        Returns:
            True if v2 analyzer should be used, False for v1 fallback
        """
        return analytics_access_token is not None and analytics_access_token.strip() != ""
    
    async def analyze_with_fallback(
        self,
        # V2 parameters
        analytics_access_token: Optional[str],
        person_urn: Optional[str],
        # V1 parameters (fallback)
        account_id: Optional[str],
        # Common parameters
        current_bio: str,
        content_to_analyze: list,
        user_writing_style: str,
        max_posts: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze LinkedIn profile with automatic fallback from v2 to v1.
        
        This method tries to use the v2 analyzer first (if analytics token is available),
        and falls back to the v1 analyzer (web scraping) if needed.
        """
        if self.should_use_v2_analyzer(analytics_access_token) and person_urn:
            logger.info("Using LinkedIn API v2 analyzer")
            try:
                return await self.analyze_linkedin_profile(
                    analytics_access_token=analytics_access_token,
                    person_urn=person_urn,
                    current_bio=current_bio,
                    content_to_analyze=content_to_analyze,
                    user_writing_style=user_writing_style,
                    max_posts=max_posts
                )
            except Exception as e:
                logger.warning(f"V2 analyzer failed, falling back to v1: {e}")
        
        # Fallback to v1 analyzer
        if account_id:
            logger.info("Using LinkedIn scraping v1 analyzer")
            from linkedin_analyzer import LinkedInAnalyzer
            
            analyzer_v1 = LinkedInAnalyzer(
                max_posts=max_posts,
                openrouter_api_key=self.openrouter_api_key
            )
            
            return analyzer_v1.analyze_linkedin(
                account_id=account_id,
                current_bio=current_bio,
                content_to_analyze=content_to_analyze,
                user_writing_style=user_writing_style
            )
        
        # No valid parameters for either analyzer
        logger.error("No valid parameters for LinkedIn analysis")
        return {
            "writing_style": "",
            "topics": [],
            "websites": [],
            "bio": current_bio,
            "error": "No valid LinkedIn credentials or identifiers provided"
        }


# Example usage function
async def example_usage():
    """Example of how to use the LinkedIn analysis service."""
    
    service = LinkedInAnalysisService(openrouter_api_key="your_openrouter_key")
    
    # Example with v2 analyzer (preferred)
    result_v2 = await service.analyze_with_fallback(
        analytics_access_token="your_analytics_token",
        person_urn="urn:li:person:123456789",
        account_id=None,  # Not needed for v2
        current_bio="I'm a software engineer...",
        content_to_analyze=["writing_style", "bio", "interests"],
        user_writing_style="Professional and technical",
        max_posts=20
    )
    
    print("V2 Analysis Result:", result_v2)
    
    # Example with fallback to v1 analyzer
    result_fallback = await service.analyze_with_fallback(
        analytics_access_token=None,  # No analytics token
        person_urn=None,
        account_id="linkedin_username",  # Fallback to scraping
        current_bio="I'm a software engineer...",
        content_to_analyze=["writing_style", "bio", "interests"],
        user_writing_style="Professional and technical",
        max_posts=20
    )
    
    print("Fallback Analysis Result:", result_fallback)


if __name__ == "__main__":
    asyncio.run(example_usage())

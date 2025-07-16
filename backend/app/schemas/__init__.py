"""Schemas module."""

from . import (
    posts,
    profile,
    content_strategies,
    daily_suggestion_schedule,
    idea_bank,
    chat,
    auth,
)
from .auth import TokenResponse, UserResponse, UserUpdate


__all__ = [
    # Auth schemas
    "UserResponse",
    "TokenResponse",
    "UserUpdate",
    # Idea bank schemas
    "IdeaBankBase",
    "IdeaBankCreate",
    "IdeaBankUpdate",
    "IdeaBankResponse",
    "IdeaBankListResponse",
    "IdeaBankData",
    # User preferences schemas
    "UserPreferencesBase",
    "UserPreferencesCreate",
    "UserPreferencesUpdate",
    "UserPreferencesResponse",
    # Social connection schemas
    "SocialConnectionBase",
    "SocialConnectionCreate",
    "SocialConnectionUpdate",
    "SocialConnectionResponse",
    # Writing style analysis schemas
    "WritingStyleAnalysisBase",
    "WritingStyleAnalysisCreate",
    "WritingStyleAnalysisUpdate",
    "WritingStyleAnalysisResponse",
    # Posts schemas
    "PostCreate",
    "PostFeedback",
    "PostListResponse",
    "PostResponse",
    "PostUpdate",
    # Platform analysis schemas
    "SubstackAnalysisResponse",
    "WritingStyleData",
    "PostingPatterns",
    "EngagementInsights",
    "PlatformAnalysisResponse",
    # Daily suggestion schedule schemas
    "DailySuggestionScheduleCreate",
    "DailySuggestionScheduleUpdate",
    "DailySuggestionScheduleResponse",
    #
]

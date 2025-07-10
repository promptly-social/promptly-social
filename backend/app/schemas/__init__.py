"""Schemas module."""

from .auth import TokenResponse, UserCreate, UserResponse, UserUpdate

from .idea_bank import (
    IdeaBankBase,
    IdeaBankCreate,
    IdeaBankData,
    IdeaBankListResponse,
    IdeaBankResponse,
    IdeaBankUpdate,
)
from .profile import (
    EngagementInsights,
    PlatformAnalysisResponse,
    PostingPatterns,
    SocialConnectionBase,
    SocialConnectionCreate,
    SocialConnectionResponse,
    SocialConnectionUpdate,
    SubstackAnalysisResponse,
    UserPreferencesBase,
    UserPreferencesCreate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    WritingStyleAnalysisBase,
    WritingStyleAnalysisCreate,
    WritingStyleAnalysisResponse,
    WritingStyleAnalysisUpdate,
    WritingStyleData,
)
from .posts import (
    PostCreate,
    PostFeedback,
    PostListResponse,
    PostResponse,
    PostUpdate,
)
from .daily_suggestion_schedule import (
    DailySuggestionScheduleCreate,
    DailySuggestionScheduleUpdate,
    DailySuggestionScheduleResponse,
)

__all__ = [
    # Auth schemas
    "UserCreate",
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
]

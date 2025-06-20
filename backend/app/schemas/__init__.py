"""Schemas module."""

from .auth import TokenResponse, UserCreate, UserResponse, UserUpdate
from .content import (ContentBase, ContentCreate, ContentListResponse,
                      ContentResponse, ContentUpdate, PublicationBase,
                      PublicationCreate, PublicationResponse,
                      PublicationUpdate)
from .profile import (EngagementInsights, PlatformAnalysisResponse,
                      PostingPatterns, SocialConnectionBase,
                      SocialConnectionCreate, SocialConnectionResponse,
                      SocialConnectionUpdate, SubstackAnalysisResponse,
                      SubstackConnectionData, SubstackData, SuggestedPostBase,
                      SuggestedPostCreate, SuggestedPostResponse,
                      UserPreferencesBase, UserPreferencesCreate,
                      UserPreferencesResponse, UserPreferencesUpdate,
                      WritingStyleAnalysisBase, WritingStyleAnalysisCreate,
                      WritingStyleAnalysisResponse, WritingStyleAnalysisUpdate,
                      WritingStyleData)

__all__ = [
    # Auth schemas
    "UserCreate",
    "UserResponse",
    "TokenResponse",
    "UserUpdate",
    # Content schemas
    "ContentBase",
    "ContentCreate",
    "ContentUpdate",
    "ContentResponse",
    "ContentListResponse",
    # Publication schemas
    "PublicationBase",
    "PublicationCreate",
    "PublicationUpdate",
    "PublicationResponse",
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
    # Suggested post schemas
    "SuggestedPostBase",
    "SuggestedPostCreate",
    "SuggestedPostResponse",
    # Platform analysis schemas
    "SubstackData",
    "SubstackConnectionData",
    "SubstackAnalysisResponse",
    "WritingStyleData",
    "PostingPatterns",
    "EngagementInsights",
    "PlatformAnalysisData",
    "PlatformAnalysisResponse",
]

"""Schemas module."""

from .auth import (
    UserCreate,
    UserResponse,
    TokenResponse,
    UserUpdate,
)
from .content import (
    ContentBase,
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentListResponse,
    PublicationBase,
    PublicationCreate,
    PublicationUpdate,
    PublicationResponse,
)

from .profile import (
    UserPreferencesBase,
    UserPreferencesCreate,
    UserPreferencesUpdate,
    UserPreferencesResponse,
    SocialConnectionBase,
    SocialConnectionCreate,
    SocialConnectionUpdate,
    SocialConnectionResponse,
    WritingStyleAnalysisBase,
    WritingStyleAnalysisCreate,
    WritingStyleAnalysisUpdate,
    WritingStyleAnalysisResponse,
    SuggestedPostBase,
    SuggestedPostCreate,
    SuggestedPostResponse,
    SubstackData,
    SubstackConnectionData,
    SubstackAnalysisResponse,
    WritingStyleData,
    PostingPatterns,
    EngagementInsights,
    PlatformAnalysisData,
    PlatformAnalysisResponse,
)

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

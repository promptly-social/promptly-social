"""Schemas module."""

from .auth import TokenResponse, UserCreate, UserResponse, UserUpdate
from .content import (
    ContentBase,
    ContentCreate,
    ContentListResponse,
    ContentResponse,
    ContentUpdate,
    PublicationBase,
    PublicationCreate,
    PublicationResponse,
    PublicationUpdate,
)
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
from .suggested_posts import (
    SuggestedPostBase,
    SuggestedPostCreate,
    SuggestedPostListResponse,
    SuggestedPostResponse,
    SuggestedPostUpdate,
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
    # Suggested post schemas
    "SuggestedPostBase",
    "SuggestedPostCreate",
    "SuggestedPostUpdate",
    "SuggestedPostResponse",
    "SuggestedPostListResponse",
    # Platform analysis schemas
    "SubstackAnalysisResponse",
    "WritingStyleData",
    "PostingPatterns",
    "EngagementInsights",
    "PlatformAnalysisData",
    "PlatformAnalysisResponse",
]

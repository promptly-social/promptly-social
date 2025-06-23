from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences."""

    topics_of_interest: List[str] = Field(default_factory=list)
    websites: List[str] = Field(default_factory=list)
    bio: str = Field(default="")


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences."""

    pass


class UserPreferencesUpdate(UserPreferencesBase):
    """Schema for updating user preferences."""

    pass


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class SocialConnectionBase(BaseModel):
    """Base schema for social connections."""

    platform: str
    platform_username: Optional[str] = None
    is_active: bool = True
    analysis_status: Optional[str] = "not_started"


class SocialConnectionCreate(SocialConnectionBase):
    """Schema for creating social connections."""

    connection_data: Optional[Dict[str, Any]] = None


class SocialConnectionUpdate(BaseModel):
    """Schema for updating social connections."""

    platform_username: Optional[str] = None
    connection_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    analysis_status: Optional[str] = None


class SocialConnectionResponse(SocialConnectionBase):
    """Schema for social connection responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    connection_data: Optional[Dict[str, Any]] = None
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    analysis_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WritingStyleAnalysisBase(BaseModel):
    """Base schema for writing style analysis."""

    source: str  # import, substack, linkedin
    analysis_data: str


class WritingStyleAnalysisCreate(WritingStyleAnalysisBase):
    """Schema for creating writing style analysis."""

    pass


class WritingStyleAnalysisUpdate(BaseModel):
    """Schema for updating writing style analysis."""

    analysis_data: Optional[str] = None
    last_analyzed_at: Optional[datetime] = None
    source: Optional[str] = None


class WritingStyleAnalysisResponse(WritingStyleAnalysisBase):
    """Schema for writing style analysis responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    last_analyzed_at: datetime
    created_at: datetime
    updated_at: datetime


class SuggestedPostBase(BaseModel):
    """Base schema for suggested posts."""

    title: str
    content: str
    platform: str
    topics: List[str] = Field(default_factory=list)
    confidence_score: int = 0


class SuggestedPostCreate(SuggestedPostBase):
    """Schema for creating suggested posts."""

    content_id: Optional[UUID] = None


class SuggestedPostResponse(SuggestedPostBase):
    """Schema for suggested post responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    content_id: Optional[UUID] = None
    generated_at: datetime
    created_at: datetime


class SubstackAnalysisResponse(BaseModel):
    """Schema for Substack analysis response."""

    is_connected: bool
    analyzed_at: Optional[str] = None
    analysis_started_at: Optional[str] = None
    analysis_completed_at: Optional[str] = None
    is_analyzing: bool = False


# Platform analysis schemas
class WritingStyleData(BaseModel):
    """Schema for writing style data."""

    tone: str
    complexity: str
    avg_length: int
    key_themes: List[str]


class PostingPatterns(BaseModel):
    """Schema for posting patterns."""

    frequency: str
    best_times: List[str]


class EngagementInsights(BaseModel):
    """Schema for engagement insights."""

    high_performing_topics: List[str]
    content_types: List[str]


class PlatformAnalysisResponse(BaseModel):
    """Schema for platform analysis response."""

    analysis_data: Optional[str] = None
    last_analyzed: Optional[str] = None
    is_connected: bool


class LinkedInAuthResponse(BaseModel):
    """Schema for the LinkedIn auth URL response."""

    authorization_url: str


class LinkedInShareRequest(BaseModel):
    """Schema for a LinkedIn share request."""

    text: str

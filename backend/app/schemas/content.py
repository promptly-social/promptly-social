"""
Content-related Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class ContentIdeaBase(BaseModel):
    """Base schema for content ideas."""

    title: str
    original_input: Optional[str] = None
    content_type: str
    status: Optional[str] = "draft"


class ContentIdeaCreate(ContentIdeaBase):
    """Schema for creating content ideas."""

    generated_outline: Optional[Dict[str, Any]] = None


class ContentIdeaUpdate(BaseModel):
    """Schema for updating content ideas."""

    title: Optional[str] = None
    status: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    publication_error: Optional[str] = None
    linkedin_post_id: Optional[str] = None


class ContentIdeaResponse(ContentIdeaBase):
    """Schema for content idea responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    generated_outline: Optional[Dict[str, Any]] = None
    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    publication_error: Optional[str] = None
    linkedin_post_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContentIdeaListResponse(BaseModel):
    """Schema for paginated content ideas list."""

    items: List[ContentIdeaResponse]
    total: int
    page: int
    size: int
    has_next: bool


class UserPreferencesBase(BaseModel):
    """Base schema for user preferences."""

    topics_of_interest: List[str] = Field(default_factory=list)
    websites: List[str] = Field(default_factory=list)


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


class SocialConnectionCreate(SocialConnectionBase):
    """Schema for creating social connections."""

    connection_data: Optional[Dict[str, Any]] = None


class SocialConnectionUpdate(BaseModel):
    """Schema for updating social connections."""

    platform_username: Optional[str] = None
    connection_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class SocialConnectionResponse(SocialConnectionBase):
    """Schema for social connection responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    connection_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class WritingStyleAnalysisBase(BaseModel):
    """Base schema for writing style analysis."""

    platform: str
    analysis_data: Dict[str, Any]
    content_count: int = 0


class WritingStyleAnalysisCreate(WritingStyleAnalysisBase):
    """Schema for creating writing style analysis."""

    pass


class WritingStyleAnalysisUpdate(BaseModel):
    """Schema for updating writing style analysis."""

    analysis_data: Optional[Dict[str, Any]] = None
    content_count: Optional[int] = None
    last_analyzed_at: Optional[datetime] = None


class WritingStyleAnalysisResponse(WritingStyleAnalysisBase):
    """Schema for writing style analysis responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    last_analyzed_at: datetime
    created_at: datetime
    updated_at: datetime


class ImportedContentBase(BaseModel):
    """Base schema for imported content."""

    platform: str
    title: Optional[str] = None
    content: str
    source_url: Optional[str] = None


class ImportedContentCreate(ImportedContentBase):
    """Schema for creating imported content."""

    published_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ImportedContentResponse(ImportedContentBase):
    """Schema for imported content responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    published_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ScrapedContentBase(BaseModel):
    """Base schema for scraped content."""

    url: str
    title: Optional[str] = None
    content: str
    topics: List[str] = Field(default_factory=list)


class ScrapedContentCreate(ScrapedContentBase):
    """Schema for creating scraped content."""

    pass


class ScrapedContentResponse(ScrapedContentBase):
    """Schema for scraped content responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    scraped_at: datetime
    created_at: datetime


class SuggestedPostBase(BaseModel):
    """Base schema for suggested posts."""

    title: str
    content: str
    platform: str
    topics: List[str] = Field(default_factory=list)
    confidence_score: int = 0


class SuggestedPostCreate(SuggestedPostBase):
    """Schema for creating suggested posts."""

    content_idea_id: Optional[UUID] = None


class SuggestedPostResponse(SuggestedPostBase):
    """Schema for suggested post responses."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    content_idea_id: Optional[UUID] = None
    generated_at: datetime
    created_at: datetime


# Substack-specific schemas
class SubstackData(BaseModel):
    """Schema for Substack data."""

    name: str
    url: str
    topics: List[str]
    subscriber_count: Optional[int] = None
    recent_posts: Optional[List[Dict[str, Any]]] = None


class SubstackConnectionData(BaseModel):
    """Schema for Substack connection data."""

    substackData: List[SubstackData]
    analyzed_at: str


class SubstackAnalysisResponse(BaseModel):
    """Schema for Substack analysis response."""

    substack_data: List[SubstackData]
    is_connected: bool
    analyzed_at: Optional[str] = None


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


class PlatformAnalysisData(BaseModel):
    """Schema for platform analysis data."""

    writing_style: WritingStyleData
    topics: List[str]
    posting_patterns: PostingPatterns
    engagement_insights: EngagementInsights


class PlatformAnalysisResponse(BaseModel):
    """Schema for platform analysis response."""

    analysis_data: Optional[PlatformAnalysisData] = None
    last_analyzed: Optional[str] = None
    is_connected: bool

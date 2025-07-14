"""
Pydantic schemas for authentication API requests and responses.
Includes validation logic for user data, tokens, and authentication flows.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    preferred_language: str = "en"
    timezone: str = "UTC"


class UserUpdate(BaseModel):
    """Schema for updating user data."""

    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user data in API responses."""

    id: str = Field(..., description="User's unique identifier")
    is_verified: bool = Field(False, description="Whether the user is verified")
    created_at: Optional[datetime] = Field(
        None, description="Timestamp of user creation"
    )
    updated_at: Optional[datetime] = Field(None, description="Timestamp of last update")

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token responses."""

    access_token: str
    refresh_token: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""

    refresh_token: str


class AuthResponse(BaseModel):
    """Schema for successful authentication responses."""

    user: UserResponse
    tokens: TokenResponse
    message: str


class LinkedInAuthRequest(BaseModel):
    """Schema for initiating LinkedIn OAuth."""

    redirect_to: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema for generic success responses."""

    message: str


class ErrorResponse(BaseModel):
    """Schema for generic error responses."""

    error: str
    details: Optional[dict] = None

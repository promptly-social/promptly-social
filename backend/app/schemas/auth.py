"""
Pydantic schemas for authentication API requests and responses.
Includes validation logic for user data, tokens, and authentication flows.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from pydantic.types import constr


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    full_name: Optional[str] = None
    preferred_language: str = "en"
    timezone: str = "UTC"


class UserCreate(UserBase):
    """Schema for user registration."""

    password: constr(min_length=8, max_length=100)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v, info):
        """Validate that password and confirm_password match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength requirements."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(UserBase):
    """Schema for user update."""

    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    password: Optional[constr(min_length=8, max_length=100)] = None
    confirm_password: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user data in API responses."""

    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    """Schema for JWT token data."""

    user_id: Optional[str] = None


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AuthResponse(BaseModel):
    """Schema for comprehensive authentication response."""

    user: UserResponse
    tokens: TokenResponse
    message: str


class ErrorResponse(BaseModel):
    """Schema for API error responses."""

    error: str
    message: Optional[str] = None
    details: Optional[dict] = None


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: constr(min_length=8, max_length=100)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v, info):
        """Validate that new_password and confirm_password match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth authentication request."""

    redirect_to: Optional[str] = None


class GoogleOAuthCallback(BaseModel):
    """Schema for Google OAuth callback handling."""

    code: str
    state: Optional[str] = None
    redirect_to: Optional[str] = None


class GoogleSignInWithToken(BaseModel):
    """Schema for Google sign in with ID token."""

    id_token: str
    redirect_to: Optional[str] = None


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str
    new_password: constr(min_length=8, max_length=100)
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v, info):
        """Validate that new_password and confirm_password match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class SessionResponse(BaseModel):
    """Schema for user session response."""

    id: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


class SuccessResponse(BaseModel):
    """Schema for simple success responses."""

    success: bool = True
    message: str

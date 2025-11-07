"""
Pydantic schemas for authentication requests and responses.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, UUID4


class GoogleOAuthRequest(BaseModel):
    """Request model for Google OAuth authentication."""

    id_token: str = Field(..., description="Google ID token from OAuth flow")
    access_token: Optional[str] = Field(None, description="Google access token (optional)")


class TokenResponse(BaseModel):
    """Response model for token generation."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Request model for refreshing access token."""

    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """Response model for user data."""

    id: UUID4
    email: EmailStr
    full_name: Optional[str] = None
    oauth_provider: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    """Response model for /auth/me endpoint."""

    user: UserResponse
    has_subscription: bool = Field(..., description="Whether user has an active subscription")
    subscription_status: Optional[str] = Field(None, description="Current subscription status")
    trial_ends_at: Optional[datetime] = Field(None, description="Trial end date")


class SubscriptionStatusResponse(BaseModel):
    """Response model for subscription status."""

    has_subscription: bool
    status: Optional[str] = None  # trialing, active, canceled, past_due
    plan_type: Optional[str] = None  # monthly, yearly
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    class Config:
        from_attributes = True

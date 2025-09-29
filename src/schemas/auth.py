"""
Authentication schemas.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr

from ..models.user import UserRole


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    id_token: str | None = None


class UserProfile(BaseModel):
    """User profile schema."""

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    picture: str | None = None
    email_verified: bool
    locale: str | None = None
    last_login: datetime | None = None

    class Config:
        """Pydantic config."""

        from_attributes = True

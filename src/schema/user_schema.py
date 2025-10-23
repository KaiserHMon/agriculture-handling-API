from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from models.user_model import UserRole


class UserBase(BaseModel):

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    picture: HttpUrl | None = None
    locale: str | None = Field(None, max_length=10)
    role: UserRole


class UserCreate(UserBase):

    auth0_id: str = Field(..., max_length=255)
    auth0_metadata: dict | None = None


class UserUpdate(BaseModel):

    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    picture: HttpUrl | None = None
    locale: str | None = Field(None, max_length=10)
    auth0_metadata: dict | None = None
    is_active: bool | None = None


class UserInDB(UserBase):

    id: int
    auth0_id: str
    email_verified: bool
    is_active: bool
    last_login: datetime | None = None
    auth0_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    class Config:

        from_attributes = True


class UserResponse(UserInDB):
    pass


class UserRoleUpdate(BaseModel):

    role: UserRole = Field(...)


class UserLoginUpdate(BaseModel):
    """Schema for user login update."""

    last_login: datetime = Field(...)

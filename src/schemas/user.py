from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    """Public user response schema."""

    id: int
    email: EmailStr
    is_confirmed: bool
    role: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """Schema for email-based actions."""

    email: EmailStr


class ResetPassword(BaseModel):
    """Schema for password reset completion."""

    token: str
    new_password: str = Field(min_length=6, max_length=128)

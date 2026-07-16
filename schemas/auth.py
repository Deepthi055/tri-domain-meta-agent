"""
app/schemas/auth.py
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime
    avatar_url: str | None = None
    two_factor_enabled: bool = False

    class Config:
        from_attributes = True


class AvatarUploadRequest(BaseModel):
    avatar_url: str


class TwoFactorRequest(BaseModel):
    current_password: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

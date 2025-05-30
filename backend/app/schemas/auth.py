"""
Complete Authentication Schemas - Final Version
Created: 2025-05-29 14:38:00 UTC by Teeksss
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from app.models.user import UserRole


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str
    
    @validator('username')
    def username_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Username cannot be empty')
        return v
    
    @validator('password')
    def password_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('Password cannot be empty')
        return v


class UserRegister(BaseModel):
    """User registration schema"""
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole
    
    @validator('username')
    def username_validation(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v
    
    @validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if len(v) > 128:
            raise ValueError('Password must be less than 128 characters')
        return v


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class PasswordChange(BaseModel):
    """Password change schema"""
    old_password: str
    new_password: str
    
    @validator('new_password')
    def new_password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v


class PasswordReset(BaseModel):
    """Password reset schema"""
    token: str
    new_password: str
    
    @validator('new_password')
    def new_password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters')
        return v
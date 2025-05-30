"""
Complete User Schemas - Final Version
Created: 2025-05-29 14:38:00 UTC by Teeksss
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    
    @validator('username')
    def username_validation(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v


class UserCreate(UserBase):
    """User creation schema"""
    password: str
    role: UserRole
    
    @validator('password')
    def password_validation(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None
    notification_preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    display_name: Optional[str]
    role: UserRole
    status: UserStatus
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    login_count: int
    notification_preferences: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            username=obj.username,
            email=obj.email,
            first_name=obj.first_name,
            last_name=obj.last_name,
            display_name=obj.display_name,
            role=obj.role,
            status=obj.status,
            is_active=obj.is_active,
            is_verified=obj.is_verified,
            last_login_at=obj.last_login_at,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            login_count=obj.login_count,
            notification_preferences=obj.notification_preferences
        )


class UserProfile(BaseModel):
    """User profile schema"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    display_name: Optional[str]
    role: UserRole
    preferences: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True
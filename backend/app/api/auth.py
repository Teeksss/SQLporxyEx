"""
Complete Authentication API Router - Final Version
Created: 2025-05-29 14:34:05 UTC by Teeksss
"""

from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core import deps
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import (
    Token,
    TokenData,
    UserLogin,
    UserRegister,
    PasswordReset,
    PasswordChange
)
from app.services.auth import AuthService
from app.services.rate_limiter import check_rate_limit
from app.services.audit import log_security_event

router = APIRouter()
security = HTTPBearer()
auth_service = AuthService()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    user_credentials: UserLogin,
    db: Session = Depends(deps.get_db)
):
    """User login endpoint"""
    
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Rate limiting
    rate_limit_result = await check_rate_limit(
        identifier=f"login:{client_ip}",
        rule_type="auth",
        ip_address=client_ip
    )
    
    if not rate_limit_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts"
        )
    
    try:
        # Authenticate user
        auth_result = await auth_service.authenticate_user(
            username=user_credentials.username,
            password=user_credentials.password,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return auth_result
        
    except HTTPException as e:
        # Log failed login
        await log_security_event(
            "login_failed",
            ip_address=client_ip,
            details={
                "username": user_credentials.username,
                "reason": "invalid_credentials",
                "user_agent": user_agent
            }
        )
        raise e


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token_data: Dict[str, str],
    db: Session = Depends(deps.get_db)
):
    """Refresh access token"""
    
    refresh_token = refresh_token_data.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required"
        )
    
    try:
        new_tokens = await auth_service.refresh_access_token(refresh_token)
        return new_tokens
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(deps.get_current_user)
):
    """User logout endpoint"""
    
    client_ip = request.client.host
    
    try:
        await auth_service.logout_user(
            user_id=current_user.id,
            ip_address=client_ip
        )
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/register", response_model=Dict[str, Any])
async def register_user(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user)
):
    """Register new user (admin only)"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | 
        (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        is_active=True,
        is_verified=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log user creation
    await log_security_event(
        "user_created",
        user_id=current_user.id,
        ip_address=request.client.host,
        details={
            "new_user_id": new_user.id,
            "new_username": new_user.username,
            "new_user_role": new_user.role.value
        }
    )
    
    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "username": new_user.username
    }


@router.post("/change-password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user: User = Depends(deps.get_current_user)
):
    """Change user password"""
    
    try:
        success = await auth_service.change_password(
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password")
async def forgot_password(
    request: Request,
    email_data: Dict[str, str]
):
    """Request password reset"""
    
    email = email_data.get("email")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    try:
        reset_token = await auth_service.reset_password_request(email)
        
        return {
            "message": "If the email exists, you will receive reset instructions",
            "reset_token": reset_token  # In production, this would be sent via email
        }
        
    except Exception as e:
        return {
            "message": "If the email exists, you will receive reset instructions"
        }


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: User = Depends(deps.get_current_user)
):
    """Get current user information"""
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "display_name": current_user.display_name,
        "role": current_user.role.value,
        "status": current_user.status.value,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "created_at": current_user.created_at.isoformat(),
        "preferences": current_user.notification_preferences
    }


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(deps.get_current_user)
):
    """Validate current token"""
    
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value
    }
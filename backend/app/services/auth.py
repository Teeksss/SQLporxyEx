"""
Complete Authentication Service - Final Version
Created: 2025-05-29 14:18:32 UTC by Teeksss
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import (
    verify_password, 
    hash_password, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    log_security_event
)
from app.models.user import User, UserSession, UserRole, UserStatus
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)


class AuthService:
    """Complete Authentication Service"""
    
    def __init__(self):
        self.failed_attempts = {}  # In-memory cache for failed attempts
        self.session_cache = {}    # Session cache
        
    async def initialize(self):
        """Initialize authentication service"""
        logger.info("Authentication Service initialized")
        
    async def authenticate_user(
        self, 
        username: str, 
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        
        with get_db_session() as db:
            # Check rate limiting
            if self._is_rate_limited(username, ip_address):
                log_security_event(
                    "rate_limit_exceeded",
                    user_id=None,
                    ip_address=ip_address,
                    details={"username": username}
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please try again later."
                )
            
            # Get user
            user = db.query(User).filter(User.username == username).first()
            
            if not user or not verify_password(password, user.hashed_password):
                self._record_failed_attempt(username, ip_address)
                log_security_event(
                    "login_failed",
                    user_id=user.id if user else None,
                    ip_address=ip_address,
                    details={
                        "username": username,
                        "reason": "invalid_credentials"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password"
                )
            
            # Check user status
            if not user.is_active:
                log_security_event(
                    "login_failed",
                    user_id=user.id,
                    ip_address=ip_address,
                    details={
                        "username": username,
                        "reason": "account_disabled"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is disabled"
                )
            
            if user.is_locked:
                log_security_event(
                    "login_failed",
                    user_id=user.id,
                    ip_address=ip_address,
                    details={
                        "username": username,
                        "reason": "account_locked"
                    }
                )
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is locked"
                )
            
            # Clear failed attempts on successful auth
            self._clear_failed_attempts(username, ip_address)
            
            # Update user login info
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            user.login_count += 1
            user.failed_login_attempts = 0
            
            # Create tokens
            token_data = {
                "sub": user.username,
                "user_id": user.id,
                "role": user.role.value,
                "email": user.email
            }
            
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token({"user_id": user.id})
            
            # Create session
            session = self._create_user_session(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                db=db
            )
            
            # Log successful login
            log_security_event(
                "login_success",
                user_id=user.id,
                ip_address=ip_address,
                details={
                    "username": username,
                    "session_id": session.session_id
                }
            )
            
            db.commit()
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": self._serialize_user(user)
            }
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token"""
        
        try:
            payload = verify_token(refresh_token, "refresh")
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user_id = payload.get("user_id")
            
            with get_db_session() as db:
                user = db.query(User).filter(User.id == user_id).first()
                
                if not user or not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
                
                # Create new tokens
                token_data = {
                    "sub": user.username,
                    "user_id": user.id,
                    "role": user.role.value,
                    "email": user.email
                }
                
                new_access_token = create_access_token(token_data)
                new_refresh_token = create_refresh_token({"user_id": user.id})
                
                return {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                    "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }
                
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def logout_user(
        self, 
        user_id: int, 
        session_id: str = None,
        ip_address: str = None
    ) -> bool:
        """Logout user and invalidate session"""
        
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if session_id:
                # Logout specific session
                session = db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.session_id == session_id
                ).first()
                
                if session:
                    session.is_active = False
                    session.logout_at = datetime.utcnow()
            else:
                # Logout all sessions
                db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                ).update({
                    "is_active": False,
                    "logout_at": datetime.utcnow()
                })
            
            # Log logout
            log_security_event(
                "logout",
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "username": user.username if user else "unknown",
                    "session_id": session_id
                }
            )
            
            db.commit()
            return True
    
    async def change_password(
        self, 
        user_id: int, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """Change user password"""
        
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Verify old password
            if not verify_password(old_password, user.hashed_password):
                log_security_event(
                    "password_change_failed",
                    user_id=user_id,
                    details={"reason": "incorrect_old_password"}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect current password"
                )
            
            # Update password
            user.hashed_password = hash_password(new_password)
            user.password_changed_at = datetime.utcnow()
            user.must_change_password = False
            
            # Invalidate all sessions except current
            db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({
                "is_active": False,
                "logout_at": datetime.utcnow()
            })
            
            # Log password change
            log_security_event(
                "password_changed",
                user_id=user_id,
                details={"username": user.username}
            )
            
            db.commit()
            return True
    
    async def reset_password_request(self, email: str) -> str:
        """Request password reset"""
        
        with get_db_session() as db:
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                # Don't reveal if email exists
                return "If the email exists, you will receive reset instructions"
            
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            
            # Store reset token (in real implementation, use database)
            # For now, we'll just return it
            
            # Log password reset request
            log_security_event(
                "password_reset_requested",
                user_id=user.id,
                details={
                    "username": user.username,
                    "email": email
                }
            )
            
            return reset_token
    
    async def validate_session(
        self, 
        session_id: str,
        ip_address: str = None
    ) -> Optional[User]:
        """Validate user session"""
        
        with get_db_session() as db:
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                return None
            
            # Update last activity
            session.last_activity = datetime.utcnow()
            
            # Verify IP address if provided
            if ip_address and session.ip_address != ip_address:
                log_security_event(
                    "session_ip_mismatch",
                    user_id=session.user_id,
                    ip_address=ip_address,
                    details={
                        "session_ip": session.ip_address,
                        "request_ip": ip_address
                    }
                )
                # Optionally invalidate session
                # session.is_active = False
            
            db.commit()
            return session.user
    
    def _is_rate_limited(self, username: str, ip_address: str) -> bool:
        """Check if user/IP is rate limited"""
        
        now = datetime.utcnow()
        
        # Check by username
        user_attempts = self.failed_attempts.get(f"user:{username}", [])
        user_attempts = [attempt for attempt in user_attempts 
                        if now - attempt < timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)]
        
        if len(user_attempts) >= settings.MAX_LOGIN_ATTEMPTS:
            return True
        
        # Check by IP address
        if ip_address:
            ip_attempts = self.failed_attempts.get(f"ip:{ip_address}", [])
            ip_attempts = [attempt for attempt in ip_attempts 
                          if now - attempt < timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)]
            
            if len(ip_attempts) >= settings.MAX_LOGIN_ATTEMPTS * 3:  # Higher limit for IP
                return True
        
        return False
    
    def _record_failed_attempt(self, username: str, ip_address: str):
        """Record failed login attempt"""
        
        now = datetime.utcnow()
        
        # Record by username
        if f"user:{username}" not in self.failed_attempts:
            self.failed_attempts[f"user:{username}"] = []
        self.failed_attempts[f"user:{username}"].append(now)
        
        # Record by IP address
        if ip_address:
            if f"ip:{ip_address}" not in self.failed_attempts:
                self.failed_attempts[f"ip:{ip_address}"] = []
            self.failed_attempts[f"ip:{ip_address}"].append(now)
    
    def _clear_failed_attempts(self, username: str, ip_address: str):
        """Clear failed login attempts"""
        
        self.failed_attempts.pop(f"user:{username}", None)
        if ip_address:
            self.failed_attempts.pop(f"ip:{ip_address}", None)
    
    def _create_user_session(
        self, 
        user: User, 
        ip_address: str,
        user_agent: str,
        db: Session
    ) -> UserSession:
        """Create new user session"""
        
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES)
        
        session = UserSession(
            user_id=user.id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(session)
        return session
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Serialize user for response"""
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "role": user.role.value,
            "status": user.status.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
            "preferences": user.notification_preferences
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        
        try:
            # Test database connection
            with get_db_session() as db:
                user_count = db.query(User).count()
            
            return {
                "status": "healthy",
                "users_count": user_count,
                "failed_attempts_cache": len(self.failed_attempts),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics"""
        
        try:
            with get_db_session() as db:
                total_users = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                active_sessions = db.query(UserSession).filter(
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                ).count()
                
                # Recent login attempts
                recent_logins = db.query(AuditLog).filter(
                    AuditLog.action == "login_success",
                    AuditLog.timestamp > datetime.utcnow() - timedelta(hours=24)
                ).count()
                
                recent_failures = db.query(AuditLog).filter(
                    AuditLog.action == "login_failed",
                    AuditLog.timestamp > datetime.utcnow() - timedelta(hours=24)
                ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "active_sessions": active_sessions,
                "recent_logins_24h": recent_logins,
                "recent_failures_24h": recent_failures,
                "failed_attempts_cache": len(self.failed_attempts),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        logger.info("Authentication Service cleanup completed")
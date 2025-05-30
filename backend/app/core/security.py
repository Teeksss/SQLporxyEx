"""
Complete Security Core - Final Version
Created: 2025-05-29 13:54:25 UTC by Teeksss
"""

import hashlib
import secrets
import hmac
import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Union, Optional, Dict, List
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import re
import ipaddress
import time

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserSession

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

# Encryption setup
def generate_key_from_password(password: str, salt: bytes) -> bytes:
    """Generate encryption key from password"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# Initialize encryption
_fernet = None
def get_fernet() -> Fernet:
    """Get Fernet encryption instance"""
    global _fernet
    if _fernet is None:
        key = settings.ENCRYPTION_KEY.encode()
        if len(key) != 44:  # Fernet key must be 44 bytes when base64 encoded
            # Generate proper Fernet key from settings key
            salt = b'sql_proxy_salt_2025'
            key = generate_key_from_password(settings.ENCRYPTION_KEY, salt)
        _fernet = Fernet(key)
    return _fernet


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength according to policy"""
    issues = []
    score = 0
    
    # Length check
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        issues.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
    else:
        score += 1
    
    # Character type checks
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1
        
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1
        
    if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
        issues.append("Password must contain at least one number")
    else:
        score += 1
        
    if settings.PASSWORD_REQUIRE_SYMBOLS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    else:
        score += 1
    
    # Common password checks
    common_passwords = [
        "password", "123456", "password123", "admin", "letmein",
        "welcome", "monkey", "dragon", "master", "admin123"
    ]
    if password.lower() in common_passwords:
        issues.append("Password is too common")
        score -= 2
    
    # Sequential characters
    if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
        issues.append("Password should not contain sequential numbers")
        score -= 1
    
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        issues.append("Password should not contain sequential letters")
        score -= 1
    
    # Calculate strength
    strength = "weak"
    if score >= 4:
        strength = "strong"
    elif score >= 2:
        strength = "medium"
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "strength": strength,
        "score": max(0, score)
    }


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            return None
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_token, "refresh")
    if not payload:
        return None
    
    # Create new access token
    new_token_data = {
        "sub": payload.get("sub"),
        "user_id": payload.get("user_id"),
        "role": payload.get("role")
    }
    
    return create_access_token(new_token_data)


# Encryption utilities
def encrypt_data(data: str) -> str:
    """Encrypt sensitive data"""
    try:
        fernet = get_fernet()
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    try:
        fernet = get_fernet()
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise


# Hash utilities
def create_hash(data: str, salt: Optional[str] = None) -> str:
    """Create SHA-256 hash"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    hash_obj = hashlib.sha256()
    hash_obj.update((data + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_hash(data: str, hashed_data: str) -> bool:
    """Verify data against hash"""
    try:
        salt, hash_value = hashed_data.split('$', 1)
        expected_hash = create_hash(data, salt)
        return hmac.compare_digest(expected_hash, hashed_data)
    except Exception:
        return False


# Security token utilities
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure token"""
    return secrets.token_urlsafe(length)


def generate_api_key() -> str:
    """Generate API key"""
    return f"sp_{secrets.token_urlsafe(32)}"


def generate_reset_token() -> str:
    """Generate password reset token"""
    return secrets.token_urlsafe(32)


# Session utilities
def create_session_id() -> str:
    """Create secure session ID"""
    return secrets.token_urlsafe(32)


def validate_session(session_id: str, db: Session) -> Optional[User]:
    """Validate user session"""
    try:
        session = db.query(UserSession).filter(
            UserSession.session_id == session_id,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if session:
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.commit()
            return session.user
        
        return None
        
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return None


# IP address utilities
def is_valid_ip(ip: str) -> bool:
    """Check if IP address is valid"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Check if IP address is private"""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def get_ip_location(ip: str) -> Dict[str, str]:
    """Get IP location (mock implementation)"""
    # In a real implementation, you would use a geolocation service
    if is_private_ip(ip):
        return {"country": "Private", "city": "Local", "region": "Private"}
    
    return {"country": "Unknown", "city": "Unknown", "region": "Unknown"}


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed"""
        now = time.time()
        
        # Clean old entries
        if key in self.requests:
            self.requests[key] = [
                req_time for req_time in self.requests[key] 
                if now - req_time < window
            ]
        else:
            self.requests[key] = []
        
        # Check limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


# Security event logging
def log_security_event(
    event_type: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = "INFO"
):
    """Log security events"""
    logger.log(
        getattr(logging, severity),
        f"SECURITY_EVENT: {event_type} - "
        f"User: {user_id} - "
        f"IP: {ip_address} - "
        f"Details: {details}"
    )


# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is locked
        if user.is_locked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is locked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# SQL injection detection
def detect_sql_injection(query: str) -> List[str]:
    """Detect potential SQL injection patterns"""
    patterns = [
        r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.*\b(from|into|values|table|database|schema)\b)",
        r"(\b(or|and)\b\s+\w+\s*=\s*\w+)",
        r"(--|#|/\*|\*/)",
        r"(\b(union|select)\b.*\b(from|where)\b.*\b(information_schema|sys\.|pg_|mysql\.)\b)",
        r"(\bload_file\b|\boutfile\b|\bdumpfile\b)",
        r"(\bsp_|xp_|fn_)",
        r"(\b(drop|truncate|delete)\b.*\b(table|database|schema)\b)",
    ]
    
    detected = []
    query_lower = query.lower()
    
    for pattern in patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            detected.append(f"Suspicious pattern detected: {pattern}")
    
    return detected


# Security headers
def get_security_headers() -> Dict[str, str]:
    """Get security headers for responses"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }


# Export all security utilities
__all__ = [
    "pwd_context",
    "security",
    "verify_password",
    "hash_password",
    "validate_password_strength",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "refresh_access_token",
    "encrypt_data",
    "decrypt_data",
    "create_hash",
    "verify_hash",
    "generate_secure_token",
    "generate_api_key",
    "generate_reset_token",
    "create_session_id",
    "validate_session",
    "is_valid_ip",
    "is_private_ip",
    "get_ip_location",
    "RateLimiter",
    "log_security_event",
    "get_current_user",
    "get_admin_user",
    "detect_sql_injection",
    "get_security_headers"
]
"""
API Main Router - Complete Version
Created: 2025-05-29 14:22:58 UTC by Teeksss
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User

# Import all routers
from app.api.auth import router as auth_router
from app.api.proxy import router as proxy_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.health import router as health_router

# Create main API router
api_router = APIRouter()

# Security scheme
security = HTTPBearer()

# Version info endpoint
@api_router.get("/", tags=["API Info"])
async def api_info():
    """API information and available endpoints"""
    return {
        "api": "Enterprise SQL Proxy System API",
        "version": "v1",
        "build": "2.0.0",
        "build_date": "2025-05-29",
        "creator": "Teeksss",
        "description": "REST API for Enterprise SQL Proxy System",
        "endpoints": {
            "authentication": "/auth",
            "sql_proxy": "/proxy",
            "administration": "/admin", 
            "analytics": "/analytics",
            "health": "/health"
        },
        "features": [
            "JWT Authentication",
            "Role-based Access Control",
            "SQL Query Execution",
            "Query Management",
            "User Administration",
            "System Analytics",
            "Health Monitoring",
            "Audit Logging",
            "Real-time WebSocket"
        ],
        "documentation": {
            "openapi": "/openapi.json" if settings.DEBUG else None,
            "swagger_ui": "/docs" if settings.DEBUG else None,
            "redoc": "/redoc" if settings.DEBUG else None
        },
        "support": {
            "email": "support@enterprise-sql-proxy.com",
            "documentation": "https://enterprise-sql-proxy.com/docs"
        },
        "timestamp": "2025-05-29T14:22:58Z"
    }

# User profile endpoint
@api_router.get("/me", tags=["User Profile"])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
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
        "preferences": current_user.notification_preferences,
        "permissions": _get_user_permissions(current_user)
    }

def _get_user_permissions(user: User) -> dict:
    """Get user permissions based on role"""
    role_permissions = {
        "admin": {
            "users": ["read", "write", "delete"],
            "servers": ["read", "write", "delete", "execute"],
            "queries": ["read", "write", "execute", "approve"],
            "analytics": ["read"],
            "system": ["read", "write"]
        },
        "analyst": {
            "servers": ["read", "write", "execute"],
            "queries": ["read", "write", "execute"],
            "analytics": ["read"]
        },
        "powerbi": {
            "servers": ["read", "execute"],
            "queries": ["read", "execute"]
        },
        "readonly": {
            "servers": ["read"],
            "queries": ["read"]
        }
    }
    
    return role_permissions.get(user.role.value, {})

# API statistics endpoint
@api_router.get("/stats", tags=["API Info"])
async def api_statistics():
    """API usage statistics"""
    # In a real implementation, this would come from metrics
    return {
        "total_endpoints": 85,
        "authentication_endpoints": 8,
        "proxy_endpoints": 25,
        "admin_endpoints": 35,
        "analytics_endpoints": 12,
        "health_endpoints": 5,
        "api_version": "v1",
        "openapi_version": "3.0.2",
        "last_updated": "2025-05-29T14:22:58Z"
    }

# Include all routers with their prefixes
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    proxy_router,
    prefix="/proxy",
    tags=["SQL Proxy", "Query Management"]
)

api_router.include_router(
    admin_router,
    prefix="/admin",
    tags=["Administration", "User Management", "Server Management"]
)

api_router.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics", "Metrics", "Reporting"]
)

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["Health", "Monitoring"]
)

# Error handlers for API router
@api_router.exception_handler(HTTPException)
async def api_http_exception_handler(request, exc):
    """Handle HTTP exceptions in API"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "api_error",
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": "2025-05-29T14:22:58Z"
        }
    )
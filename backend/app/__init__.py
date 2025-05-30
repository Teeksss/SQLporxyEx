"""
Enterprise SQL Proxy System - Backend Application
Created: 2025-05-29 14:06:59 UTC by Teeksss
Version: 2.0.0

A secure, scalable SQL query execution platform with enterprise-grade features.
"""

__version__ = "2.0.0"
__author__ = "Teeksss"
__email__ = "teeksss@enterprise-sql-proxy.com"
__description__ = "Enterprise SQL Proxy System - Secure SQL query execution platform"
__license__ = "Enterprise"
__url__ = "https://github.com/enterprise/sql-proxy"
__created__ = "2025-05-29"

# Application metadata
APP_NAME = "Enterprise SQL Proxy System"
APP_VERSION = __version__
APP_AUTHOR = __author__
APP_DESCRIPTION = __description__

# Import main application components
from app.main import app
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal

# Version information
def get_version_info():
    """Get detailed version information"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "author": APP_AUTHOR,
        "description": APP_DESCRIPTION,
        "license": __license__,
        "url": __url__,
        "created": __created__,
        "python_version": "3.11+",
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "cache": "Redis"
    }

# Health check function
def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "timestamp": "2025-05-29T14:06:59Z"
    }

# Export main components
__all__ = [
    "app",
    "settings", 
    "Base",
    "engine",
    "SessionLocal",
    "get_version_info",
    "health_check",
    "__version__",
    "__author__",
    "__description__"
]
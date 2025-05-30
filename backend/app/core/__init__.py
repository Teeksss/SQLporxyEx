"""
Core Module - Application Core Components
Created: 2025-05-29 14:06:59 UTC by Teeksss

This module contains the core components of the Enterprise SQL Proxy System
including configuration, database, security, and utility functions.
"""

from app.core.config import Settings, settings
from app.core.database import (
    Base,
    engine, 
    SessionLocal,
    get_db,
    get_db_session,
    create_all_tables,
    drop_all_tables,
    check_database_health,
    get_connection_info,
    get_pool_status,
    vacuum_database,
    analyze_database,
    DatabaseTransaction,
    execute_raw_sql
)
from app.core.security import (
    pwd_context,
    security,
    verify_password,
    hash_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    verify_token,
    refresh_access_token,
    encrypt_data,
    decrypt_data,
    create_hash,
    verify_hash,
    generate_secure_token,
    generate_api_key,
    generate_reset_token,
    create_session_id,
    validate_session,
    is_valid_ip,
    is_private_ip,
    get_ip_location,
    RateLimiter,
    log_security_event,
    get_current_user,
    get_admin_user,
    detect_sql_injection,
    get_security_headers
)
from app.core.exceptions import (
    CustomHTTPException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
    ExternalServiceException,
    QueryException,
    RateLimitException,
    ConfigurationException,
    SecurityException,
    NotificationException,
    UserNotFoundException,
    ServerNotFoundException,
    QueryNotFoundException,
    InvalidQueryException,
    QueryTimeoutException,
    ApprovalRequiredException,
    ConnectionException,
    PermissionDeniedException,
    ResourceLimitException,
    MaintenanceException,
    FileException,
    ExportException,
    BackupException,
    create_error_response,
    handle_database_error,
    handle_external_service_error
)

# Module metadata
__version__ = "2.0.0"
__author__ = "Teeksss"
__description__ = "Core components for Enterprise SQL Proxy System"

# Core configuration
CORE_CONFIG = {
    "database_enabled": True,
    "security_enabled": True,
    "authentication_enabled": True,
    "rate_limiting_enabled": True,
    "encryption_enabled": True,
    "audit_logging_enabled": True
}

# Initialize core components
def initialize_core():
    """Initialize all core components"""
    try:
        # Check database connection
        if not check_database_health():
            raise DatabaseException("Database connection failed")
        
        # Create tables if they don't exist
        create_all_tables()
        
        return True
    except Exception as e:
        print(f"Core initialization failed: {e}")
        return False

# Core status check
def get_core_status():
    """Get status of all core components"""
    status = {
        "database": {
            "healthy": check_database_health(),
            "connection_info": get_connection_info(),
            "pool_status": get_pool_status()
        },
        "security": {
            "enabled": True,
            "encryption": True,
            "rate_limiting": settings.RATE_LIMIT_ENABLED
        },
        "configuration": {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "version": __version__
        }
    }
    return status

# Export all core components
__all__ = [
    # Configuration
    "Settings",
    "settings",
    
    # Database
    "Base",
    "engine",
    "SessionLocal", 
    "get_db",
    "get_db_session",
    "create_all_tables",
    "drop_all_tables",
    "check_database_health",
    "get_connection_info",
    "get_pool_status",
    "vacuum_database",
    "analyze_database",
    "DatabaseTransaction",
    "execute_raw_sql",
    
    # Security
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
    "get_security_headers",
    
    # Exceptions
    "CustomHTTPException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "DatabaseException",
    "ExternalServiceException",
    "QueryException",
    "RateLimitException",
    "ConfigurationException",
    "SecurityException",
    "NotificationException",
    "UserNotFoundException",
    "ServerNotFoundException",
    "QueryNotFoundException",
    "InvalidQueryException",
    "QueryTimeoutException",
    "ApprovalRequiredException",
    "ConnectionException",
    "PermissionDeniedException",
    "ResourceLimitException",
    "MaintenanceException",
    "FileException",
    "ExportException",
    "BackupException",
    "create_error_response",
    "handle_database_error",
    "handle_external_service_error",
    
    # Utilities
    "initialize_core",
    "get_core_status",
    "CORE_CONFIG"
]
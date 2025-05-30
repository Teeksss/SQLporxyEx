"""
Complete Exception Handling - Final Version
Created: 2025-05-29 13:54:25 UTC by Teeksss
"""

from typing import Any, Dict, Optional, List
from fastapi import HTTPException, status


class CustomHTTPException(HTTPException):
    """Base custom HTTP exception with additional context"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "unknown_error",
        context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.context = context or {}


class ValidationException(CustomHTTPException):
    """Validation error exception"""
    
    def __init__(
        self,
        detail: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        field: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="validation_error"
        )
        self.errors = errors or []
        self.field = field


class AuthenticationException(CustomHTTPException):
    """Authentication error exception"""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="authentication_error",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(CustomHTTPException):
    """Authorization error exception"""
    
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="authorization_error"
        )


class DatabaseException(CustomHTTPException):
    """Database operation error exception"""
    
    def __init__(self, detail: str = "Database operation failed", operation: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="database_error",
            context={"operation": operation}
        )


class ExternalServiceException(CustomHTTPException):
    """External service error exception"""
    
    def __init__(self, detail: str = "External service unavailable", service: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="external_service_error",
            context={"service": service}
        )


class QueryException(CustomHTTPException):
    """SQL query execution error exception"""
    
    def __init__(
        self,
        detail: str,
        query_hash: Optional[str] = None,
        server_id: Optional[int] = None,
        error_type: str = "execution_error"
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="query_error",
            context={
                "query_hash": query_hash,
                "server_id": server_id,
                "error_type": error_type
            }
        )


class RateLimitException(CustomHTTPException):
    """Rate limit exceeded exception"""
    
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="rate_limit_exceeded",
            headers={"Retry-After": str(retry_after)}
        )


class ConfigurationException(CustomHTTPException):
    """Configuration error exception"""
    
    def __init__(self, detail: str, config_key: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="configuration_error",
            context={"config_key": config_key}
        )


class SecurityException(CustomHTTPException):
    """Security violation exception"""
    
    def __init__(self, detail: str, violation_type: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="security_violation",
            context={"violation_type": violation_type}
        )


class NotificationException(CustomHTTPException):
    """Notification sending error exception"""
    
    def __init__(self, detail: str, notification_type: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="notification_error",
            context={"notification_type": notification_type}
        )


# Specific business logic exceptions
class UserNotFoundException(CustomHTTPException):
    """User not found exception"""
    
    def __init__(self, user_identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_identifier}",
            error_code="user_not_found",
            context={"user_identifier": user_identifier}
        )


class ServerNotFoundException(CustomHTTPException):
    """SQL Server not found exception"""
    
    def __init__(self, server_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server not found: {server_id}",
            error_code="server_not_found",
            context={"server_id": server_id}
        )


class QueryNotFoundException(CustomHTTPException):
    """Query execution not found exception"""
    
    def __init__(self, execution_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query execution not found: {execution_id}",
            error_code="query_not_found",
            context={"execution_id": execution_id}
        )


class InvalidQueryException(CustomHTTPException):
    """Invalid SQL query exception"""
    
    def __init__(self, detail: str, query_preview: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="invalid_query",
            context={"query_preview": query_preview}
        )


class QueryTimeoutException(CustomHTTPException):
    """Query execution timeout exception"""
    
    def __init__(self, timeout_seconds: int, query_hash: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Query execution timed out after {timeout_seconds} seconds",
            error_code="query_timeout",
            context={
                "timeout_seconds": timeout_seconds,
                "query_hash": query_hash
            }
        )


class ApprovalRequiredException(CustomHTTPException):
    """Query requires approval exception"""
    
    def __init__(self, approval_id: int, risk_level: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Query requires administrator approval",
            error_code="approval_required",
            context={
                "approval_id": approval_id,
                "risk_level": risk_level
            }
        )


class ConnectionException(CustomHTTPException):
    """Database connection error exception"""
    
    def __init__(self, detail: str, server_name: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="connection_error",
            context={"server_name": server_name}
        )


class PermissionDeniedException(CustomHTTPException):
    """Permission denied for specific operation exception"""
    
    def __init__(self, operation: str, resource: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied for operation: {operation}",
            error_code="permission_denied",
            context={
                "operation": operation,
                "resource": resource
            }
        )


class ResourceLimitException(CustomHTTPException):
    """Resource limit exceeded exception"""
    
    def __init__(self, resource_type: str, limit: int, current: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{resource_type} limit exceeded: {current}/{limit}",
            error_code="resource_limit_exceeded",
            context={
                "resource_type": resource_type,
                "limit": limit,
                "current": current
            }
        )


class MaintenanceException(CustomHTTPException):
    """System maintenance mode exception"""
    
    def __init__(self, maintenance_until: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is temporarily unavailable for maintenance",
            error_code="maintenance_mode",
            context={"maintenance_until": maintenance_until},
            headers={"Retry-After": "3600"}  # 1 hour
        )


class FileException(CustomHTTPException):
    """File operation error exception"""
    
    def __init__(self, detail: str, file_path: Optional[str] = None, operation: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="file_error",
            context={
                "file_path": file_path,
                "operation": operation
            }
        )


class ExportException(CustomHTTPException):
    """Data export error exception"""
    
    def __init__(self, detail: str, export_format: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="export_error",
            context={"export_format": export_format}
        )


class BackupException(CustomHTTPException):
    """Backup operation error exception"""
    
    def __init__(self, detail: str, backup_type: str = "unknown"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="backup_error",
            context={"backup_type": backup_type}
        )


# Exception utility functions
def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": error_code,
        "message": message,
        "status_code": status_code,
        "details": details or {},
        "timestamp": "2025-05-29T13:54:25Z"
    }


def handle_database_error(error: Exception) -> DatabaseException:
    """Convert database errors to custom exceptions"""
    error_message = str(error)
    
    if "connection" in error_message.lower():
        return DatabaseException("Database connection failed", "connection")
    elif "timeout" in error_message.lower():
        return DatabaseException("Database operation timed out", "timeout")
    elif "constraint" in error_message.lower():
        return DatabaseException("Database constraint violation", "constraint")
    elif "duplicate" in error_message.lower():
        return DatabaseException("Duplicate record found", "duplicate")
    else:
        return DatabaseException("Database operation failed", "unknown")


def handle_external_service_error(error: Exception, service_name: str) -> ExternalServiceException:
    """Convert external service errors to custom exceptions"""
    error_message = str(error)
    
    if "timeout" in error_message.lower():
        return ExternalServiceException(f"{service_name} service timed out", service_name)
    elif "connection" in error_message.lower():
        return ExternalServiceException(f"Cannot connect to {service_name} service", service_name)
    else:
        return ExternalServiceException(f"{service_name} service error", service_name)


# Export all exceptions
__all__ = [
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
    "handle_external_service_error"
]